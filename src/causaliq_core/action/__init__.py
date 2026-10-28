"""
Action provider framework for CausalIQ workflow components.

This package provides the base classes and interfaces for implementing
action providers that expose multiple workflow actions.

The CausalIQActionProvider ABC defines the interface that all action
providers must implement. CoreActionProvider provides standard graphml
and json compression/decompression for workflow caches.

The framework is split by responsibility: specifications and sentinels
live in ``spec``, errors in ``errors``, the input contract in
``parameters``, the provider ABC in ``provider``, the core provider in
``core_provider`` and the GraphML binary codec in ``graphml_codec``.
Every public name is re-exported here so existing imports keep working.
"""

from causaliq_core.action.core_provider import CoreActionProvider
from causaliq_core.action.errors import (
    ActionExecutionError,
    ActionValidationError,
)
from causaliq_core.action.parameters import resolve_action_parameters
from causaliq_core.action.provider import (
    ActionResult,
    CausalIQActionProvider,
)
from causaliq_core.action.spec import (
    NO_DEFAULT,
    ActionInput,
    ActionOutput,
    ActionPattern,
)

# Export ActionProvider for auto-discovery by causaliq-workflow
ActionProvider = CoreActionProvider

__all__ = [
    "NO_DEFAULT",
    "ActionExecutionError",
    "ActionInput",
    "ActionOutput",
    "ActionPattern",
    "ActionProvider",
    "ActionResult",
    "ActionValidationError",
    "CausalIQActionProvider",
    "CoreActionProvider",
    "resolve_action_parameters",
]
