"""Root conftest for causaliq-core test suite.

Registers custom pytest markers and applies automatic skip logic for
tests requiring external language runtimes.
"""

import pytest

from causaliq_core.java.availability import is_java_available
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
    config.addinivalue_line(
        "markers",
        "java_integration: marks tests requiring Java and Java tools",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list,
) -> None:
    """Auto-skip external-runtime integration tests when unavailable."""
    r_available = is_r_available()
    bnlearn_available = (
        is_r_package_available("bnlearn") if r_available else False
    )

    if not r_available:
        skip = pytest.mark.skip(reason="R runtime not available")
        for item in items:
            if "r_integration" in item.keywords:
                item.add_marker(skip)
    elif not bnlearn_available:
        skip = pytest.mark.skip(reason="R package 'bnlearn' not available")
        for item in items:
            if "r_integration" in item.keywords:
                item.add_marker(skip)

    if not is_java_available():
        skip = pytest.mark.skip(reason="Java runtime not available")
        for item in items:
            if "java_integration" in item.keywords:
                item.add_marker(skip)
