"""Root conftest for causaliq-core test suite.

Registers custom pytest markers and applies automatic skip logic for
tests requiring external language runtimes.
"""

import pytest

from causaliq_core.r.availability import (
    is_r_available,
    is_r_package_available,
)


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers with pytest."""
    config.addinivalue_line(
        "markers",
        "r_integration: marks tests requiring R, rpy2 and bnlearn",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list,
) -> None:
    """Auto-skip r_integration tests when R or bnlearn is unavailable."""
    if not is_r_available() or not is_r_package_available("bnlearn"):
        skip = pytest.mark.skip(reason="R, rpy2 or bnlearn not available")
        for item in items:
            if "r_integration" in item.keywords:
                item.add_marker(skip)
