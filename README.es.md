# aia-compliance

[![PyPI version](https://img.shields.io/pypi/v/aia-compliance.svg)](https://pypi.org/project/aia-compliance/)
[![Tests](https://github.com/SoberanIA-ai/aia-compliance/actions/workflows/tests.yml/badge.svg)](https://github.com/SoberanIA-ai/aia-compliance/actions/workflows/tests.yml)
[![Licencia: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Librería Python para la evaluación de cumplimiento del Reglamento de IA de la UE (2024/1689).**

Desarrollada por [SoberanIA](https://soberania.ai) — tu aliado en soberanía tecnológica e inteligencia artificial responsable. Basada en las 16 guías de AESIA (Agencia Española de Supervisión de la Inteligencia Artificial) y el texto oficial del Reglamento IA de la UE. Completamente determinista: sin LLMs, sin llamadas a APIs externas.

> **Fechas clave:** Las obligaciones generales aplican desde el **2 de agosto de 2026**. Los requisitos para sistemas de alto riesgo del Anexo III ya están en vigor para sistemas nuevos.

---

## ¿Qué es el Reglamento de IA de la UE?

El Reglamento IA de la UE (2024/1689) es el primer marco jurídico integral del mundo para la inteligencia artificial. Clasifica los sistemas de IA en niveles de riesgo e impone obligaciones proporcionales:

| Nivel de riesgo | Ejemplos | Obligaciones clave |
|-----------------|----------|-------------------|
| **Inaceptable** | Puntuación social, IA manipuladora | Prohibido (Art. 5) |
| **Alto** | IA sanitaria, contratación, biometría | Paquete completo (Arts. 9–15, 43–49) |
| **Limitado** | Chatbots, generadores de deepfakes | Declaración de transparencia (Art. 50) |
| **Mínimo** | Filtros de spam, recomendadores | Códigos de conducta voluntarios |

---

## Instalación

```bash
pip install aia-compliance
```

Con soporte para PostgreSQL:

```bash
pip install aia-compliance[postgres]
```

---

## Inicio rápido

```python
from aia_compliance import classify, check_aesia_compliance, AuditLog, generate_document_checklist

# 1. Clasificar el nivel de riesgo
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
print(result.obligations)     # ["Art. 9 — Sistema de gestión de riesgos", ...]

# 2. Comprobar cumplimiento de las 16 guías AESIA
compliance = check_aesia_compliance(
    system_description="Sistema de triaje de pacientes en urgencias hospitalarias",
    sector="healthcare",
    has_risk_management=True,
    has_human_oversight=True,
    has_technical_docs=False,
)

print(compliance.compliant)   # False
print(compliance.score)       # % de cumplimiento
print(compliance.priority)    # Lista priorizada de acciones

# 3. Generar checklist documental
docs = generate_document_checklist(risk_level="high", sector="healthcare")
print(docs.mandatory_count)   # Nº de documentos obligatorios

# 4. Registro de auditoría inmutable
log = AuditLog(storage="sqlite:///audit.db")
entry = log.record(
    action="decision_credito",
    actor="agente_ia",
    input_data={"solicitante": "s-001"},
    output_data={"decision": "aprobado", "confianza": 0.92},
    model_used="mistral-large",
    human_reviewed=False,
)
print(log.verify_integrity()) # True
```

---

## Referencia de la API

### `classify()` — Clasificador de riesgo

Clasifica un sistema de IA según el Anexo III del Reglamento IA.

**Sectores cubiertos:** `biometrics`, `critical_infrastructure`, `education`, `employment`, `essential_services`, `law_enforcement`, `migration`, `justice`, `healthcare`

**Retorna:** `RiskClassification` con `risk_level`, `score`, `annex_iii_match`, `obligations`, `explanation`

---

### `check_aesia_compliance()` — Verificador de las 16 guías AESIA

Evalúa el cumplimiento contra las 16 guías publicadas por AESIA.

| Guía | Descripción | Artículo |
|------|-------------|---------|
| G01 | Sistema de gestión de riesgos | Art. 9 |
| G02 | Gobernanza de datos | Art. 10 |
| G03 | Documentación técnica | Art. 11 |
| G04 | Registro y trazabilidad | Art. 12 |
| G05 | Transparencia | Art. 13 |
| G06 | Supervisión humana | Art. 14 |
| G07 | Exactitud, robustez y ciberseguridad | Art. 15 |
| G08 | Evaluación de conformidad | Art. 43 |
| G09 | Métricas de precisión | Art. 15 |
| G10 | Documentación de robustez | Art. 15 |
| G11 | Medidas de ciberseguridad | Art. 15 |
| G12 | Supervisión post-comercialización | Art. 61 |
| G13 | Notificación de incidentes | Art. 62 |
| G14 | Registro en base de datos UE | Art. 49 |
| G15 | Declaración UE de conformidad | Art. 47 |
| G16 | Marcado CE | Art. 48 |

---

### `AuditLog` — Registro de auditoría SHA-256 inmutable

Registro a prueba de manipulaciones para decisiones de IA. Compatible con Art. 12 y Art. 19 del Reglamento IA.

```python
log = AuditLog(storage="sqlite:///audit.db")
log = AuditLog(storage="postgresql://usuario:contraseña@servidor/basedatos")

entry = log.record(...)
log.verify_integrity()     # Verifica la cadena de hashes
log.export_audit_report()  # Exporta el informe completo
```

---

## Ejemplos por sector

### Sanidad

```python
result = classify(
    sector="healthcare",
    data_types=["health"],
    autonomy="automated",
    affected_persons=1000,
    legal_effects=True,
)
# → Alto riesgo: paquete completo de cumplimiento obligatorio
```

### Recursos Humanos

```python
result = classify(
    sector="employment",
    data_types=["personal"],
    autonomy="assisted",
    affected_persons=200,
    legal_effects=True,
)
# → Cribado de CVs con revisión humana: alto riesgo
```

### Educación

```python
result = classify(
    sector="education",
    data_types=["personal"],
    autonomy="analysis",
    affected_persons=50,
    legal_effects=False,
)
# → Panel de análisis para docentes: riesgo mínimo/bajo
```

---

## Integraciones enterprise

El equipo de SoberanIA está disponible para integraciones enterprise, formación y consultoría de cumplimiento del Reglamento IA. Contacta con nosotros en [info@soberania.ai](mailto:info@soberania.ai).

Servicios disponibles:
- Integración de `aia-compliance` en tus pipelines MLOps
- Formación para equipos de desarrollo y compliance
- Auditorías de sistemas de IA existentes
- Asesoría continua durante la fase de implementación del Reglamento IA

---

## Contribuir

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para información sobre cómo reportar issues, proponer cambios y añadir nuevas guías AESIA cuando se publiquen.

---

## Aviso legal

Esta librería proporciona herramientas de cumplimiento basadas en información públicamente disponible sobre el Reglamento IA de la UE (2024/1689) y las guías de AESIA. No constituye asesoramiento jurídico. Consulta con abogados especializados para decisiones de cumplimiento normativo.

---

## Licencia

[MIT](LICENSE) — Copyright (c) 2024 SoberanIA
