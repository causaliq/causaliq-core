"""R session initialisation and shared rpy2 access helpers."""

import importlib
from typing import Any

from causaliq_core.r.availability import (
    is_r_available,
    is_r_package_available,
)
from causaliq_core.r.exceptions import (
    RNotAvailableError,
    RPackageNotAvailableError,
)


def get_robjects() -> Any:
    """Return the rpy2.robjects module.

    Raises:
        RNotAvailableError: If R or rpy2 is not available.

    Returns:
        The rpy2.robjects module.
    """
    if not is_r_available():
        raise RNotAvailableError(
            "R is not available. Install R and rpy2 to use this "
            "functionality."
        )
    return importlib.import_module("rpy2.robjects")


def import_r_package(package: str) -> Any:
    """Import and return an R package via rpy2.

    Args:
        package: Name of the R package to import, e.g. 'bnlearn'.

    Raises:
        RNotAvailableError: If R or rpy2 is not available.
        RPackageNotAvailableError: If the package is not installed.

    Returns:
        The imported rpy2 R package object.
    """
    if not is_r_available():
        raise RNotAvailableError(
            "R is not available. Install R and rpy2 to use this "
            "functionality."
        )
    if not is_r_package_available(package):
        raise RPackageNotAvailableError(
            f"R package '{package}' is not installed."
        )
    from rpy2.robjects.packages import importr  # noqa: PLC0415

    return importr(package)
