# aia-compliance

[![PyPI version](https://img.shields.io/pypi/v/aia-compliance.svg)](https://pypi.org/project/aia-compliance/)
[![Tests](https://github.com/SoberanIA-ai/aia-compliance/actions/workflows/tests.yml/badge.svg)](https://github.com/SoberanIA-ai/aia-compliance/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Python library for EU AI Act (Regulation 2024/1689) compliance assessment.**

Built on the 16 guides published by AESIA (Agencia Española de Supervisión de la Inteligencia Artificial) and the official text of the AI Act. Fully deterministic — no LLMs, no external API calls.

> **Enforcement timeline:** General obligations apply from **2 August 2026**. High-risk system requirements under Annex III are already in force for new systems. Start your compliance journey now.

---

## What is the EU AI Act?

The EU AI Act (Regulation 2024/1689) is the world's first comprehensive legal framework for artificial intelligence. It classifies AI systems into risk tiers and imposes proportionate obligations on providers and deployers:

| Risk Level | Examples | Key Obligations |
|------------|----------|-----------------|
| **Unacceptable** | Social scoring, manipulative AI | Prohibited (Art. 5) |
| **High** | Healthcare AI, hiring systems, biometrics | Full compliance package (Arts. 9–15, 43–49) |
| **Limited** | Chatbots, deepfake generators | Transparency disclosure (Art. 50) |
| **Minimal** | Spam filters, recommendation systems | Voluntary codes of conduct |

---

## Installation

```bash
pip install aia-compliance
```

For PostgreSQL audit log support:

```bash
pip install aia-compliance[postgres]
```

---

## Quick Start

```python
from aia_compliance import classify, check_aesia_compliance, AuditLog, generate_document_checklist

# 1. Classify your AI system's risk level
result = classify(
    sector="healthcare",
    data_types=["health", "personal"],
    autonomy="automated",
    affected_persons=500,
    legal_effects=True,
)

print(result.risk_level)      # "high"
print(result.score)           # 85
print(result.annex_iii_match) # True
print(result.obligations)     # ["Art. 9 — Risk management system", ...]
print(result.explanation)     # Human-readable explanation

# 2. Check compliance against AESIA's 16 guides
compliance = check_aesia_compliance(
    system_description="AI system for patient triage in hospital ERs",
    sector="healthcare",
    has_risk_management=True,
    has_human_oversight=True,
    has_technical_docs=False,
    has_logging=True,
    has_transparency=False,
    has_data_governance=True,
)

print(compliance.compliant)   # False
print(compliance.score)       # 37.5
print(compliance.missing)     # ["G03 — Technical Documentation: ...", ...]
print(compliance.priority)    # ["[CRITICAL] G03 — Technical Documentation", ...]

# 3. Generate your required document checklist
docs = generate_document_checklist(risk_level="high", sector="healthcare")
print(docs.mandatory_count)   # 13
for doc in docs.documents:
    print(f"[{'x' if doc.mandatory else ' '}] {doc.name} ({doc.article})")

# 4. Record AI decisions in an immutable audit log
log = AuditLog(storage="sqlite:///audit.db")

entry = log.record(
    action="authorization_decision",
    actor="ai_agent",
    input_data={"patient_id": "p-001", "insurer": "acme"},
    output_data={"decision": "approved", "confidence": 0.92},
    model_used="mistral-large",
    human_reviewed=False,
)

print(entry.hash_sha256)      # SHA-256 of the entry
print(entry.chain_hash)       # Chained with previous entry

print(log.verify_integrity()) # True — chain is intact
report = log.export_audit_report()
```

---

## API Reference

### `classify(sector, data_types, autonomy, affected_persons, legal_effects, **flags) → RiskClassification`

Classifies an AI system under the EU AI Act Annex III.

| Parameter | Type | Values |
|-----------|------|--------|
| `sector` | `str` | `biometrics`, `critical_infrastructure`, `education`, `employment`, `essential_services`, `law_enforcement`, `migration`, `justice`, `healthcare` |
| `data_types` | `list[str]` | `biometric`, `health`, `financial`, `personal` |
| `autonomy` | `str` | `automated`, `assisted`, `analysis` |
| `affected_persons` | `int` | Number of persons affected |
| `legal_effects` | `bool` | Does it produce legal or significant effects? |
| `precision_undefined` | `bool` | Are accuracy metrics missing? (AESIA G09) |
| `robustness_undocumented` | `bool` | Is robustness testing undocumented? (AESIA G10) |
| `cybersecurity_missing` | `bool` | Are cybersecurity measures absent? (AESIA G11) |

**Returns:** `RiskClassification(risk_level, score, annex_iii_match, obligations, explanation, score_breakdown)`

---

### `check_aesia_compliance(system_description, sector, **flags) → ComplianceResult`

Evaluates compliance against the 16 AESIA guides.

| Flag | AESIA Guide | Article |
|------|-------------|---------|
| `has_risk_management` | G01 | Art. 9 |
| `has_data_governance` | G02 | Art. 10 |
| `has_technical_docs` | G03 | Art. 11 |
| `has_logging` | G04 | Art. 12 |
| `has_transparency` | G05 | Art. 13 |
| `has_human_oversight` | G06 | Art. 14 |
| `has_accuracy_metrics` | G07 | Art. 15 |
| `has_conformity_assessment` | G08 | Art. 43 |
| `has_precision_metrics` | G09 | Art. 15 |
| `has_robustness_testing` | G10 | Art. 15 |
| `has_cybersecurity` | G11 | Art. 15 |
| `has_post_market_monitoring` | G12 | Art. 61 |
| `has_incident_reporting` | G13 | Art. 62 |
| `has_registration` | G14 | Art. 49 |
| `has_declaration_of_conformity` | G15 | Art. 47 |
| `has_ce_marking` | G16 | Art. 48 |

**Returns:** `ComplianceResult(compliant, score, guides, missing, priority, summary)`

---

### `calculate_score(...) → ScoreResult`

Low-level deterministic scoring engine. Returns the raw and capped score with a per-factor breakdown.

**Scoring weights:**

| Factor | Weight |
|--------|--------|
| Biometric data | 35 |
| Health data | 30 |
| Financial data | 20 |
| Personal data | 15 |
| Security / law enforcement sector | 40 |
| Healthcare / employment sector | 35 |
| Credit / public services sector | 30 |
| Education sector | 25 |
| Automated decision-making | 40 |
| Human-assisted decision | 15 |
| Analysis only | 5 |
| >1,000 affected persons | 20 |
| 100–1,000 affected persons | 10 |
| <100 affected persons | 5 |
| Legal/significant effects (Art. 6.2) | 30 |
| Precision undefined (G09) | 15 |
| Robustness undocumented (G10) | 15 |
| Cybersecurity missing (G11) | 15 |

---

### `AuditLog(storage) → AuditLog`

Tamper-evident audit log backed by SQLite or PostgreSQL.

```python
log = AuditLog(storage="sqlite:///audit.db")
log = AuditLog(storage="postgresql://user:pass@localhost/db")  # requires [postgres]

entry = log.record(action, actor, input_data, output_data, model_used, human_reviewed, metadata)
log.verify_integrity()     # raises IntegrityError if tampered
log.export_audit_report()  # full JSON-serialisable report
log.close()
```

---

### `generate_document_checklist(risk_level, sector) → DocumentChecklist`

Returns the list of documents required or recommended for compliance, with article references.

---

## Examples by Sector

### Healthcare

```python
from aia_compliance import classify

result = classify(
    sector="healthcare",
    data_types=["health"],
    autonomy="automated",
    affected_persons=1000,
    legal_effects=True,
)
# risk_level = "high" → full Art. 9-15 + conformity assessment required
```

### Employment

```python
result = classify(
    sector="employment",
    data_types=["personal"],
    autonomy="assisted",
    affected_persons=200,
    legal_effects=True,
)
# Automated CV screening with human review → high risk
```

### Education

```python
result = classify(
    sector="education",
    data_types=["personal"],
    autonomy="analysis",
    affected_persons=50,
    legal_effects=False,
)
# Analytics dashboard for teachers → minimal/low risk
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting issues, proposing changes, and adding new AESIA guides.

---

## Legal Notice

This library provides compliance tooling based on publicly available information about the EU AI Act (Regulation 2024/1689) and AESIA guidance. It does not constitute legal advice. Consult qualified legal counsel for compliance decisions.

---

## License

[MIT](LICENSE) — Copyright (c) 2024 SoberanIA
