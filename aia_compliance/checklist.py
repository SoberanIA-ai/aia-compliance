"""AESIA 16-guide compliance checker for the EU AI Act.

Evaluates an AI system against the 16 guides published by AESIA
(Agencia Española de Supervisión de la Inteligencia Artificial).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class GuideStatus:
    """Compliance status for a single AESIA guide."""

    code: str
    title: str
    article: str
    compliant: bool
    required: bool
    action: Optional[str] = None
    priority: int = 3  # 1 = critical, 2 = high, 3 = medium


@dataclass
class ComplianceResult:
    """Result of an AESIA compliance check."""

    compliant: bool
    score: float
    guides: dict[str, GuideStatus]
    missing: list[str]
    priority: list[str]
    summary: str


_GUIDE_DEFINITIONS: list[dict] = [
    {
        "code": "G01",
        "title": "Risk Management System",
        "article": "Art. 9",
        "flag": "has_risk_management",
        "action": "Implement a continuous risk management system covering the full AI lifecycle.",
        "priority": 1,
    },
    {
        "code": "G02",
        "title": "Data and Data Governance",
        "article": "Art. 10",
        "flag": "has_data_governance",
        "action": "Define data governance policies: collection, labelling, bias analysis, quality metrics.",
        "priority": 1,
    },
    {
        "code": "G03",
        "title": "Technical Documentation",
        "article": "Art. 11 + Annex IV",
        "flag": "has_technical_docs",
        "action": "Produce Annex IV technical documentation before market placement.",
        "priority": 1,
    },
    {
        "code": "G04",
        "title": "Record-Keeping and Logging",
        "article": "Art. 12",
        "flag": "has_logging",
        "action": "Enable automatic logging of system operation throughout the lifecycle.",
        "priority": 2,
    },
    {
        "code": "G05",
        "title": "Transparency and User Information",
        "article": "Art. 13",
        "flag": "has_transparency",
        "action": "Provide users with clear information about system capabilities and limitations.",
        "priority": 2,
    },
    {
        "code": "G06",
        "title": "Human Oversight",
        "article": "Art. 14",
        "flag": "has_human_oversight",
        "action": "Design and implement meaningful human oversight mechanisms.",
        "priority": 1,
    },
    {
        "code": "G07",
        "title": "Accuracy, Robustness and Cybersecurity",
        "article": "Art. 15",
        "flag": "has_accuracy_metrics",
        "action": "Define accuracy metrics; document performance thresholds for the intended purpose.",
        "priority": 1,
    },
    {
        "code": "G08",
        "title": "Conformity Assessment",
        "article": "Art. 43",
        "flag": "has_conformity_assessment",
        "action": "Conduct a conformity assessment (internal or third-party) before deployment.",
        "priority": 1,
    },
    {
        "code": "G09",
        "title": "Precision and Performance Metrics",
        "article": "Art. 15 / AESIA Guide 09",
        "flag": "has_precision_metrics",
        "action": "Define and document precision, recall, F1 or sector-appropriate performance metrics.",
        "priority": 2,
    },
    {
        "code": "G10",
        "title": "Robustness Documentation",
        "article": "Art. 15 / AESIA Guide 10",
        "flag": "has_robustness_testing",
        "action": "Document robustness tests including adversarial inputs and edge cases.",
        "priority": 2,
    },
    {
        "code": "G11",
        "title": "Cybersecurity Measures",
        "article": "Art. 15 / AESIA Guide 11",
        "flag": "has_cybersecurity",
        "action": "Implement and document cybersecurity measures against attacks on model integrity.",
        "priority": 2,
    },
    {
        "code": "G12",
        "title": "Post-Market Monitoring",
        "article": "Art. 61",
        "flag": "has_post_market_monitoring",
        "action": "Establish a post-market monitoring plan and assign responsibility.",
        "priority": 2,
    },
    {
        "code": "G13",
        "title": "Incident Reporting",
        "article": "Art. 62",
        "flag": "has_incident_reporting",
        "action": "Set up procedures for reporting serious incidents to market surveillance authorities.",
        "priority": 2,
    },
    {
        "code": "G14",
        "title": "EU Database Registration",
        "article": "Art. 49",
        "flag": "has_registration",
        "action": "Register the system in the EU database before making it available on the market.",
        "priority": 3,
    },
    {
        "code": "G15",
        "title": "EU Declaration of Conformity",
        "article": "Art. 47",
        "flag": "has_declaration_of_conformity",
        "action": "Draft and sign the EU Declaration of Conformity.",
        "priority": 3,
    },
    {
        "code": "G16",
        "title": "CE Marking",
        "article": "Art. 48",
        "flag": "has_ce_marking",
        "action": "Affix the CE marking to the AI system and its accompanying documentation.",
        "priority": 3,
    },
]


def check_aesia_compliance(
    system_description: str,
    sector: str,
    has_risk_management: bool = False,
    has_human_oversight: bool = False,
    has_technical_docs: bool = False,
    has_logging: bool = False,
    has_transparency: bool = False,
    has_data_governance: bool = False,
    has_accuracy_metrics: bool = False,
    has_robustness_testing: bool = False,
    has_cybersecurity: bool = False,
    has_conformity_assessment: bool = False,
    has_post_market_monitoring: bool = False,
    has_incident_reporting: bool = False,
    has_registration: bool = False,
    has_declaration_of_conformity: bool = False,
    has_ce_marking: bool = False,
    has_precision_metrics: bool = False,
) -> ComplianceResult:
    """Evaluate an AI system against the 16 AESIA compliance guides.

    Parameters
    ----------
    system_description:
        Free-text description of the AI system.
    sector:
        Business sector the system operates in.
    has_*:
        Boolean flags indicating which compliance measures are already in place.

    Returns
    -------
    ComplianceResult
        Compliance status, percentage score, per-guide status, missing items,
        and a prioritised action list.
    """
    flags: dict[str, bool] = {
        "has_risk_management": has_risk_management,
        "has_human_oversight": has_human_oversight,
        "has_technical_docs": has_technical_docs,
        "has_logging": has_logging,
        "has_transparency": has_transparency,
        "has_data_governance": has_data_governance,
        "has_accuracy_metrics": has_accuracy_metrics,
        "has_robustness_testing": has_robustness_testing,
        "has_cybersecurity": has_cybersecurity,
        "has_conformity_assessment": has_conformity_assessment,
        "has_post_market_monitoring": has_post_market_monitoring,
        "has_incident_reporting": has_incident_reporting,
        "has_registration": has_registration,
        "has_declaration_of_conformity": has_declaration_of_conformity,
        "has_ce_marking": has_ce_marking,
        "has_precision_metrics": has_precision_metrics,
    }

    guides: dict[str, GuideStatus] = {}
    missing: list[str] = []
    compliant_count = 0

    for gdef in _GUIDE_DEFINITIONS:
        flag_value = flags.get(gdef["flag"], False)
        status = GuideStatus(
            code=gdef["code"],
            title=gdef["title"],
            article=gdef["article"],
            compliant=flag_value,
            required=True,
            action=None if flag_value else gdef["action"],
            priority=gdef["priority"],
        )
        guides[gdef["code"]] = status
        if flag_value:
            compliant_count += 1
        else:
            missing.append(f"{gdef['code']} — {gdef['title']}: {gdef['action']}")

    total = len(_GUIDE_DEFINITIONS)
    score = round((compliant_count / total) * 100, 1)
    fully_compliant = compliant_count == total

    # Sort action list by priority (critical first)
    priority_actions: list[str] = []
    for p in (1, 2, 3):
        for gdef in _GUIDE_DEFINITIONS:
            if not flags.get(gdef["flag"], False) and gdef["priority"] == p:
                label = {1: "CRITICAL", 2: "HIGH", 3: "MEDIUM"}[p]
                priority_actions.append(f"[{label}] {gdef['code']} — {gdef['title']}")

    summary = (
        f"Sector: {sector}. "
        f"Compliant with {compliant_count}/{total} AESIA guides ({score}%). "
        f"{'All obligations met.' if fully_compliant else f'{len(missing)} requirement(s) pending.'}"
    )

    return ComplianceResult(
        compliant=fully_compliant,
        score=score,
        guides=guides,
        missing=missing,
        priority=priority_actions,
        summary=summary,
    )
