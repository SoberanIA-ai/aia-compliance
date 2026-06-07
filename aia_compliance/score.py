"""Deterministic scoring engine for EU AI Act risk assessment.

Same input always produces the same output — auditable and reproducible.
Weights are based on the 16 AESIA guides and Art. 6.2 of the AI Act.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .exceptions import InvalidInputError

WEIGHTS: dict = {
    "data_types": {
        "biometric": 35,
        "health": 30,
        "financial": 20,
        "personal": 15,
    },
    "sector": {
        "security": 40,
        "healthcare_employment": 35,
        "credit_public": 30,
        "education": 25,
    },
    "autonomy": {
        "automated": 40,
        "assisted": 15,
        "analysis": 5,
    },
    "affected_persons": {
        "over_1000": 20,
        "100_to_1000": 10,
        "under_100": 5,
    },
    "legal_effects": 30,           # Art. 6.2
    "precision_undefined": 15,     # AESIA Guide 09
    "robustness_undocumented": 15, # AESIA Guide 10
    "cybersecurity_missing": 15,   # AESIA Guide 11
}

_SECTOR_WEIGHT_MAP: dict[str, str] = {
    "biometrics": "security",
    "critical_infrastructure": "security",
    "law_enforcement": "security",
    "migration": "security",
    "justice": "security",
    "healthcare": "healthcare_employment",
    "employment": "healthcare_employment",
    "essential_services": "credit_public",
    "education": "education",
}

_VALID_AUTONOMY = frozenset(WEIGHTS["autonomy"])
_VALID_DATA_TYPES = frozenset(WEIGHTS["data_types"])

THRESHOLDS: list[tuple[int, int, str]] = [
    (0, 24, "minimal"),
    (25, 49, "low"),
    (50, 74, "limited"),
    (75, 100, "high"),
]


@dataclass(frozen=True)
class ScoreResult:
    """Output of the deterministic scoring engine."""

    raw_score: int
    capped_score: int
    risk_band: str
    breakdown: dict[str, int]


def score_to_risk_band(score: int) -> str:
    for lo, hi, label in THRESHOLDS:
        if lo <= score <= hi:
            return label
    return "high"


def calculate_score(
    sector: str,
    data_types: Sequence[str],
    autonomy: str,
    affected_persons: int,
    legal_effects: bool,
    precision_undefined: bool = False,
    robustness_undocumented: bool = False,
    cybersecurity_missing: bool = False,
) -> ScoreResult:
    """Calculate a deterministic compliance risk score.

    Returns the same result for the same inputs every time.
    """
    if autonomy not in _VALID_AUTONOMY:
        raise InvalidInputError(
            f"Invalid autonomy '{autonomy}'. Choose from: {', '.join(sorted(_VALID_AUTONOMY))}"
        )

    breakdown: dict[str, int] = {}
    total = 0

    # Data types — take the highest single weight, not cumulative
    max_data_weight = 0
    for dt in data_types:
        dt_norm = dt.lower()
        if dt_norm not in _VALID_DATA_TYPES:
            raise InvalidInputError(
                f"Invalid data type '{dt}'. Choose from: {', '.join(sorted(_VALID_DATA_TYPES))}"
            )
        w = WEIGHTS["data_types"][dt_norm]
        if w > max_data_weight:
            max_data_weight = w
    if max_data_weight:
        breakdown["data_types"] = max_data_weight
        total += max_data_weight

    # Sector
    sector_norm = sector.lower()
    sector_key = _SECTOR_WEIGHT_MAP.get(sector_norm)
    if sector_key:
        w = WEIGHTS["sector"][sector_key]
        breakdown["sector"] = w
        total += w

    # Autonomy
    w = WEIGHTS["autonomy"][autonomy]
    breakdown["autonomy"] = w
    total += w

    # Affected persons
    if affected_persons > 1000:
        persons_key = "over_1000"
    elif affected_persons >= 100:
        persons_key = "100_to_1000"
    else:
        persons_key = "under_100"
    w = WEIGHTS["affected_persons"][persons_key]
    breakdown["affected_persons"] = w
    total += w

    # Boolean risk factors
    if legal_effects:
        breakdown["legal_effects"] = WEIGHTS["legal_effects"]
        total += WEIGHTS["legal_effects"]

    if precision_undefined:
        breakdown["precision_undefined"] = WEIGHTS["precision_undefined"]
        total += WEIGHTS["precision_undefined"]

    if robustness_undocumented:
        breakdown["robustness_undocumented"] = WEIGHTS["robustness_undocumented"]
        total += WEIGHTS["robustness_undocumented"]

    if cybersecurity_missing:
        breakdown["cybersecurity_missing"] = WEIGHTS["cybersecurity_missing"]
        total += WEIGHTS["cybersecurity_missing"]

    capped = min(100, total)
    return ScoreResult(
        raw_score=total,
        capped_score=capped,
        risk_band=score_to_risk_band(capped),
        breakdown=breakdown,
    )
