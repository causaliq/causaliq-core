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

## Environment Tests

The `tests/functional/test_environment.py` tests are marked as `slow` because they:
- Access real system resources (CPU info, memory stats)
- Read/write to filesystem cache
- Take longer to execute

These tests are important for validating cross-platform behavior but can be skipped during rapid development cycles.