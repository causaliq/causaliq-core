"""R and rpy2 availability detection utilities."""

import os
import sys
from contextlib import contextmanager
from typing import Generator


@contextmanager
def _suppress_fd_stderr() -> Generator[None, None, None]:
    """Redirect OS-level stderr to devnull during R probing.

    Suppresses subprocess stderr (e.g. R config.sh noise) that cannot
    be caught via sys.stderr redirection.
    """
    devnull = os.open(os.devnull, os.O_WRONLY)
    saved = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        sys.stderr.flush()
        os.dup2(saved, 2)
        os.close(saved)


def is_r_available() -> bool:
    """Return True if R is installed and rpy2 can connect to it.

    Safe to call unconditionally; returns False rather than raising
    when R or rpy2 is absent.

    Returns:
        True if rpy2 is installed and can connect to R, False
        otherwise.
    """
    try:
        with _suppress_fd_stderr():
            import rpy2.robjects  # noqa: F401

        return True
    except Exception:
        return False


def is_r_package_available(package: str) -> bool:
    """Return True if the specified R package is installed and loadable.

    Safe to call unconditionally; returns False rather than raising
    when R is absent or the package is not installed.

    Args:
        package: Name of the R package to check, e.g. 'bnlearn'.

    Returns:
        True if the package can be imported via rpy2, False otherwise.
    """
    if not is_r_available():
        return False
    try:
        from rpy2.robjects.packages import importr  # noqa: F401

        importr(package)
        return True
    except Exception:
        return False
