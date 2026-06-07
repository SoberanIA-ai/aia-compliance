# Changelog

All notable changes to `aia-compliance` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2024-06-05

### Added

- `classifier.py` — Deterministic risk classifier covering all 9 Annex III sectors
- `score.py` — Deterministic scoring engine with documented AESIA/AI Act weights
- `checklist.py` — Compliance checker against all 16 AESIA guides (G01–G16)
- `audit_log.py` — SHA-256 chain-hashed audit log with SQLite and PostgreSQL backends
- `documents.py` — Required document checklist generator by risk level
- `exceptions.py` — Custom exception hierarchy
- Full test suite with ≥90% coverage across Python 3.10, 3.11, 3.12
- GitHub Actions CI (tests) and CD (PyPI publish on release)
- README in English and Spanish

[Unreleased]: https://github.com/SoberanIA-ai/aia-compliance/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/SoberanIA-ai/aia-compliance/releases/tag/v0.1.0
