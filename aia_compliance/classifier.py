"""Risk classifier for EU AI Act (Annex III).

Classifies AI systems into risk levels based on sector, data types,
autonomy level, affected population, and legal effects.

Never uses an LLM — fully deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .exceptions import InvalidSectorError, InvalidInputError
from .score import calculate_score, ScoreResult

ANNEX_III_SECTORS: frozenset[str] = frozenset(
    {
        "biometrics",
        "critical_infrastructure",
        "education",
        "employment",
        "essential_services",
        "law_enforcement",
        "migration",
        "justice",
        "healthcare",
    }
)

_OBLIGATIONS: dict[str, list[str]] = {
    "high": [
        "Art. 9 — Risk management system",
        "Art. 10 — Data and data governance",
        "Art. 11 — Technical documentation",
        "Art. 12 — Record-keeping",
        "Art. 13 — Transparency and provision of information",
        "Art. 14 — Human oversight",
        "Art. 15 — Accuracy, robustness and cybersecurity",
        "Art. 43 — Conformity assessment",
        "Art. 47 — EU declaration of conformity",
        "Art. 48 — CE marking",
        "Art. 49 — Registration in EU database",
        "Art. 61 — Post-market monitoring",
        "Art. 62 — Reporting of serious incidents",
    ],
    "limited": [
        "Art. 50 — Transparency obligations for certain AI systems",
    ],
    "low": [],
    "minimal": [],
}

_ANNEX_III_EXPLANATIONS: dict[str, str] = {
    "biometrics": (
        "Biometric identification and categorisation systems fall under Annex III (1). "
        "Remote biometric ID in public spaces is prohibited (Art. 5) with narrow exceptions."
    ),
    "critical_infrastructure": (
        "AI systems used as safety components in critical infrastructure fall under Annex III (2)."
    ),
    "education": (
        "AI determining access or assigning students to educational institutions falls under Annex III (3)."
    ),
    "employment": (
        "AI for recruitment, task allocation or performance monitoring falls under Annex III (4)."
    ),
    "essential_services": (
        "AI evaluating creditworthiness or eligibility for essential services falls under Annex III (5)."
    ),
    "law_enforcement": (
        "AI used by law enforcement for risk assessment or evidence evaluation falls under Annex III (6)."
    ),
    "migration": (
        "AI for migration control, border management or asylum assessment falls under Annex III (7)."
    ),
    "justice": (
        "AI assisting judicial authorities in research or interpretation of facts falls under Annex III (8)."
    ),
    "healthcare": (
        "AI used as a medical device or in healthcare decisions affecting patients falls under Annex III (5)."
    ),
}


@dataclass(frozen=True)
class RiskClassification:
    """Result of classifying an AI system under the EU AI Act."""

    risk_level: str
    score: int
    annex_iii_match: bool
    obligations: list[str]
    explanation: str
    score_breakdown: dict[str, int] = field(default_factory=dict)


def classify(
    sector: str,
    data_types: Sequence[str],
    autonomy: str,
    affected_persons: int,
    legal_effects: bool,
    precision_undefined: bool = False,
    robustness_undocumented: bool = False,
    cybersecurity_missing: bool = False,
) -> RiskClassification:
    """Classify an AI system's risk level under the EU AI Act.

    Parameters
    ----------
    sector:
        Business/application sector. Must be one of the Annex III sectors.
    data_types:
        Types of personal data processed. Valid values: ``biometric``,
        ``health``, ``financial``, ``personal``.
    autonomy:
        Decision-making mode — ``automated``, ``assisted``, or ``analysis``.
    affected_persons:
        Estimated number of persons affected by the system.
    legal_effects:
        Whether decisions produce legal or similarly significant effects (Art. 6.2).
    precision_undefined:
        Whether accuracy/precision metrics are missing (AESIA Guide 09).
    robustness_undocumented:
        Whether robustness testing is undocumented (AESIA Guide 10).
    cybersecurity_missing:
        Whether cybersecurity measures are absent (AESIA Guide 11).

    Returns
    -------
    RiskClassification
        Immutable object with risk level, score, obligations and explanation.
    """
    sector_norm = sector.lower()
    if sector_norm not in ANNEX_III_SECTORS:
        raise InvalidSectorError(sector, sorted(ANNEX_III_SECTORS))

    if affected_persons < 0:
        raise InvalidInputError("affected_persons must be a non-negative integer.")

    result: ScoreResult = calculate_score(
        sector=sector_norm,
        data_types=data_types,
        autonomy=autonomy,
        affected_persons=affected_persons,
        legal_effects=legal_effects,
        precision_undefined=precision_undefined,
        robustness_undocumented=robustness_undocumented,
        cybersecurity_missing=cybersecurity_missing,
    )

    annex_iii_match = sector_norm in ANNEX_III_SECTORS
    risk_level = result.risk_band
    obligations = list(_OBLIGATIONS.get(risk_level, []))

    base_explanation = _ANNEX_III_EXPLANATIONS.get(sector_norm, "")
    risk_explanation = _build_risk_explanation(
        risk_level=risk_level,
        score=result.capped_score,
        breakdown=result.breakdown,
        annex_iii_match=annex_iii_match,
    )
    explanation = f"{base_explanation} {risk_explanation}".strip()

    return RiskClassification(
        risk_level=risk_level,
        score=result.capped_score,
        annex_iii_match=annex_iii_match,
        obligations=obligations,
        explanation=explanation,
        score_breakdown=result.breakdown,
    )


def _build_risk_explanation(
    risk_level: str,
    score: int,
    breakdown: dict[str, int],
    annex_iii_match: bool,
) -> str:
    drivers = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
    top_drivers = ", ".join(f"{k.replace('_', ' ')} (+{v})" for k, v in drivers[:3])

    level_texts = {
        "high": (
            f"Score {score}/100 → HIGH RISK. "
            f"Full compliance package required (Arts. 9–15, 43, 47–49, 61–62). "
        ),
        "limited": (
            f"Score {score}/100 → LIMITED RISK. "
            f"Transparency obligations apply (Art. 50). "
        ),
        "low": (
            f"Score {score}/100 → LOW RISK. "
            f"No mandatory requirements, voluntary codes of conduct recommended. "
        ),
        "minimal": (
            f"Score {score}/100 → MINIMAL RISK. "
            f"No specific EU AI Act obligations. Good practice guidelines apply. "
        ),
    }

    text = level_texts.get(risk_level, f"Score {score}/100.")
    if top_drivers:
        text += f"Main risk drivers: {top_drivers}."
    if annex_iii_match:
        text += " System falls within Annex III scope."
    return text
