"""R session management via Rscript subprocess."""

import os
import shutil
import subprocess
from typing import Optional

from causaliq_core.r.exceptions import (
    RNotAvailableError,
    RRuntimeError,
)


def _find_rscript() -> Optional[str]:
    """Return path to the Rscript executable, or None if not found.

    Searches PATH first, then falls back to the R_HOME environment
    variable to locate the executable on Windows.

    Returns:
        Absolute path to Rscript, or None if not found.
    """
    path = shutil.which("Rscript")
    if path:
        return path
    r_home = os.environ.get("R_HOME", "")
    if r_home:
        for candidate in (
            os.path.join(r_home, "bin", "Rscript.exe"),
            os.path.join(r_home, "bin", "Rscript"),
            os.path.join(r_home, "bin", "x64", "Rscript.exe"),
        ):
            if os.path.isfile(candidate):
                return candidate
    return None


def run_r_script(script: str, timeout: int = 60) -> str:
    """Run R code via Rscript subprocess and return stdout.

    The script is piped via stdin to avoid temporary files and
    file-locking issues under parallel test execution.

    Args:
        script: R source code to execute.
        timeout: Seconds to wait before raising
                 subprocess.TimeoutExpired.

    Raises:
        RNotAvailableError: If Rscript cannot be found.
        RRuntimeError: If the script exits with a non-zero status.

    Returns:
        The stdout produced by the R script.
    """
    rscript = _find_rscript()
    if rscript is None:
        raise RNotAvailableError(
            "Rscript not found. Install R from " "https://cran.r-project.org/"
        )
    result = subprocess.run(
        [rscript, "--vanilla", "-"],
        input=script,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RRuntimeError(result.stderr.strip())
    return result.stdout
