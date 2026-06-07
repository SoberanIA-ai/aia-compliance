# Contributing to aia-compliance

Thank you for helping improve EU AI Act compliance tooling. This document explains how to contribute effectively.

## Reporting Issues

Use [GitHub Issues](https://github.com/SoberanIA-ai/aia-compliance/issues) to report:

- **Bugs** — unexpected behaviour, wrong risk classifications, broken audit log integrity
- **Inaccuracies** — if an AESIA guide mapping or article reference is wrong
- **New AESIA guides** — when AESIA publishes updates beyond the initial 16 guides

When filing a bug, include:
1. Python version and OS
2. `pip show aia-compliance` output
3. Minimal reproducible example
4. Expected vs. actual output

## Proposing Changes

For non-trivial changes, open an issue first to discuss the approach before writing code. This avoids wasted effort on directions the maintainers won't merge.

Good candidates for contributions:
- New sector mappings as the AI Act's secondary legislation evolves
- Additional AESIA guides (G17+) when published
- New backend adapters for the audit log (e.g. MongoDB, BigQuery)
- Performance improvements to the scoring engine
- Additional language READMEs

## Adding New AESIA Guides

When AESIA publishes new guides beyond the current 16:

1. Open an issue linking the official AESIA publication
2. Add the new guide entry to `_GUIDE_DEFINITIONS` in `aia_compliance/checklist.py`:
   ```python
   {
       "code": "G17",
       "title": "New Guide Title",
       "article": "Art. XX",
       "flag": "has_new_guide",
       "action": "Action required to comply.",
       "priority": 2,
   }
   ```
3. Add the corresponding parameter to `check_aesia_compliance()` with a `False` default
4. Add the parameter to `__init__.py` docstring
5. Add tests to `tests/test_checklist.py`
6. Update `CHANGELOG.md`

## Development Setup

```bash
git clone https://github.com/SoberanIA-ai/aia-compliance.git
cd aia-compliance
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest                    # run all tests with coverage
pytest tests/test_score.py  # single module
pytest -v                 # verbose output
```

Tests must maintain ≥90% coverage. The CI gate enforces this on every PR.

## PR Process

1. Fork the repository and create a feature branch: `git checkout -b feat/your-feature`
2. Write or update tests — PRs without tests for new functionality will not be merged
3. Ensure `pytest` passes locally with ≥90% coverage
4. Run `ruff check .` and `black --check .` — fix any issues
5. Update `CHANGELOG.md` under `[Unreleased]`
6. Open a PR against `main` with a clear description of the change and its motivation

### PR Review Criteria

- Correctness: does the change accurately reflect the AI Act or AESIA guidance?
- Determinism: does `calculate_score` and `classify` remain fully deterministic?
- Backwards compatibility: existing function signatures must not change in patch/minor releases
- Test coverage: new code paths must be covered

## Legal Accuracy

This library maps regulatory obligations to code. Any change affecting risk classification, article references, or compliance guide mappings must cite the specific article or AESIA document being implemented. Maintainers will verify against the official sources before merging.

Official sources:
- [Regulation (EU) 2024/1689](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)
- [AESIA compliance guides](https://www.aesia.es/)

## Code of Conduct

Be respectful, precise, and cite your sources. Regulatory work requires accuracy above all else.
