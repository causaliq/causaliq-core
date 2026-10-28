"""Unit tests for causaliq_core.action.parameters."""

from typing import Any, Dict

import pytest

from causaliq_core import (
    ActionInput,
    ActionResult,
    ActionValidationError,
    CausalIQActionProvider,
    resolve_action_parameters,
)


class _Provider(CausalIQActionProvider):
    """Minimal concrete provider for contract tests."""

    name = "test-provider"
    supported_actions = {"run"}

    def _execute(
        self, action, parameters, mode, context, logger
    ) -> ActionResult:
        return ("success", {}, [])


# Test an enumerated default is accepted when it is a member of choices.
def test_provider_accepts_enumerated_default() -> None:
    class ValidProvider(_Provider):
        inputs = {
            "randomise": ActionInput(
                name="randomise",
                description="Randomisation options",
                default="no-randomise",
                choices=("no-randomise", "var_best"),
            )
        }

    spec = ValidProvider.inputs["randomise"]
    assert spec.default == "no-randomise"


# Test an open-domain default needs no choices to be accepted.
def test_provider_accepts_open_domain_default() -> None:
    class ValidProvider(_Provider):
        inputs = {
            "timeout": ActionInput(
                name="timeout",
                description="Timeout in minutes",
                default=60,
                type_hint="int",
            )
        }

    assert ValidProvider.inputs["timeout"].default == 60


# Test a specification key that disagrees with its declared name fails.
def test_provider_rejects_name_mismatch() -> None:
    with pytest.raises(ActionValidationError, match="does not match its key"):

        class InvalidProvider(_Provider):
            inputs = {
                "timeout": ActionInput(
                    name="time_limits",
                    description="Timeout in minutes",
                    default=60,
                )
            }


# Test a required input must not declare a default.
def test_provider_rejects_required_default() -> None:
    with pytest.raises(ActionValidationError, match="must not declare"):

        class InvalidProvider(_Provider):
            inputs = {
                "input": ActionInput(
                    name="input",
                    description="Input path",
                    required=True,
                    default="data.csv",
                )
            }


# Test a null default is rejected.
def test_provider_rejects_null_default() -> None:
    with pytest.raises(ActionValidationError, match="null default"):

        class InvalidProvider(_Provider):
            inputs = {
                "trace": ActionInput(
                    name="trace",
                    description="Trace path",
                    default=None,
                )
            }


# Test an empty choices set is rejected.
def test_provider_rejects_empty_choices() -> None:
    with pytest.raises(ActionValidationError, match="must not be empty"):

        class InvalidProvider(_Provider):
            inputs = {
                "mode": ActionInput(
                    name="mode",
                    description="Mode",
                    default="fast",
                    choices=(),
                )
            }


# Test a choices set cannot contain a null entry.
def test_provider_rejects_null_choice() -> None:
    with pytest.raises(ActionValidationError, match="must not contain null"):

        class InvalidProvider(_Provider):
            inputs = {
                "mode": ActionInput(
                    name="mode",
                    description="Mode",
                    default="fast",
                    choices=("fast", None),
                )
            }


# Test a default outside the declared choices set is rejected.
def test_provider_rejects_default_outside_choices() -> None:
    with pytest.raises(ActionValidationError, match="not one of its choices"):

        class InvalidProvider(_Provider):
            inputs = {
                "mode": ActionInput(
                    name="mode",
                    description="Mode",
                    default="slow",
                    choices=("fast",),
                )
            }


# Test a legacy specification object is ignored by the contract check.
def test_provider_ignores_non_action_input() -> None:
    class LegacyProvider(_Provider):
        inputs = {"mode": {"name": "other"}}

    assert LegacyProvider.inputs["mode"] == {"name": "other"}


# Test a declared default is applied when the parameter is omitted.
def test_resolve_applies_default() -> None:
    class ValidProvider(_Provider):
        inputs = {
            "timeout": ActionInput(
                name="timeout",
                description="Timeout",
                default=60,
            )
        }

    parameters = resolve_action_parameters(ValidProvider(), "run", {})
    assert parameters == {"timeout": 60}


# Test a supplied value wins over the declared default.
def test_resolve_keeps_supplied_value() -> None:
    class ValidProvider(_Provider):
        inputs = {
            "timeout": ActionInput(
                name="timeout",
                description="Timeout",
                default=60,
            )
        }

    parameters = resolve_action_parameters(
        ValidProvider(), "run", {"timeout": 5}
    )
    assert parameters == {"timeout": 5}


# Test null-valued parameters are dropped as not applicable.
def test_resolve_drops_null_values() -> None:
    parameters = resolve_action_parameters(_Provider(), "run", {"x": None})
    assert parameters == {}


# Test an explicit null marks not-applicable and receives no default.
def test_resolve_does_not_default_a_null_value() -> None:
    class ValidProvider(_Provider):
        inputs = {
            "timeout": ActionInput(
                name="timeout",
                description="Timeout",
                default=60,
            )
        }

    parameters = resolve_action_parameters(
        ValidProvider(), "run", {"timeout": None}
    )
    assert parameters == {}


# Test a parameter without a default stays absent when omitted.
def test_resolve_omits_parameter_without_default() -> None:
    class ValidProvider(_Provider):
        inputs = {
            "seed": ActionInput(name="seed", description="Seed"),
        }

    parameters = resolve_action_parameters(ValidProvider(), "run", {})
    assert parameters == {}


# Test defaults are limited to the names an action declares.
def test_resolve_limits_defaults_to_declared_action() -> None:
    class MultiProvider(_Provider):
        supported_actions = {"first", "second"}
        inputs = {
            "alpha": ActionInput(
                name="alpha", description="Alpha", default="a"
            ),
            "beta": ActionInput(name="beta", description="Beta", default="b"),
        }
        action_parameters = {"first": {"alpha"}, "second": {"beta"}}

    parameters = resolve_action_parameters(MultiProvider(), "first", {})
    assert parameters == {"alpha": "a"}


# Test an action the provider does not list receives no defaults.
def test_resolve_unknown_action_receives_no_defaults() -> None:
    class MultiProvider(_Provider):
        supported_actions = {"first"}
        inputs = {
            "alpha": ActionInput(
                name="alpha", description="Alpha", default="a"
            ),
        }
        action_parameters = {"first": {"alpha"}}

    parameters = resolve_action_parameters(MultiProvider(), "other", {})
    assert parameters == {}


# Test supplied parameters that do not apply are passed through unchanged.
def test_resolve_keeps_supplied_parameters() -> None:
    parameters = resolve_action_parameters(
        _Provider(), "run", {"custom": "value"}
    )
    assert parameters == {"custom": "value"}


# Test the resolver accepts a class that only declares inputs.
def test_resolve_accepts_plain_provider_attributes() -> None:
    class Plain:
        inputs: Dict[str, Any] = {
            "timeout": ActionInput(
                name="timeout", description="Timeout", default=60
            )
        }

    parameters = resolve_action_parameters(Plain(), "run", {})
    assert parameters == {"timeout": 60}
