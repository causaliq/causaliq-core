"""
causaliq-core: Core utilities and classes for the CausalIQ ecosystem
"""

from causaliq_core.action import (
    ActionExecutionError,
    ActionInput,
    ActionOutput,
    ActionResult,
    ActionValidationError,
    BaseActionProvider,
    CausalIQActionProvider,
    CoreActionProvider,
)
from causaliq_core.cache import TokenCache

__version__ = "0.4.0.dev3"
__author__ = "CausalIQ"
__email__ = "info@causaliq.org"

# Package metadata
__title__ = "causaliq-core"
__description__ = "Utility and graph classes for the CausalIQ ecosystem"

__url__ = "https://github.com/causaliq/causaliq-core"
__license__ = "MIT"


# Version tuple for programmatic access (strips dev/alpha/beta suffixes)
_version_parts = __version__.split(".")[:3]  # Take only major.minor.patch
VERSION = tuple(
    int(p.split("dev")[0].split("a")[0].split("b")[0]) for p in _version_parts
)

# Legacy software version constant
SOFTWARE_VERSION: int = 252

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "VERSION",
    "SOFTWARE_VERSION",
    "TokenCache",
    # Action provider framework
    "ActionExecutionError",
    "ActionInput",
    "ActionOutput",
    "ActionResult",
    "ActionValidationError",
    "BaseActionProvider",
    "CausalIQActionProvider",
    "CoreActionProvider",
]
