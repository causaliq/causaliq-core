"""Unit tests for causaliq_core.java.session."""

from unittest.mock import MagicMock

import pytest

from causaliq_core.java.exceptions import (
    JavaNotAvailableError,
    JavaRuntimeError,
)
from causaliq_core.java.session import _find_java, run_java_jar


# Test _find_java returns path when java is on PATH.
def test_find_java_returns_path_when_on_path(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.java.session.shutil.which",
        lambda _: "/usr/bin/java",
    )
    assert _find_java() == "/usr/bin/java"


# Test _find_java returns None when not found anywhere.
def test_find_java_returns_none_when_not_found(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.java.session.shutil.which",
        lambda _: None,
    )
    monkeypatch.setattr("causaliq_core.java.session.os.environ", {})
    assert _find_java() is None


# Test _find_java returns path via JAVA_HOME when not on PATH.
def test_find_java_returns_path_from_java_home(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.java.session.shutil.which",
        lambda _: None,
    )
    monkeypatch.setattr(
        "causaliq_core.java.session.os.environ",
        {"JAVA_HOME": "/fake/java"},
    )
    monkeypatch.setattr(
        "causaliq_core.java.session.os.path.isfile",
        lambda _: True,
    )
    result = _find_java()
    assert result is not None
    assert "java" in result.lower()


# Test run_java_jar raises TypeError when jar_path type is invalid.
def test_run_java_jar_raises_type_error_for_bad_jar_path_type():
    with pytest.raises(TypeError):
        run_java_jar(123)  # type: ignore[arg-type]


# Test run_java_jar raises ValueError when jar_path is empty.
def test_run_java_jar_raises_value_error_for_empty_jar_path():
    with pytest.raises(ValueError):
        run_java_jar("")


# Test run_java_jar raises FileNotFoundError for missing jar.
def test_run_java_jar_raises_for_missing_jar():
    with pytest.raises(FileNotFoundError):
        run_java_jar("/missing/tool.jar")


# Test run_java_jar raises TypeError for invalid args structure.
def test_run_java_jar_raises_type_error_for_bad_args(tmp_path):
    jar_path = tmp_path / "tool.jar"
    jar_path.write_text("dummy", encoding="utf-8")
    with pytest.raises(TypeError):
        run_java_jar(str(jar_path), args=["ok", 1])  # type: ignore[list-item]


# Test run_java_jar raises JavaNotAvailableError when java not found.
def test_run_java_jar_raises_when_java_not_found(monkeypatch, tmp_path):
    jar_path = tmp_path / "tool.jar"
    jar_path.write_text("dummy", encoding="utf-8")
    monkeypatch.setattr("causaliq_core.java.session._find_java", lambda: None)
    with pytest.raises(JavaNotAvailableError):
        run_java_jar(str(jar_path))


# Test run_java_jar returns stdout on successful execution.
def test_run_java_jar_returns_stdout(monkeypatch, tmp_path):
    jar_path = tmp_path / "tool.jar"
    jar_path.write_text("dummy", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "ok\n"

    monkeypatch.setattr(
        "causaliq_core.java.session._find_java",
        lambda: "/usr/bin/java",
    )
    monkeypatch.setattr(
        "causaliq_core.java.session.subprocess.run",
        lambda *a, **kw: mock_result,
    )

    assert run_java_jar(str(jar_path), args=["--help"]) == "ok\n"


# Test run_java_jar raises JavaRuntimeError on non-zero exit code.
def test_run_java_jar_raises_on_nonzero_exit(monkeypatch, tmp_path):
    jar_path = tmp_path / "tool.jar"
    jar_path.write_text("dummy", encoding="utf-8")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "boom"

    monkeypatch.setattr(
        "causaliq_core.java.session._find_java",
        lambda: "/usr/bin/java",
    )
    monkeypatch.setattr(
        "causaliq_core.java.session.subprocess.run",
        lambda *a, **kw: mock_result,
    )

    with pytest.raises(JavaRuntimeError):
        run_java_jar(str(jar_path), args=["--run"])
