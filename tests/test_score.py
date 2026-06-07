"""Tests for the deterministic scoring engine."""
import pytest

from aia_compliance.score import calculate_score, score_to_risk_band, ScoreResult, WEIGHTS
from aia_compliance.exceptions import InvalidInputError


class TestScoreToRiskBand:
    def test_minimal(self):
        assert score_to_risk_band(0) == "minimal"
        assert score_to_risk_band(12) == "minimal"
        assert score_to_risk_band(24) == "minimal"

    def test_low(self):
        assert score_to_risk_band(25) == "low"
        assert score_to_risk_band(37) == "low"
        assert score_to_risk_band(49) == "low"

    def test_limited(self):
        assert score_to_risk_band(50) == "limited"
        assert score_to_risk_band(62) == "limited"
        assert score_to_risk_band(74) == "limited"

    def test_high(self):
        assert score_to_risk_band(75) == "high"
        assert score_to_risk_band(88) == "high"
        assert score_to_risk_band(100) == "high"


class TestCalculateScore:
    def test_returns_score_result(self):
        result = calculate_score(
            sector="healthcare",
            data_types=["health"],
            autonomy="automated",
            affected_persons=500,
            legal_effects=False,
        )
        assert isinstance(result, ScoreResult)

    def test_deterministic_same_input_same_output(self):
        kwargs = dict(
            sector="healthcare",
            data_types=["health", "personal"],
            autonomy="automated",
            affected_persons=1500,
            legal_effects=True,
        )
        r1 = calculate_score(**kwargs)
        r2 = calculate_score(**kwargs)
        assert r1 == r2

    def test_capped_at_100(self):
        result = calculate_score(
            sector="law_enforcement",
            data_types=["biometric", "health"],
            autonomy="automated",
            affected_persons=5000,
            legal_effects=True,
            precision_undefined=True,
            robustness_undocumented=True,
            cybersecurity_missing=True,
        )
        assert result.capped_score <= 100

    def test_raw_score_can_exceed_100(self):
        result = calculate_score(
            sector="law_enforcement",
            data_types=["biometric"],
            autonomy="automated",
            affected_persons=5000,
            legal_effects=True,
            precision_undefined=True,
            robustness_undocumented=True,
            cybersecurity_missing=True,
        )
        assert result.raw_score >= result.capped_score

    def test_high_risk_healthcare(self):
        result = calculate_score(
            sector="healthcare",
            data_types=["health"],
            autonomy="automated",
            affected_persons=500,
            legal_effects=True,
        )
        assert result.risk_band == "high"

    def test_low_risk_education(self):
        # education(25) + personal(15) + analysis(5) + under_100(5) = 50 → limited
        # The minimum possible score for any Annex III sector is 50 due to sector weight floors
        result = calculate_score(
            sector="education",
            data_types=["personal"],
            autonomy="analysis",
            affected_persons=50,
            legal_effects=False,
        )
        assert result.risk_band in ("low", "limited")

    def test_breakdown_contains_expected_keys(self):
        result = calculate_score(
            sector="healthcare",
            data_types=["health"],
            autonomy="automated",
            affected_persons=500,
            legal_effects=True,
        )
        assert "data_types" in result.breakdown
        assert "sector" in result.breakdown
        assert "autonomy" in result.breakdown
        assert "affected_persons" in result.breakdown
        assert "legal_effects" in result.breakdown

    def test_legal_effects_adds_weight(self):
        base = calculate_score("healthcare", ["personal"], "analysis", 50, False)
        with_legal = calculate_score("healthcare", ["personal"], "analysis", 50, True)
        assert with_legal.capped_score >= base.capped_score + WEIGHTS["legal_effects"]

    def test_optional_risk_flags_add_to_score(self):
        base = calculate_score("healthcare", ["personal"], "analysis", 50, False)
        with_flags = calculate_score(
            "healthcare", ["personal"], "analysis", 50, False,
            precision_undefined=True,
            robustness_undocumented=True,
            cybersecurity_missing=True,
        )
        added = (
            WEIGHTS["precision_undefined"]
            + WEIGHTS["robustness_undocumented"]
            + WEIGHTS["cybersecurity_missing"]
        )
        assert with_flags.raw_score == base.raw_score + added

    def test_invalid_autonomy_raises(self):
        with pytest.raises(InvalidInputError, match="autonomy"):
            calculate_score("healthcare", ["health"], "magic", 100, False)

    def test_invalid_data_type_raises(self):
        with pytest.raises(InvalidInputError, match="data type"):
            calculate_score("healthcare", ["unknown_type"], "automated", 100, False)

    def test_over_1000_persons_weight(self):
        result = calculate_score("healthcare", ["health"], "automated", 1001, False)
        assert result.breakdown["affected_persons"] == WEIGHTS["affected_persons"]["over_1000"]

    def test_100_to_1000_persons_weight(self):
        result = calculate_score("healthcare", ["health"], "automated", 500, False)
        assert result.breakdown["affected_persons"] == WEIGHTS["affected_persons"]["100_to_1000"]

    def test_under_100_persons_weight(self):
        result = calculate_score("healthcare", ["health"], "automated", 50, False)
        assert result.breakdown["affected_persons"] == WEIGHTS["affected_persons"]["under_100"]

    def test_highest_data_type_wins(self):
        # biometric (35) > health (30) — only biometric weight should be counted
        result_biometric_only = calculate_score("healthcare", ["biometric"], "automated", 50, False)
        result_both = calculate_score("healthcare", ["biometric", "health"], "automated", 50, False)
        assert result_both.breakdown["data_types"] == result_biometric_only.breakdown["data_types"]

    def test_all_sectors_are_scoreable(self):
        sectors = [
            "biometrics", "critical_infrastructure", "education", "employment",
            "essential_services", "law_enforcement", "migration", "justice", "healthcare",
        ]
        for sector in sectors:
            result = calculate_score(sector, ["personal"], "analysis", 50, False)
            assert 0 <= result.capped_score <= 100
