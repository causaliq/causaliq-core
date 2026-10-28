"""
Errors raised by the action provider framework.

``ActionExecutionError`` reports a failure while an action runs and
``ActionValidationError`` reports an invalid action name or parameter.
"""

from __future__ import annotations


class ActionExecutionError(Exception):
    """Raised when action execution fails."""

    pass


class ActionValidationError(Exception):
    """Raised when action input validation fails."""

    pass
