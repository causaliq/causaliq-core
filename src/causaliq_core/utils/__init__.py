"""
This module provides extended enumeration functionality, mathematical
utilities, and other utility classes commonly used across the CausalIQ
ecosystem.
"""

from enum import Enum
from typing import Any

from .environment import environment
from .io import FileFormatError, is_valid_path
from .math import ln, rndsf
from .random import RandomIntegers
from .timing import Timing


class EnumWithAttrs(Enum):
    """
    Base class for enumerations with additional read-only attributes.

    This class extends the standard Python Enum to support enums that carry
    additional attributes such as human-readable labels. Sub-classes can
    extend this pattern to include more attributes.

    Example:
        >>> class Status(EnumWithAttrs):
        ...     PENDING = 'pending', 'Pending Review'
        ...     APPROVED = 'approved', 'Approved for Use'
        ...     REJECTED = 'rejected', 'Rejected - Needs Changes'
        >>>
        >>> print(Status.PENDING)  # 'pending'
        >>> print(Status.PENDING.label)  # 'Pending Review'

    Note:
        Values should be set as tuples where the first element is the enum
        value and subsequent elements are the additional attributes.
        The base class provides a `label` attribute from the second tuple
        element.
    """

    def __new__(cls, *args: Any, **kwargs: Any) -> "EnumWithAttrs":
        """
        Create a new enum instance with additional attributes.

        Args:
            *args: The enum value and additional attribute values
            **kwargs: Additional keyword arguments (unused)

        Returns:
            New enum instance with the value set to the first argument
        """
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: str, label: str) -> None:
        """
        Initialise the enum instance with a label attribute.

        Args:
            _: The enum value (already set in __new__)
            label: Human-readable label for this enum value
        """
        self._label_ = label

    def __str__(self) -> str:
        """
        Return the string representation of the enum value.

        Returns:
            The enum's value as a string
        """
        return str(self.value)

    @property
    def label(self) -> str:
        """
        Get the human-readable label for this enum value.

        Returns:
            The label string for this enum value
        """
        return self._label_


__all__ = [
    "EnumWithAttrs",
    "environment",
    "rndsf",
    "ln",
    "FileFormatError",
    "is_valid_path",
    "RandomIntegers",
    "Timing",
]
