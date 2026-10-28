"""
Action specification types for CausalIQ workflow components.

This module declares the shape of an action: its execution pattern, the
input parameters it accepts and the outputs it produces. These
specifications are the single source of truth for a parameter's default;
providers must not repeat a default in their own code.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Tuple


class ActionPattern(Enum):
    """Workflow action execution patterns.

    Defines how actions interact with caches and matrix definitions.
    The workflow executor validates and enforces these patterns.

    Attributes:
        CREATE: Writes new cache entries. Requires an output cache and a
            matrix; a cache input is prohibited.
        AGGREGATE: Combines existing cache entries into new entries.
            Requires a cache input, an output cache and a matrix.
    """

    CREATE = "create"
    AGGREGATE = "aggregate"


class _NoDefault:
    """Sentinel type marking an input that declares no default value."""

    def __repr__(self) -> str:
        """Return a readable name for documentation and logs."""
        return "NO_DEFAULT"


NO_DEFAULT = _NoDefault()
"""Sentinel used when an action input declares no default value.

``None`` cannot be used for this purpose because it is also a value a
user might supply. An omitted parameter that declares a default is filled
in by the framework; a parameter with no default stays absent, which
means it does not apply to the action in this configuration.
"""


@dataclass
class ActionInput:
    """Define action input specification.

    The specification is the single source of truth for a parameter's
    default. Providers must not repeat the default in their own code; the
    framework supplies it before the action runs.

    Attributes:
        name: Parameter name.
        description: Human-readable description.
        required: Whether the parameter is required. A required input
            must not declare a default.
        default: Default value if not provided, or ``NO_DEFAULT`` when
            the parameter has no default. A default must be a value the
            user could supply and must appear in ``choices`` when choices
            are declared. ``None`` is never a valid default.
        type_hint: Type hint string for documentation.
        choices: Closed set of values the parameter may take, or ``None``
            when any value of the declared type is accepted. For a
            list-valued parameter the choices enumerate the values each
            element may take, in addition to any scalar "off" token.
    """

    name: str
    description: str
    required: bool = False
    default: Any = NO_DEFAULT
    type_hint: str = "Any"
    choices: Optional[Tuple[Any, ...]] = None


@dataclass
class ActionOutput:
    """Define action output specification.

    Attributes:
        name: Output name.
        description: Human-readable description.
        value: Output value.
    """

    name: str
    description: str
    value: Any
