"""Java integration layer for CausalIQ Core.

Provides subprocess-based Java runtime discovery and command
execution utilities used by downstream CausalIQ repositories.
"""

from causaliq_core.java.availability import is_java_available
from causaliq_core.java.exceptions import (
    JavaNotAvailableError,
    JavaRuntimeError,
)
from causaliq_core.java.session import run_java_jar

__all__ = [
    "is_java_available",
    "run_java_jar",
    "JavaNotAvailableError",
    "JavaRuntimeError",
]
