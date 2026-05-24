"""Unit tests for causaliq_core.r.session."""

from unittest.mock import MagicMock

import pytest

from causaliq_core.r.exceptions import RNotAvailableError, RRuntimeError
from causaliq_core.r.session import _find_rscript, run_r_script


# Test _find_rscript returns path when Rscript is on PATH.
def test_find_rscript_returns_path_when_on_path(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.session.shutil.which",
        lambda _: "/usr/bin/Rscript",
    )
    assert _find_rscript() == "/usr/bin/Rscript"


# Test _find_rscript returns None when not found anywhere.
def test_find_rscript_returns_none_when_not_found(monkeypatch):
    monkeypatch.setattr("causaliq_core.r.session.shutil.which", lambda _: None)
    monkeypatch.setattr(
        "causaliq_core.r.session.os.environ",
        {},
    )
    assert _find_rscript() is None


# Test run_r_script raises RNotAvailableError when Rscript not found.
def test_run_r_script_raises_when_rscript_not_found(monkeypatch):
    monkeypatch.setattr("causaliq_core.r.session._find_rscript", lambda: None)
    with pytest.raises(RNotAvailableError):
        run_r_script("cat('hello')")


# Test run_r_script returns stdout on successful execution.
def test_run_r_script_returns_stdout(monkeypatch):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "hello\n"
    monkeypatch.setattr(
        "causaliq_core.r.session._find_rscript",
        lambda: "/usr/bin/Rscript",
    )
    monkeypatch.setattr(
        "causaliq_core.r.session.subprocess.run",
        lambda *a, **kw: mock_result,
    )
    assert run_r_script("cat('hello')") == "hello\n"


# Test run_r_script raises RRuntimeError on non-zero exit code.
def test_run_r_script_raises_on_nonzero_exit(monkeypatch):
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Error: something went wrong"
    monkeypatch.setattr(
        "causaliq_core.r.session._find_rscript",
        lambda: "/usr/bin/Rscript",
    )
    monkeypatch.setattr(
        "causaliq_core.r.session.subprocess.run",
        lambda *a, **kw: mock_result,
    )
    with pytest.raises(RRuntimeError):
        run_r_script("stop('error')")


# Test _find_rscript returns path via R_HOME when not on PATH.
def test_find_rscript_returns_path_from_r_home(monkeypatch):
    monkeypatch.setattr("causaliq_core.r.session.shutil.which", lambda _: None)
    monkeypatch.setattr(
        "causaliq_core.r.session.os.environ",
        {"R_HOME": "/fake/R"},
    )
    monkeypatch.setattr(
        "causaliq_core.r.session.os.path.isfile", lambda _: True
    )
    result = _find_rscript()
    assert result is not None
    assert "Rscript" in result
