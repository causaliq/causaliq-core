"""
Action input contract and parameter default resolution.

A provider declares its inputs with :class:`ActionInput`. This module
checks that declaration when a provider class is defined, and fills in
the declared defaults for the parameters that apply to an action.
"""

from __future__ import annotations

from typing import Any, Dict

from causaliq_core.action.errors import ActionValidationError
from causaliq_core.action.spec import NO_DEFAULT, ActionInput


def _check_input_choices(where: str, spec: ActionInput) -> None:
    """Raise when an input's choices are empty, null or miss the default.

    Args:
        where: Location prefix used in the error message.
        spec: Input specification to check.

    Raises:
        ActionValidationError: If the choices set is unusable or does not
            contain the declared default.
    """
    if spec.choices is None:
        return
    if not spec.choices:
        raise ActionValidationError(f"{where}: choices must not be empty")
    if any(choice is None for choice in spec.choices):
        raise ActionValidationError(
            f"{where}: choices must not contain null; the user omits the "
            f"parameter instead"
        )
    if spec.default is not NO_DEFAULT and spec.default not in spec.choices:
        raise ActionValidationError(
            f"{where}: default {spec.default!r} is not one of its choices "
            f"{list(spec.choices)!r}"
        )


def _check_input_spec(provider_name: str, key: str, spec: Any) -> None:
    """Raise when one action input specification breaks the contract.

    Specifications that are not :class:`ActionInput` instances are
    ignored so that legacy and mock providers keep working.

    Args:
        provider_name: Provider name used in error messages.
        key: Dictionary key the specification is declared under.
        spec: Value found in the provider's ``inputs`` mapping.

    Raises:
        ActionValidationError: If the specification is inconsistent.
    """
    if not isinstance(spec, ActionInput):
        return
    where = f"Provider '{provider_name}' input '{key}'"
    if spec.name != key:
        raise ActionValidationError(
            f"{where}: declared name '{spec.name}' does not match its key"
        )
    if spec.required and spec.default is not NO_DEFAULT:
        raise ActionValidationError(
            f"{where}: a required input must not declare a default"
        )
    if spec.default is None:
        raise ActionValidationError(
            f"{where}: a null default is not supported; omit the "
            f"parameter instead or declare an explicit value"
        )
    _check_input_choices(where, spec)


def _check_input_specs(
    provider_name: str, inputs: Dict[str, ActionInput]
) -> None:
    """Raise when a provider's input specifications break the contract.

    Args:
        provider_name: Provider name used in error messages.
        inputs: The provider's declared input specifications.

    Raises:
        ActionValidationError: If any specification is inconsistent.
    """
    for key, spec in inputs.items():
        _check_input_spec(provider_name, key, spec)


def _applicable_inputs(provider: Any, action: str) -> Dict[str, ActionInput]:
    """Return the input specifications that apply to one action.

    A provider that declares ``action_parameters`` (action name to
    accepted parameter names) restricts defaults to those parameters.
    An action the provider does not list receives no defaults, so an
    unknown action is reported by action-specific validation rather than
    by an unexpected parameter.

    Args:
        provider: Action provider instance or class.
        action: Action name the parameters apply to.

    Returns:
        Mapping of applicable input specifications.
    """
    inputs: Dict[str, ActionInput] = dict(getattr(provider, "inputs", {}))
    action_parameters = getattr(provider, "action_parameters", None)
    if not isinstance(action_parameters, dict):
        return inputs
    if action not in action_parameters:
        return {}
    names = action_parameters[action]
    return {name: spec for name, spec in inputs.items() if name in names}


def resolve_action_parameters(
    provider: Any,
    action: str,
    supplied: Dict[str, Any],
) -> Dict[str, Any]:
    """Return the effective parameters for one action.

    Supplied values win. A parameter that was omitted takes its declared
    default when it applies to the action. A parameter supplied as
    ``None`` marks a matrix dimension that is not applicable: it is left
    out and does not receive a default.

    Args:
        provider: Action provider instance or class.
        action: Action name the parameters apply to.
        supplied: Parameters supplied by the workflow step.

    Returns:
        Effective parameters, with declared defaults filled in and
        parameters that do not apply left out.
    """
    effective = {
        name: value for name, value in supplied.items() if value is not None
    }
    for name, spec in _applicable_inputs(provider, action).items():
        if name in supplied or spec.default is NO_DEFAULT:
            continue
        effective[name] = spec.default
    return effective
