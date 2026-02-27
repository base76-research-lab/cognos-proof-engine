# Contributing to CognOS Proof Engine

Thanks for contributing.

## Fast path

1. Fork the repo
2. Create a branch: `feat/short-description`
3. Make focused changes
4. Run relevant checks
5. Open a PR using the template

## What we value

- Small, testable PRs
- Clear problem statements
- Reproducible bug reports
- Docs updates for behavior changes

## Development checks

- Run syntax check for touched Python files:
  - `python3 -m py_compile src/main.py`
- Run smoke tests when relevant:
  - `python3 src/smoke_oc001.py`
  - `python3 src/smoke_oc002.py`

## Good first contributions

- Improve onboarding docs
- Add integration examples
- Improve error messages and runbooks
- Add test coverage around existing behavior

## Reporting bugs

Use the bug template and include:

- Expected behavior
- Actual behavior
- Reproduction steps
- Logs/status codes/trace IDs (if available)

## Security

Do not post secrets or API keys in issues.
If you find a sensitive issue, open a private report via repository contacts.
