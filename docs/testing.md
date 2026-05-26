# Test Execution Guide

## Pytest Markers

This project uses pytest markers to categorize tests:

- `unit`: Fast unit tests with no external dependencies
- `functional`: Tests that interact with CLI or use mocked dependencies  
- `integration`: Tests with real external dependencies
- `slow`: Tests that take significant time (system resource access, etc.)

## Running Tests

### Fast Development Workflow
Skip slow tests for quick feedback during development:
```bash
pytest -m "not slow"
```

### Full Test Suite
Run all tests including slow ones:
```bash
pytest
```

### Specific Categories
Run only specific test categories:
```bash
pytest -m "unit"           # Only unit tests
pytest -m "functional"     # Only functional tests  
pytest -m "slow"          # Only slow tests
pytest -m "unit or functional and not slow"  # Complex combinations
```

### Coverage Without Slow Tests
```bash
pytest --cov=causaliq_core -m "not slow"
```

## R Integration Tests

R integration tests call real R/bnlearn via subprocess and are skipped
automatically when R or bnlearn is not installed.

### Running locally

```powershell
.\scripts\activate.ps1; python -m pytest -m r_integration -v --no-cov
```

### Running on GitHub Actions

R integration tests do not run automatically on every commit. They are
triggered manually when needed (e.g. before a release, or after changes
to the R session layer):

1. Go to the repository on GitHub.
2. Click the **Actions** tab.
3. Select **R Integration** in the left sidebar.
4. Click **Run workflow** → **Run workflow**.

The workflow runs on Ubuntu and Windows with Python 3.11. R packages are
cached between runs to avoid reinstalling bnlearn from scratch each time.

## Environment Tests

The `tests/functional/test_environment.py` tests are marked as `slow` because they:
- Access real system resources (CPU info, memory stats)
- Read/write to filesystem cache
- Take longer to execute

These tests are important for validating cross-platform behavior but can be skipped during rapid development cycles.