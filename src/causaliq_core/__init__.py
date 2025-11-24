"""
causaliq-core: Core utilities and classes for the CausalIQ ecosystem
"""

__version__ = "0.1.0"
__author__ = "CausalIQ"
__email__ = "info@causaliq.org"

# Package metadata
__title__ = "causaliq-core"
__description__ = "Core utilities and classes for the CausalIQ ecosystem"

__url__ = "https://github.com/causaliq/causaliq-core"
__license__ = "MIT"


# Version tuple for programmatic access
VERSION = tuple(map(int, __version__.split(".")))

# Legacy software version constant (migrated from legacy.py)
SOFTWARE_VERSION: int = 229


__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "VERSION",
    "SOFTWARE_VERSION",
]
