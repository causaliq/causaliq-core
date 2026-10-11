"""Java runtime management via subprocess."""

import os
import shutil
import subprocess
from typing import List, Optional

from causaliq_core.java.exceptions import (
    JavaNotAvailableError,
    JavaRuntimeError,
)


def _find_java() -> Optional[str]:
    """Return path to Java executable, or None if not found.

    Searches PATH first, then falls back to the JAVA_HOME environment
    variable to locate the executable on Windows and Unix-like systems.

    Returns:
        Absolute path to Java executable, or None if not found.
    """
    path = shutil.which("java")
    if path:
        return path

    java_home = os.environ.get("JAVA_HOME", "")
    if java_home:
        candidates = (
            os.path.join(java_home, "bin", "java.exe"),
            os.path.join(java_home, "bin", "java"),
        )
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate

    return None


def _validate_java_args(jar_path: str, args: Optional[List[str]]) -> List[str]:
    """Validate Java invocation arguments and normalise the argument list.

    Args:
        jar_path: Path to the JAR to execute.
        args: Optional list of CLI arguments, or None.

    Returns:
        The argument list to pass after the JAR path.

    Raises:
        TypeError: If argument types are invalid.
        ValueError: If jar_path is empty.
        FileNotFoundError: If jar_path does not exist.
    """
    if not isinstance(jar_path, str):
        raise TypeError(
            "'jar_path' must be a string; " f"got {type(jar_path).__name__}."
        )
    if not jar_path:
        raise ValueError("'jar_path' must not be an empty string.")
    if not os.path.isfile(jar_path):
        raise FileNotFoundError(f"JAR file not found: {jar_path}")

    if args is None:
        args = []
    if not isinstance(args, list) or not all(
        isinstance(item, str) for item in args
    ):
        raise TypeError("'args' must be a list of strings.")
    return args


def _run_java_command(command: List[str], timeout: int) -> str:
    """Run a Java command and return its standard output.

    Args:
        command: Full command line including the Java executable.
        timeout: Seconds to wait before raising TimeoutExpired.

    Returns:
        Standard output produced by the Java command.

    Raises:
        JavaRuntimeError: If Java exits with a non-zero status.
    """
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise JavaRuntimeError(stderr or "Java command failed.")
    return result.stdout


def run_java_jar(
    jar_path: str,
    args: Optional[List[str]] = None,
    timeout: int = 120,
) -> str:
    """Run a Java JAR and return stdout.

    Args:
        jar_path: Absolute or relative path to executable JAR.
        args: Optional list of CLI arguments passed after the JAR path.
        timeout: Seconds to wait before raising TimeoutExpired.

    Raises:
        TypeError: If arguments have invalid types.
        ValueError: If jar_path is empty.
        FileNotFoundError: If jar_path does not exist.
        JavaNotAvailableError: If Java executable cannot be found.
        JavaRuntimeError: If Java command exits with non-zero status.

    Returns:
        Standard output produced by the Java command.
    """
    args = _validate_java_args(jar_path, args)

    java_exe = _find_java()
    if java_exe is None:
        raise JavaNotAvailableError(
            "Java executable not found. Install Java or set JAVA_HOME."
        )

    command = [java_exe, "-jar", jar_path] + args
    return _run_java_command(command, timeout)
