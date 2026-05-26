"""Java availability detection utilities."""

import subprocess

from causaliq_core.java.session import _find_java


def is_java_available() -> bool:
    """Return True if Java is available on this system.

    Safe to call unconditionally; returns False rather than raising
    when Java is absent or fails to run.

    Returns:
        True if Java is found and runs successfully, False otherwise.
    """
    java_exe = _find_java()
    if java_exe is None:
        return False

    try:
        result = subprocess.run(
            [java_exe, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False
