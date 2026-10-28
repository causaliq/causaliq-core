"""Unit tests for causaliq_core.action.errors."""

import pytest

from causaliq_core import ActionExecutionError, ActionValidationError

# ---------------------------------------------------------------------------
# Exception tests
# ---------------------------------------------------------------------------


# Test ActionExecutionError is proper exception.
def test_action_execution_error() -> None:
    with pytest.raises(ActionExecutionError, match="failed"):
        raise ActionExecutionError("Action failed")


# Test ActionValidationError is proper exception.
def test_action_validation_error() -> None:
    with pytest.raises(ActionValidationError, match="invalid"):
        raise ActionValidationError("Input invalid")
