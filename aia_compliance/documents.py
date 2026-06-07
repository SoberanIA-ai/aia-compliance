"""Document checklist generator for EU AI Act compliance.

Generates the list of documents required based on the system's risk level
and sector, referencing specific articles of Regulation (EU) 2024/1689.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class RequiredDocument:
    name: str
    article: str
    description: str
    mandatory: bool
    template_url: Optional[str] = None


@dataclass
class DocumentChecklist:
    risk_level: str
    sector: str
    documents: list[RequiredDocument]
    mandatory_count: int
    optional_count: int
    summary: str


_HIGH_RISK_DOCS: list[dict] = [
    {
        "name": "Technical Documentation (Annex IV)",
        "article": "Art. 11 + Annex IV",
        "description": (
            "Comprehensive technical documentation covering system design, "
            "development process, training data, performance metrics and limitations."
        ),
        "mandatory": True,
    },
    {
        "name": "Risk Management System Records",
        "article": "Art. 9",
        "description": (
            "Documentation of the risk management system including identified risks, "
            "mitigations applied, and residual risk assessment."
        ),
        "mandatory": True,
    },
    {
        "name": "Data Governance Documentation",
        "article": "Art. 10",
        "description": (
            "Data management practices, dataset provenance, labelling methodology, "
            "bias analysis, and data quality metrics."
        ),
        "mandatory": True,
    },
    {
        "name": "Automatic Logging System Records",
        "article": "Art. 12",
        "description": (
            "Records generated automatically by the system during operation, "
            "retained for at least six months (or as required by sector regulation)."
        ),
        "mandatory": True,
    },
    {
        "name": "Instructions for Use",
        "article": "Art. 13",
        "description": (
            "User-facing documentation explaining capabilities, limitations, "
            "intended purpose, and any known risks."
        ),
        "mandatory": True,
    },
    {
        "name": "Human Oversight Measures Description",
        "article": "Art. 14",
        "description": (
            "Description of the human oversight mechanisms built into the system, "
            "including override capabilities and stop functions."
        ),
        "mandatory": True,
    },
    {
        "name": "Accuracy, Robustness and Cybersecurity Report",
        "article": "Art. 15",
        "description": (
            "Performance metrics, robustness test results, and cybersecurity measures "
            "implemented in the system."
        ),
        "mandatory": True,
    },
    {
        "name": "EU Declaration of Conformity",
        "article": "Art. 47 + Annex V",
        "description": (
            "Signed declaration that the AI system complies with the AI Act and any "
            "other applicable Union harmonisation legislation."
        ),
        "mandatory": True,
    },
    {
        "name": "Conformity Assessment Report",
        "article": "Art. 43",
        "description": (
            "Internal or third-party conformity assessment demonstrating compliance "
            "with the essential requirements."
        ),
        "mandatory": True,
    },
    {
        "name": "EU Database Registration Certificate",
        "article": "Art. 49",
        "description": (
            "Confirmation of registration in the EU AI systems database "
            "before market placement."
        ),
        "mandatory": True,
    },
    {
        "name": "Post-Market Monitoring Plan",
        "article": "Art. 61",
        "description": (
            "Plan for monitoring system performance, detecting issues, and implementing "
            "corrective measures after deployment."
        ),
        "mandatory": True,
    },
    {
        "name": "Incident Reporting Procedure",
        "article": "Art. 62",
        "description": (
            "Internal procedure for identifying, evaluating, and reporting serious "
            "incidents to national supervisory authorities."
        ),
        "mandatory": True,
    },
    {
        "name": "Quality Management System Documentation",
        "article": "Art. 17",
        "description": (
            "Quality management system covering the full AI lifecycle from design "
            "to decommissioning."
        ),
        "mandatory": True,
    },
]

_LIMITED_RISK_DOCS: list[dict] = [
    {
        "name": "Transparency Disclosure Notice",
        "article": "Art. 50",
        "description": (
            "Notice informing users they are interacting with an AI system "
            "(required for chatbots, emotion recognition, deepfake generation)."
        ),
        "mandatory": True,
    },
    {
        "name": "AI System Description",
        "article": "Art. 50",
        "description": (
            "Basic description of the AI system's purpose, capabilities, and limitations "
            "made available to users."
        ),
        "mandatory": True,
    },
]

_VOLUNTARY_DOCS: list[dict] = [
    {
        "name": "Voluntary Code of Conduct",
        "article": "Art. 95",
        "description": (
            "Self-regulatory code of conduct aligned with the AI Act's principles "
            "for minimal-risk AI systems."
        ),
        "mandatory": False,
    },
    {
        "name": "AI Literacy Training Materials",
        "article": "Art. 4",
        "description": (
            "Training materials to ensure staff deploying or managing the system "
            "have appropriate AI literacy."
        ),
        "mandatory": False,
    },
]


def generate_document_checklist(
    risk_level: str,
    sector: str,
    include_voluntary: bool = True,
) -> DocumentChecklist:
    """Generate a document checklist for EU AI Act compliance.

    Parameters
    ----------
    risk_level:
        Risk level from the classifier: ``high``, ``limited``, ``low``, or ``minimal``.
    sector:
        Business sector of the AI system.
    include_voluntary:
        Whether to include voluntary/recommended documents for lower-risk systems.

    Returns
    -------
    DocumentChecklist
        List of required documents with article references and descriptions.
    """
    risk_norm = risk_level.lower()
    docs: list[RequiredDocument] = []

    if risk_norm == "high":
        for d in _HIGH_RISK_DOCS:
            docs.append(RequiredDocument(**d))
    elif risk_norm == "limited":
        for d in _LIMITED_RISK_DOCS:
            docs.append(RequiredDocument(**d))

    if include_voluntary and risk_norm in ("low", "minimal", "limited"):
        for d in _VOLUNTARY_DOCS:
            docs.append(RequiredDocument(**d))

    mandatory = sum(1 for d in docs if d.mandatory)
    optional = sum(1 for d in docs if not d.mandatory)

    if risk_norm == "high":
        summary = (
            f"HIGH RISK system in '{sector}'. "
            f"{mandatory} mandatory documents required before market placement."
        )
    elif risk_norm == "limited":
        summary = (
            f"LIMITED RISK system in '{sector}'. "
            f"{mandatory} transparency document(s) required under Art. 50."
        )
    else:
        summary = (
            f"{risk_norm.upper()} RISK system in '{sector}'. "
            f"No mandatory EU AI Act documents. "
            f"{optional} voluntary document(s) recommended."
        )

    return DocumentChecklist(
        risk_level=risk_norm,
        sector=sector,
        documents=docs,
        mandatory_count=mandatory,
        optional_count=optional,
        summary=summary,
    )
