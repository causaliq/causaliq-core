"""Unit tests for causaliq_core.java.availability."""

from unittest.mock import MagicMock

from causaliq_core.java.availability import is_java_available


# Test is_java_available returns bool in current environment.
def test_is_java_available_returns_bool():
    assert isinstance(is_java_available(), bool)


# Test is_java_available returns False when java not found.
def test_is_java_available_false_when_java_not_found(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.java.availability._find_java",
        lambda: None,
    )
    assert is_java_available() is False


# Test is_java_available returns True when java runs successfully.
def test_is_java_available_true_when_java_runs(monkeypatch):
    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(
        "causaliq_core.java.availability._find_java",
        lambda: "/usr/bin/java",
    )
    monkeypatch.setattr(
        "causaliq_core.java.availability.subprocess.run",
        lambda *a, **kw: mock_result,
    )
    assert is_java_available() is True


# Test is_java_available returns False when subprocess raises.
def test_is_java_available_false_when_subprocess_raises(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.java.availability._find_java",
        lambda: "/usr/bin/java",
    )

    def _raise(*a, **kw):
        raise OSError("not found")

    monkeypatch.setattr(
        "causaliq_core.java.availability.subprocess.run",
        _raise,
    )
    assert is_java_available() is False
