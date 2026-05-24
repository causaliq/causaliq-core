"""Unit tests for causaliq_core.r.availability."""

from unittest.mock import MagicMock

from causaliq_core.r.availability import (
    is_r_available,
    is_r_package_available,
)
from causaliq_core.r.exceptions import RRuntimeError


# Test is_r_available returns bool in current environment.
def test_is_r_available_returns_bool():
    assert isinstance(is_r_available(), bool)


# Test is_r_available returns False when Rscript not found.
def test_is_r_available_false_when_rscript_not_found(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.availability._find_rscript", lambda: None
    )
    assert is_r_available() is False


# Test is_r_available returns True when Rscript runs successfully.
def test_is_r_available_true_when_rscript_runs(monkeypatch):
    mock_result = MagicMock()
    mock_result.returncode = 0
    monkeypatch.setattr(
        "causaliq_core.r.availability._find_rscript",
        lambda: "/usr/bin/Rscript",
    )
    monkeypatch.setattr(
        "causaliq_core.r.availability.subprocess.run",
        lambda *a, **kw: mock_result,
    )
    assert is_r_available() is True


# Test is_r_available returns False when subprocess raises.
def test_is_r_available_false_when_subprocess_raises(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.availability._find_rscript",
        lambda: "/usr/bin/Rscript",
    )

    def _raise(*a, **kw):
        raise OSError("not found")

    monkeypatch.setattr("causaliq_core.r.availability.subprocess.run", _raise)
    assert is_r_available() is False


# Test is_r_package_available returns False when R not available.
def test_is_r_package_available_false_when_r_unavailable(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.availability.is_r_available",
        lambda: False,
    )
    assert is_r_package_available("bnlearn") is False


# Test is_r_package_available returns True when run_r_script succeeds.
def test_is_r_package_available_true_when_script_succeeds(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.availability.is_r_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "causaliq_core.r.availability.run_r_script",
        lambda s, timeout=15: "",
    )
    assert is_r_package_available("bnlearn") is True


# Test is_r_package_available returns False when run_r_script raises.
def test_is_r_package_available_false_when_script_raises(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.availability.is_r_available",
        lambda: True,
    )

    def _raise(s: str, timeout: int = 15) -> str:
        raise RRuntimeError("not available")

    monkeypatch.setattr("causaliq_core.r.availability.run_r_script", _raise)
    assert is_r_package_available("bnlearn") is False
