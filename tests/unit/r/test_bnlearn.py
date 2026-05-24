"""Unit tests for causaliq_core.r.bnlearn."""

import pytest

from causaliq_core.bn import BN
from causaliq_core.graph import PDAG
from causaliq_core.r.bnlearn import (
    bnlearn_compare,
    bnlearn_cpdag,
    bnlearn_import,
)
from causaliq_core.r.exceptions import RNotAvailableError, RRuntimeError

# ---------------------------------------------------------------------------
# bnlearn_cpdag
# ---------------------------------------------------------------------------


# Test bnlearn_cpdag raises TypeError for non-PDAG input.
def test_bnlearn_cpdag_raises_typeerror_for_non_pdag():
    with pytest.raises(TypeError):
        bnlearn_cpdag("not a pdag")


# Test bnlearn_cpdag raises ValueError for empty PDAG.
def test_bnlearn_cpdag_raises_valueerror_for_empty_pdag():
    with pytest.raises(ValueError):
        bnlearn_cpdag(PDAG([], []))


# Test bnlearn_cpdag returns PDAG with mocked run_r_script.
def test_bnlearn_cpdag_returns_pdag_with_mock(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.run_r_script",
        lambda s, **kw: "",
    )
    pdag = PDAG(["A", "B"], [])
    result = bnlearn_cpdag(pdag)
    assert isinstance(result, PDAG)
    assert result.nodes == ["A", "B"]


# Test bnlearn_cpdag generates set.arc for a directed edge.
def test_bnlearn_cpdag_generates_set_arc_for_directed_edge(monkeypatch):
    captured = []

    def _capture(s: str, **kw: object) -> str:
        captured.append(s)
        return ""

    monkeypatch.setattr("causaliq_core.r.bnlearn.run_r_script", _capture)
    pdag = PDAG(["A", "B"], [("A", "->", "B")])
    bnlearn_cpdag(pdag)
    assert "set.arc" in captured[0]


# Test bnlearn_cpdag generates set.edge for an undirected edge.
def test_bnlearn_cpdag_generates_set_edge_for_undirected_edge(monkeypatch):
    captured = []

    def _capture(s: str, **kw: object) -> str:
        captured.append(s)
        return ""

    monkeypatch.setattr("causaliq_core.r.bnlearn.run_r_script", _capture)
    pdag = PDAG(["A", "B"], [("A", "-", "B")])
    bnlearn_cpdag(pdag)
    assert "set.edge" in captured[0]


# Test bnlearn_cpdag re-raises RRuntimeError from run_r_script.
def test_bnlearn_cpdag_reraises_rruntimeerror(monkeypatch):
    def _raise(s: str, **kw: object) -> str:
        raise RRuntimeError("bnlearn error")

    monkeypatch.setattr("causaliq_core.r.bnlearn.run_r_script", _raise)
    with pytest.raises(RRuntimeError):
        bnlearn_cpdag(PDAG(["A", "B"], []))


# Test bnlearn_cpdag re-raises RNotAvailableError from run_r_script.
def test_bnlearn_cpdag_reraises_rnotavailableerror(monkeypatch):
    def _raise(s: str, **kw: object) -> str:
        raise RNotAvailableError("no Rscript")

    monkeypatch.setattr("causaliq_core.r.bnlearn.run_r_script", _raise)
    with pytest.raises(RNotAvailableError):
        bnlearn_cpdag(PDAG(["A", "B"], []))


# Test bnlearn_cpdag wraps unexpected exceptions as RRuntimeError.
def test_bnlearn_cpdag_wraps_unexpected_exception(monkeypatch):
    def _raise(s: str, **kw: object) -> str:
        raise RuntimeError("R failed")

    monkeypatch.setattr("causaliq_core.r.bnlearn.run_r_script", _raise)
    with pytest.raises(RRuntimeError):
        bnlearn_cpdag(PDAG(["A", "B"], []))


# Test bnlearn_cpdag parses tab-separated arc output as directed edge.
def test_bnlearn_cpdag_directed_arc_in_result(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.run_r_script",
        lambda s, **kw: "A\tB\n",
    )
    pdag = PDAG(["A", "B"], [])
    result = bnlearn_cpdag(pdag)
    edges = list(result.edges.items())
    assert len(edges) == 1
    assert edges[0][0] == ("A", "B")


# ---------------------------------------------------------------------------
# bnlearn_compare
# ---------------------------------------------------------------------------


# Test bnlearn_compare raises TypeError for non-PDAG first arg.
def test_bnlearn_compare_raises_typeerror_for_non_pdag_first():
    ref = PDAG(["A", "B"], [])
    with pytest.raises(TypeError):
        bnlearn_compare("bad", ref)


# Test bnlearn_compare raises TypeError for non-PDAG second arg.
def test_bnlearn_compare_raises_typeerror_for_non_pdag_second():
    pdag = PDAG(["A", "B"], [])
    with pytest.raises(TypeError):
        bnlearn_compare(pdag, "bad")


# Test bnlearn_compare raises ValueError for empty PDAG.
def test_bnlearn_compare_raises_valueerror_for_empty_pdag():
    with pytest.raises(ValueError):
        bnlearn_compare(PDAG([], []), PDAG([], []))


# Test bnlearn_compare raises ValueError for mismatched node sets.
def test_bnlearn_compare_raises_valueerror_for_mismatched_nodes():
    with pytest.raises(ValueError):
        bnlearn_compare(
            PDAG(["A", "B"], []),
            PDAG(["A", "C"], []),
        )


