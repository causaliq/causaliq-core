"""Unit tests for causaliq_core.r.availability."""

import sys
from unittest.mock import MagicMock

from causaliq_core.r.availability import (
    is_r_available,
    is_r_package_available,
)


# Test is_r_available returns bool in current environment.
def test_is_r_available_returns_bool():
    assert isinstance(is_r_available(), bool)


# Test is_r_available returns True when rpy2.robjects is in sys.modules.
def test_is_r_available_returns_true_when_rpy2_present(monkeypatch):
    monkeypatch.setitem(sys.modules, "rpy2", MagicMock())
    monkeypatch.setitem(sys.modules, "rpy2.robjects", MagicMock())
    assert is_r_available() is True


# Test is_r_available returns False when rpy2.robjects blocked.
def test_is_r_available_returns_false_when_rpy2_blocked(monkeypatch):
    monkeypatch.setitem(sys.modules, "rpy2.robjects", None)
    assert is_r_available() is False


# Test is_r_package_available returns False when R not available.
def test_is_r_package_available_false_when_r_unavailable(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.availability.is_r_available",
        lambda: False,
    )
    assert is_r_package_available("bnlearn") is False


# Test is_r_package_available returns False when importr raises.
def test_is_r_package_available_false_when_importr_raises(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.availability.is_r_available",
        lambda: True,
    )
    mock_packages = MagicMock()
    mock_packages.importr.side_effect = Exception("not installed")
    monkeypatch.setitem(sys.modules, "rpy2.robjects.packages", mock_packages)
    assert is_r_package_available("bnlearn") is False


# Test is_r_package_available returns True when importr succeeds.
def test_is_r_package_available_true_when_importr_succeeds(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.availability.is_r_available",
        lambda: True,
    )
    mock_packages = MagicMock()
    monkeypatch.setitem(sys.modules, "rpy2.robjects.packages", mock_packages)
    assert is_r_package_available("bnlearn") is True
