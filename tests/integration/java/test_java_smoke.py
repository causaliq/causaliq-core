"""Java integration smoke tests.

These tests require a working Java installation. The Hello World test
requires JDK tools (`javac` and `jar`) to be available.

Tests are auto-skipped when Java is not available
(see tests/conftest.py). Run explicitly with:
`pytest -m java_integration`
"""

import os
import shutil
import subprocess

import pytest

from causaliq_core.java.availability import is_java_available
from causaliq_core.java.session import run_java_jar


def _find_jdk_tool(tool_name: str) -> str:
    """Return path to a JDK tool or empty string when unavailable."""
    path = shutil.which(tool_name)
    if path:
        return path

    java_home = os.environ.get("JAVA_HOME", "")
    if not java_home:
        return ""

    candidates = (
        os.path.join(java_home, "bin", f"{tool_name}.exe"),
        os.path.join(java_home, "bin", tool_name),
    )
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate

    return ""


# Test Java runtime is available in this environment.
@pytest.mark.java_integration
def test_java_is_available():
    assert is_java_available()


# Test run_java_jar executes a minimal Hello World JAR.
@pytest.mark.java_integration
def test_run_java_jar_hello_world(tmp_path):
    javac_exe = _find_jdk_tool("javac")
    jar_exe = _find_jdk_tool("jar")

    if not javac_exe or not jar_exe:
        pytest.skip("JDK tools (javac and jar) are not available")

    java_file = tmp_path / "HelloMain.java"
    java_file.write_text(
        "public class HelloMain { "
        "public static void main(String[] args) { "
        'System.out.println("hello from java"); '
        "} }",
        encoding="utf-8",
    )

    subprocess.run(
        [javac_exe, str(java_file)],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
        text=True,
    )

    jar_path = tmp_path / "hello.jar"
    subprocess.run(
        [
            jar_exe,
            "--create",
            "--file",
            str(jar_path),
            "--main-class",
            "HelloMain",
            "HelloMain.class",
        ],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
        text=True,
    )

    output = run_java_jar(str(jar_path))
    assert output.strip() == "hello from java"
