"""R and Rscript availability detection utilities."""

import subprocess

from causaliq_core.r.session import _find_rscript, run_r_script


def is_r_available() -> bool:
    """Return True if Rscript is available on this system.

    Safe to call unconditionally; returns False rather than raising
    when Rscript is absent or fails to run.

    Returns:
        True if Rscript is found and runs successfully, False
        otherwise.
    """
    rscript = _find_rscript()
    if rscript is None:
        return False
    try:
        result = subprocess.run(
            [rscript, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def is_r_package_available(package: str) -> bool:
    """Return True if the given R package is installed and loadable.

    Safe to call unconditionally; returns False rather than raising
    when R is absent or the package is not installed.

    Args:
        package: Name of the R package to check, e.g. 'bnlearn'.

    Returns:
        True if the package loads in R, False otherwise.
    """
    if not is_r_available():
        return False
    try:
        run_r_script(
            f'if (!requireNamespace("{package}", quietly=TRUE)) '
            f'stop("not available")',
            timeout=15,
        )
        return True
    except Exception:
        return False
