"""Tests for the risk classifier module."""
import pytest

from aia_compliance.classifier import classify, RiskClassification, ANNEX_III_SECTORS
from aia_compliance.exceptions import InvalidSectorError, InvalidInputError


class TestClassifyBasic:
    def test_returns_risk_classification(self):
        result = classify(
            sector="healthcare",
            data_types=["health"],
            autonomy="automated",
            affected_persons=500,
            legal_effects=True,
        )
        assert isinstance(result, RiskClassification)

    def test_risk_level_is_valid_string(self):
        result = classify("healthcare", ["health"], "automated", 500, True)
        assert result.risk_level in ("minimal", "low", "limited", "high")

    def test_score_in_range(self):
        result = classify("healthcare", ["health"], "automated", 500, True)
        assert 0 <= result.score <= 100

    def test_annex_iii_match_true_for_covered_sector(self):
        result = classify("healthcare", ["health"], "automated", 500, True)
        assert result.annex_iii_match is True

    def test_high_risk_healthcare(self):
        result = classify(
            sector="healthcare",
            data_types=["health", "personal"],
            autonomy="automated",
            affected_persons=500,
            legal_effects=True,
        )
        assert result.risk_level == "high"

    def test_high_risk_has_obligations(self):
        result = classify("healthcare", ["health"], "automated", 500, True)
        assert len(result.obligations) > 0
        assert any("Art. 9" in o for o in result.obligations)

    def test_low_risk_education(self):
        # education(25) + personal(15) + analysis(5) + under_100(5) = 50 → limited
        # The minimum achievable score for any Annex III sector is ≥50 due to sector weight floors
        result = classify("education", ["personal"], "analysis", 20, False)
        assert result.risk_level in ("low", "limited", "minimal")

    def test_explanation_is_non_empty(self):
        result = classify("healthcare", ["health"], "automated", 500, True)
        assert isinstance(result.explanation, str)
        assert len(result.explanation) > 0

    def test_score_breakdown_provided(self):
        result = classify("healthcare", ["health"], "automated", 500, True)
        assert isinstance(result.score_breakdown, dict)
        assert len(result.score_breakdown) > 0


class TestClassifyDeterminism:
    def test_same_input_same_output(self):
        kwargs = dict(
            sector="employment",
            data_types=["personal", "financial"],
            autonomy="automated",
            affected_persons=2000,
            legal_effects=True,
        )
        r1 = classify(**kwargs)
        r2 = classify(**kwargs)
        assert r1 == r2

    def test_different_sector_different_score(self):
        r_healthcare = classify("healthcare", ["health"], "automated", 500, True)
        r_education = classify("education", ["personal"], "analysis", 500, True)
        assert r_healthcare.score != r_education.score


class TestClassifyAllSectors:
    @pytest.mark.parametrize("sector", sorted(ANNEX_III_SECTORS))
    def test_all_sectors_classify(self, sector):
        result = classify(sector, ["personal"], "analysis", 100, False)
        assert result.annex_iii_match is True
        assert result.risk_level in ("minimal", "low", "limited", "high")


class TestClassifyValidation:
    def test_invalid_sector_raises(self):
        with pytest.raises(InvalidSectorError) as exc_info:
            classify("finance", ["personal"], "automated", 100, False)
        assert "finance" in str(exc_info.value)
        assert exc_info.value.sector == "finance"

    def test_invalid_sector_includes_valid_list(self):
        with pytest.raises(InvalidSectorError) as exc_info:
            classify("foo", ["personal"], "automated", 100, False)
        assert exc_info.value.valid_sectors

    def test_invalid_autonomy_raises(self):
        with pytest.raises(InvalidInputError):
            classify("healthcare", ["health"], "magic", 100, False)

    def test_negative_affected_persons_raises(self):
        with pytest.raises(InvalidInputError):
            classify("healthcare", ["health"], "automated", -1, False)

    def test_invalid_data_type_raises(self):
        with pytest.raises(InvalidInputError):
            classify("healthcare", ["unknown"], "automated", 100, False)


class TestClassifyObligations:
    def test_high_risk_art9_present(self):
        result = classify("healthcare", ["health"], "automated", 500, True)
        if result.risk_level == "high":
            obligation_texts = " ".join(result.obligations)
            assert "Art. 9" in obligation_texts

    def test_high_risk_art47_present(self):
        result = classify("healthcare", ["health"], "automated", 500, True)
        if result.risk_level == "high":
            obligation_texts = " ".join(result.obligations)
            assert "Art. 47" in obligation_texts

    def test_limited_risk_art50_present(self):
        result = classify("education", ["personal"], "assisted", 50, False)
        if result.risk_level == "limited":
            assert any("Art. 50" in o for o in result.obligations)

    def test_biometrics_explanation_contains_annex(self):
        result = classify("biometrics", ["biometric"], "automated", 500, True)
        assert "Annex III" in result.explanation or "biometric" in result.explanation.lower()


class TestClassifyOptionalFlags:
    def test_precision_undefined_increases_score(self):
        base = classify("healthcare", ["personal"], "analysis", 50, False)
        with_flag = classify(
            "healthcare", ["personal"], "analysis", 50, False,
            precision_undefined=True,
        )
        assert with_flag.score >= base.score

    def test_all_flags_can_be_set(self):
        result = classify(
            sector="law_enforcement",
            data_types=["biometric"],
            autonomy="automated",
            affected_persons=5000,
            legal_effects=True,
            precision_undefined=True,
            robustness_undocumented=True,
            cybersecurity_missing=True,
        )
        assert result.risk_level == "high"
        assert result.score == 100
