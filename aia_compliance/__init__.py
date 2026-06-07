"""aia-compliance — EU AI Act compliance assessment library.

Quick start
-----------
.. code-block:: python

    from aia_compliance import classify, check_aesia_compliance, AuditLog

    # 1. Classify risk level
    result = classify(
        sector="healthcare",
        data_types=["health", "personal"],
        autonomy="automated",
        affected_persons=500,
        legal_effects=True,
    )
    print(result.risk_level)   # "high"
    print(result.score)        # 0-100

    # 2. Check AESIA guide compliance
    compliance = check_aesia_compliance(
        system_description="Patient triage AI",
        sector="healthcare",
        has_risk_management=True,
        has_human_oversight=True,
    )
    print(compliance.score)    # % compliant

    # 3. Immutable audit log
    log = AuditLog(storage="sqlite:///audit.db")
    entry = log.record(
        action="triage_decision",
        actor="ai_agent",
        input_data={"patient_id": "p-001"},
        output_data={"priority": "urgent"},
        model_used="mistral-large",
        human_reviewed=False,
    )
    print(log.verify_integrity())  # True
"""
from .audit_log import AuditLog, AuditEntry
from .checklist import check_aesia_compliance, ComplianceResult, GuideStatus
from .classifier import classify, RiskClassification, ANNEX_III_SECTORS
from .documents import generate_document_checklist, DocumentChecklist, RequiredDocument
from .exceptions import (
    AIAComplianceError,
    InvalidSectorError,
    InvalidInputError,
    AuditLogError,
    IntegrityError,
)
from .score import calculate_score, ScoreResult, WEIGHTS

__version__ = "0.1.0"
__all__ = [
    # Core functions
    "classify",
    "check_aesia_compliance",
    "calculate_score",
    "generate_document_checklist",
    # Classes
    "AuditLog",
    "AuditEntry",
    "RiskClassification",
    "ComplianceResult",
    "GuideStatus",
    "DocumentChecklist",
    "RequiredDocument",
    "ScoreResult",
    # Constants
    "ANNEX_III_SECTORS",
    "WEIGHTS",
    # Exceptions
    "AIAComplianceError",
    "InvalidSectorError",
    "InvalidInputError",
    "AuditLogError",
    "IntegrityError",
]