# Test bnlearn_compare parses newline-delimited output correctly.
def test_bnlearn_compare_returns_dict_with_mock(monkeypatch):
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.run_r_script",
        lambda s, **kw: "3\n1\n2\n4\n",
    )
    pdag = PDAG(["A", "B"], [])
    ref = PDAG(["A", "B"], [])
    result = bnlearn_compare(pdag, ref)
    assert result == {"tp": 3, "fp": 1, "fn": 2, "shd": 4}


# Test bnlearn_compare re-raises RRuntimeError from run_r_script.
def test_bnlearn_compare_reraises_rruntimeerror(monkeypatch):
    def _raise(s: str, **kw: object) -> str:
        raise RRuntimeError("R error")

    monkeypatch.setattr("causaliq_core.r.bnlearn.run_r_script", _raise)
    with pytest.raises(RRuntimeError):
        bnlearn_compare(PDAG(["A", "B"], []), PDAG(["A", "B"], []))


# Test bnlearn_compare wraps unexpected exceptions as RRuntimeError.
def test_bnlearn_compare_wraps_unexpected_exception(monkeypatch):
    def _raise(s: str, **kw: object) -> str:
        raise RuntimeError("R failed")

    monkeypatch.setattr("causaliq_core.r.bnlearn.run_r_script", _raise)
    with pytest.raises(RRuntimeError):
        bnlearn_compare(PDAG(["A", "B"], []), PDAG(["A", "B"], []))


# ---------------------------------------------------------------------------
# bnlearn_import
# ---------------------------------------------------------------------------


# Test bnlearn_import raises TypeError for non-string path.
def test_bnlearn_import_raises_typeerror_for_non_string():
    with pytest.raises(TypeError):
        bnlearn_import(123)  # type: ignore[arg-type]


# Test bnlearn_import raises FileNotFoundError for missing file.
def test_bnlearn_import_raises_filenotfounderror_for_missing_file():
    with pytest.raises(FileNotFoundError):
        bnlearn_import("/nonexistent/path/test.rda")


# Test bnlearn_import raises ValueError for missing (Intercept) coef.
def test_bnlearn_import_raises_valueerror_for_invalid_bn(
    monkeypatch, tmp_path
):
    rda_file = tmp_path / "test.rda"
    rda_file.touch()

    def _fake(s: str, **kw: object) -> str:
        return "NODE\tA\nPARENTS\t\n" "COEF\twrong_key\t0.5\nSD\t0.1\n"

    monkeypatch.setattr("causaliq_core.r.bnlearn.run_r_script", _fake)
    with pytest.raises(ValueError):
        bnlearn_import(str(rda_file))


# Test bnlearn_import returns BN for valid mocked rda file.
def test_bnlearn_import_returns_bn_for_valid_rda(monkeypatch, tmp_path):
    rda_file = tmp_path / "test.rda"
    rda_file.touch()

    def _fake(s: str, **kw: object) -> str:
        return "NODE\tA\nPARENTS\t\n" "COEF\t(Intercept)\t2.5\nSD\t0.4\n"

    monkeypatch.setattr("causaliq_core.r.bnlearn.run_r_script", _fake)
    result = bnlearn_import(str(rda_file))
    assert isinstance(result, BN)


# Test bnlearn_import wraps unexpected exception as RRuntimeError.
def test_bnlearn_import_wraps_unexpected_exception(monkeypatch, tmp_path):
    rda_file = tmp_path / "test.rda"
    rda_file.touch()

    def _raise(s: str, **kw: object) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr("causaliq_core.r.bnlearn.run_r_script", _raise)
    with pytest.raises(RRuntimeError):
        bnlearn_import(str(rda_file))


# Test bnlearn_import re-raises RRuntimeError from run_r_script.
def test_bnlearn_import_reraises_rruntimeerror(monkeypatch, tmp_path):
    rda_file = tmp_path / "test.rda"
    rda_file.touch()

    def _raise(s: str, **kw: object) -> str:
        raise RRuntimeError("R error")

    monkeypatch.setattr("causaliq_core.r.bnlearn.run_r_script", _raise)
    with pytest.raises(RRuntimeError):
        bnlearn_import(str(rda_file))


# Test bnlearn_import handles BN node with non-empty parents list.
def test_bnlearn_import_handles_parent_nodes(monkeypatch, tmp_path):
    rda_file = tmp_path / "test.rda"
    rda_file.touch()
    output = (
        "NODE\tA\nPARENTS\t\nCOEF\t(Intercept)\t1.0\nSD\t0.5\n"
        "NODE\tB\nPARENTS\tA\n"
        "COEF\t(Intercept)\t0.0\nCOEF\tA\t0.8\nSD\t0.3\n"
    )
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.run_r_script",
        lambda s, **kw: output,
    )
    result = bnlearn_import(str(rda_file))
    assert isinstance(result, BN)


# Test bnlearn_import skips empty lines in R output.
def test_bnlearn_import_skips_empty_lines_in_output(monkeypatch, tmp_path):
    rda_file = tmp_path / "test.rda"
    rda_file.touch()
    output = "NODE\tA\nPARENTS\t\n\n" "COEF\t(Intercept)\t2.5\nSD\t0.4\n"
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.run_r_script",
        lambda s, **kw: output,
    )
    result = bnlearn_import(str(rda_file))
    assert isinstance(result, BN)
