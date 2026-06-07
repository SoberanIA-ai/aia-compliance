"""Tests for the AESIA compliance checklist module."""
import pytest

from aia_compliance.checklist import check_aesia_compliance, ComplianceResult, GuideStatus


class TestChecklistBasic:
    def test_returns_compliance_result(self):
        result = check_aesia_compliance(
            system_description="Test system",
            sector="healthcare",
        )
        assert isinstance(result, ComplianceResult)

    def test_all_guides_present(self):
        result = check_aesia_compliance("Test", "healthcare")
        assert len(result.guides) == 16
        for code in [f"G{i:02d}" for i in range(1, 17)]:
            assert code in result.guides

    def test_guide_status_type(self):
        result = check_aesia_compliance("Test", "healthcare")
        for guide in result.guides.values():
            assert isinstance(guide, GuideStatus)

    def test_zero_compliance_by_default(self):
        result = check_aesia_compliance("Test", "healthcare")
        assert result.score == 0.0
        assert result.compliant is False

    def test_full_compliance(self):
        result = check_aesia_compliance(
            system_description="Fully compliant system",
            sector="healthcare",
            has_risk_management=True,
            has_human_oversight=True,
            has_technical_docs=True,
            has_logging=True,
            has_transparency=True,
            has_data_governance=True,
            has_accuracy_metrics=True,
            has_robustness_testing=True,
            has_cybersecurity=True,
            has_conformity_assessment=True,
            has_post_market_monitoring=True,
            has_incident_reporting=True,
            has_registration=True,
            has_declaration_of_conformity=True,
            has_ce_marking=True,
            has_precision_metrics=True,
        )
        assert result.compliant is True
        assert result.score == 100.0
        assert len(result.missing) == 0

    def test_partial_compliance_score(self):
        result = check_aesia_compliance(
            "Test", "healthcare",
            has_risk_management=True,
            has_human_oversight=True,
        )
        assert 0 < result.score < 100
        assert result.compliant is False

    def test_missing_list_populated(self):
        result = check_aesia_compliance("Test", "healthcare")
        assert len(result.missing) == 16

    def test_missing_contains_guide_codes(self):
        result = check_aesia_compliance("Test", "healthcare")
        codes_in_missing = [m[:3] for m in result.missing]
        assert "G01" in codes_in_missing

    def test_priority_list_ordered_critical_first(self):
        result = check_aesia_compliance("Test", "healthcare")
        assert result.priority[0].startswith("[CRITICAL]")

    def test_compliant_guides_have_no_action(self):
        result = check_aesia_compliance("Test", "healthcare", has_risk_management=True)
        assert result.guides["G01"].action is None

    def test_non_compliant_guides_have_action(self):
        result = check_aesia_compliance("Test", "healthcare")
        assert result.guides["G01"].action is not None

    def test_summary_contains_sector(self):
        result = check_aesia_compliance("Test", "employment")
        assert "employment" in result.summary

    def test_summary_contains_score(self):
        result = check_aesia_compliance("Test", "healthcare", has_risk_management=True)
        assert "%" in result.summary or str(result.score) in result.summary


class TestChecklistGuideAttributes:
    def test_g01_has_correct_article(self):
        result = check_aesia_compliance("Test", "healthcare")
        assert "Art. 9" in result.guides["G01"].article

    def test_g06_has_correct_article(self):
        result = check_aesia_compliance("Test", "healthcare")
        assert "Art. 14" in result.guides["G06"].article

    def test_g08_has_correct_article(self):
        result = check_aesia_compliance("Test", "healthcare")
        assert "Art. 43" in result.guides["G08"].article

    def test_all_guides_required(self):
        result = check_aesia_compliance("Test", "healthcare")
        for guide in result.guides.values():
            assert guide.required is True

    def test_priority_values_are_1_2_or_3(self):
        result = check_aesia_compliance("Test", "healthcare")
        for guide in result.guides.values():
            assert guide.priority in (1, 2, 3)


class TestChecklistSectors:
    @pytest.mark.parametrize("sector", [
        "healthcare", "employment", "education", "biometrics",
        "law_enforcement", "migration", "justice", "essential_services",
        "critical_infrastructure",
    ])
    def test_all_sectors_work(self, sector):
        result = check_aesia_compliance("Test", sector)
        assert isinstance(result, ComplianceResult)

    def test_sector_in_summary(self):
        for sector in ("healthcare", "employment"):
            result = check_aesia_compliance("Test", sector)
            assert sector in result.summary


class TestChecklistDeterminism:
    def test_same_input_same_output(self):
        kwargs = dict(
            system_description="Test AI",
            sector="healthcare",
            has_risk_management=True,
            has_human_oversight=False,
            has_technical_docs=True,
        )
        r1 = check_aesia_compliance(**kwargs)
        r2 = check_aesia_compliance(**kwargs)
        assert r1.score == r2.score
        assert r1.compliant == r2.compliant
        assert r1.missing == r2.missing
