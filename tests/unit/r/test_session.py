"""Unit tests for causaliq_core.r.session."""

import sys
from unittest.mock import MagicMock

import pytest

from causaliq_core.r.exceptions import (
    RNotAvailableError,
    RPackageNotAvailableError,
)
from causaliq_core.r.session import get_robjects, import_r_package


# Test get_robjects raises RNotAvailableError when R is not available.
def test_get_robjects_raises_when_r_not_available(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.session.is_r_available", lambda: False
    )
    with pytest.raises(RNotAvailableError):
        get_robjects()


# Test get_robjects returns robjects module when R is available.
def test_get_robjects_returns_module_when_r_available(monkeypatch):
    monkeypatch.setattr("causaliq_core.r.session.is_r_available", lambda: True)
    mock_ro = MagicMock()
    monkeypatch.setitem(sys.modules, "rpy2.robjects", mock_ro)
    result = get_robjects()
    assert result is mock_ro


# Test import_r_package raises RNotAvailableError when R not available.
def test_import_r_package_raises_when_r_not_available(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.session.is_r_available", lambda: False
    )
    with pytest.raises(RNotAvailableError):
        import_r_package("bnlearn")


# Test import_r_package raises RPackageNotAvailableError when missing.
def test_import_r_package_raises_when_package_not_available(monkeypatch):
    monkeypatch.setattr("causaliq_core.r.session.is_r_available", lambda: True)
    monkeypatch.setattr(
        "causaliq_core.r.session.is_r_package_available",
        lambda p: False,
    )
    with pytest.raises(RPackageNotAvailableError):
        import_r_package("bnlearn")


# Test import_r_package returns package object when available.
def test_import_r_package_returns_package_when_available(monkeypatch):
    monkeypatch.setattr("causaliq_core.r.session.is_r_available", lambda: True)
    monkeypatch.setattr(
        "causaliq_core.r.session.is_r_package_available",
        lambda p: True,
    )
    mock_pkg = MagicMock()
    mock_packages = MagicMock()
    mock_packages.importr.return_value = mock_pkg
    monkeypatch.setitem(sys.modules, "rpy2.robjects.packages", mock_packages)
    result = import_r_package("bnlearn")
    assert result is mock_pkg
