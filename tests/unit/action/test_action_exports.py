"""Unit tests for the public surface of causaliq_core.action."""

import pytest

import causaliq_core
from causaliq_core import CoreActionProvider
from causaliq_core.action import ActionProvider

# Public names expected from both causaliq_core and causaliq_core.action.
PUBLIC_NAMES = [
    "NO_DEFAULT",
    "ActionExecutionError",
    "ActionInput",
    "ActionOutput",
    "ActionPattern",
    "ActionResult",
    "ActionValidationError",
    "CausalIQActionProvider",
    "CoreActionProvider",
    "resolve_action_parameters",
]


# Test the alias used for workflow auto-discovery is the core provider.
def test_action_provider_alias_is_core_provider() -> None:
    assert ActionProvider is CoreActionProvider


# Test every public name is exported from the package and the root.
@pytest.mark.parametrize("name", PUBLIC_NAMES)
def test_public_names_exported_from_action_package(name: str) -> None:
    assert getattr(causaliq_core.action, name) is getattr(causaliq_core, name)
