"""Tests for the document checklist generator."""
import pytest

from aia_compliance.documents import generate_document_checklist, DocumentChecklist, RequiredDocument


class TestDocumentChecklistHigh:
    def test_returns_document_checklist(self):
        result = generate_document_checklist("high", "healthcare")
        assert isinstance(result, DocumentChecklist)

    def test_high_risk_has_mandatory_docs(self):
        result = generate_document_checklist("high", "healthcare")
        assert result.mandatory_count > 0

    def test_high_risk_13_mandatory_docs(self):
        result = generate_document_checklist("high", "healthcare")
        assert result.mandatory_count == 13

    def test_high_risk_documents_are_required_doc_instances(self):
        result = generate_document_checklist("high", "healthcare")
        for doc in result.documents:
            assert isinstance(doc, RequiredDocument)

    def test_high_risk_all_mandatory(self):
        result = generate_document_checklist("high", "healthcare")
        mandatory_docs = [d for d in result.documents if d.mandatory]
        assert len(mandatory_docs) == result.mandatory_count

    def test_high_risk_technical_doc_present(self):
        result = generate_document_checklist("high", "healthcare")
        names = [d.name for d in result.documents]
        assert any("Technical Documentation" in n for n in names)

    def test_high_risk_eu_declaration_present(self):
        result = generate_document_checklist("high", "healthcare")
        names = [d.name for d in result.documents]
        assert any("Declaration of Conformity" in n for n in names)

    def test_high_risk_summary_mentions_sector(self):
        result = generate_document_checklist("high", "employment")
        assert "employment" in result.summary

    def test_high_risk_summary_mentions_high(self):
        result = generate_document_checklist("high", "healthcare")
        assert "HIGH RISK" in result.summary or "high" in result.summary.lower()

    def test_high_risk_documents_have_article_refs(self):
        result = generate_document_checklist("high", "healthcare")
        for doc in result.documents:
            assert "Art." in doc.article

    def test_high_risk_documents_have_descriptions(self):
        result = generate_document_checklist("high", "healthcare")
        for doc in result.documents:
            assert len(doc.description) > 10


class TestDocumentChecklistLimited:
    def test_limited_risk_has_transparency_doc(self):
        result = generate_document_checklist("limited", "education")
        names = [d.name for d in result.documents]
        assert any("Transparency" in n for n in names)

    def test_limited_risk_art50_referenced(self):
        result = generate_document_checklist("limited", "education")
        articles = [d.article for d in result.documents if d.mandatory]
        assert any("Art. 50" in a for a in articles)

    def test_limited_risk_mandatory_count(self):
        result = generate_document_checklist("limited", "education")
        assert result.mandatory_count == 2

    def test_limited_risk_includes_voluntary_by_default(self):
        result = generate_document_checklist("limited", "education")
        optional = [d for d in result.documents if not d.mandatory]
        assert len(optional) > 0

    def test_limited_risk_no_voluntary_when_excluded(self):
        result = generate_document_checklist("limited", "education", include_voluntary=False)
        optional = [d for d in result.documents if not d.mandatory]
        assert len(optional) == 0


class TestDocumentChecklistLowMinimal:
    def test_low_risk_no_mandatory(self):
        result = generate_document_checklist("low", "education")
        assert result.mandatory_count == 0

    def test_minimal_risk_no_mandatory(self):
        result = generate_document_checklist("minimal", "education")
        assert result.mandatory_count == 0

    def test_low_risk_has_voluntary_docs(self):
        result = generate_document_checklist("low", "education")
        assert result.optional_count > 0

    def test_minimal_risk_no_voluntary_when_excluded(self):
        result = generate_document_checklist("minimal", "education", include_voluntary=False)
        assert len(result.documents) == 0

    def test_low_risk_summary_mentions_no_mandatory(self):
        result = generate_document_checklist("low", "education")
        assert "No mandatory" in result.summary or result.mandatory_count == 0

    def test_minimal_risk_summary_mentions_no_mandatory(self):
        result = generate_document_checklist("minimal", "education")
        assert "No mandatory" in result.summary


class TestDocumentChecklistAttributes:
    def test_risk_level_stored(self):
        result = generate_document_checklist("high", "healthcare")
        assert result.risk_level == "high"

    def test_sector_stored(self):
        result = generate_document_checklist("high", "employment")
        assert result.sector == "employment"

    def test_case_insensitive_risk_level(self):
        result = generate_document_checklist("HIGH", "healthcare")
        assert result.risk_level == "high"

    def test_document_has_name(self):
        result = generate_document_checklist("high", "healthcare")
        for doc in result.documents:
            assert isinstance(doc.name, str)
            assert len(doc.name) > 0

    def test_no_template_url_by_default(self):
        result = generate_document_checklist("high", "healthcare")
        for doc in result.documents:
            assert doc.template_url is None

    @pytest.mark.parametrize("risk_level", ["high", "limited", "low", "minimal"])
    def test_all_risk_levels_return_checklist(self, risk_level):
        result = generate_document_checklist(risk_level, "healthcare")
        assert isinstance(result, DocumentChecklist)
