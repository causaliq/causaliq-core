"""Unit tests for causaliq_core.r.bnlearn."""

from unittest.mock import MagicMock

import pytest

from causaliq_core.bn import BN
from causaliq_core.graph import PDAG
from causaliq_core.r.bnlearn import (
    bnlearn_compare,
    bnlearn_cpdag,
    bnlearn_import,
)
from causaliq_core.r.exceptions import RPackageNotAvailableError, RRuntimeError

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


# Test bnlearn_cpdag returns PDAG with mocked bnlearn.
def test_bnlearn_cpdag_returns_pdag_with_mock(monkeypatch):
    mock_bnl = MagicMock()
    mock_bnl.arcs.return_value = []  # empty arcs -> empty CPDAG
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.import_r_package",
        lambda pkg: mock_bnl,
    )
    pdag = PDAG(["A", "B"], [])
    result = bnlearn_cpdag(pdag)
    assert isinstance(result, PDAG)
    assert result.nodes == ["A", "B"]


# Test bnlearn_cpdag calls set_arc for a directed edge in the PDAG.
def test_bnlearn_cpdag_calls_set_arc_for_directed_edge(monkeypatch):
    mock_bnl = MagicMock()
    mock_bnl.arcs.return_value = []
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.import_r_package",
        lambda pkg: mock_bnl,
    )
    pdag = PDAG(["A", "B"], [("A", "->", "B")])
    bnlearn_cpdag(pdag)
    mock_bnl.set_arc.assert_called_once()


# Test bnlearn_cpdag calls set_edge for an undirected edge in the PDAG.
def test_bnlearn_cpdag_calls_set_edge_for_undirected_edge(monkeypatch):
    mock_bnl = MagicMock()
    mock_bnl.arcs.return_value = []
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.import_r_package",
        lambda pkg: mock_bnl,
    )
    pdag = PDAG(["A", "B"], [("A", "-", "B")])
    bnlearn_cpdag(pdag)
    mock_bnl.set_edge.assert_called_once()


# Test bnlearn_cpdag re-raises RPackageNotAvailableError from try block.
def test_bnlearn_cpdag_reraises_package_not_available(monkeypatch):
    def _raise(pkg: str) -> None:
        raise RPackageNotAvailableError("no bnlearn")

    monkeypatch.setattr("causaliq_core.r.bnlearn.import_r_package", _raise)
    with pytest.raises(RPackageNotAvailableError):
        bnlearn_cpdag(PDAG(["A", "B"], []))


# Test bnlearn_cpdag wraps unexpected exceptions as RRuntimeError.
def test_bnlearn_cpdag_wraps_unexpected_exception(monkeypatch):
    mock_bnl = MagicMock()
    mock_bnl.cpdag.side_effect = RuntimeError("R failed")
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.import_r_package",
        lambda pkg: mock_bnl,
    )
    with pytest.raises(RRuntimeError):
        bnlearn_cpdag(PDAG(["A", "B"], []))


# Test bnlearn_cpdag converts arcs result to directed edges.
def test_bnlearn_cpdag_directed_arc_in_result(monkeypatch):
    mock_bnl = MagicMock()
    # Column-major: froms=["A"], tos=["B"] => A -> B
    mock_bnl.arcs.return_value = ["A", "B"]
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.import_r_package",
        lambda pkg: mock_bnl,
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


# Test bnlearn_compare returns dict with expected keys via mock.
def test_bnlearn_compare_returns_dict_with_mock(monkeypatch):
    mock_metrics = MagicMock()
    mock_metrics.rx2.side_effect = lambda k: {
        "tp": [3],
        "fp": [1],
        "fn": [2],
    }[k]
    mock_shd = [4]

    mock_bnl = MagicMock()
    mock_bnl.compare.return_value = mock_metrics
    mock_bnl.shd.return_value = mock_shd

    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.import_r_package",
        lambda pkg: mock_bnl,
    )
    pdag = PDAG(["A", "B"], [])
    ref = PDAG(["A", "B"], [])
    result = bnlearn_compare(pdag, ref)
    assert result == {"tp": 3, "fp": 1, "fn": 2, "shd": 4}


# Test bnlearn_compare re-raises RPackageNotAvailableError from try block.
def test_bnlearn_compare_reraises_package_not_available(monkeypatch):
    def _raise(pkg: str) -> None:
        raise RPackageNotAvailableError("no bnlearn")

    monkeypatch.setattr("causaliq_core.r.bnlearn.import_r_package", _raise)
    with pytest.raises(RPackageNotAvailableError):
        bnlearn_compare(PDAG(["A", "B"], []), PDAG(["A", "B"], []))


# Test bnlearn_compare wraps unexpected exceptions as RRuntimeError.
def test_bnlearn_compare_wraps_unexpected_exception(monkeypatch):
    mock_bnl = MagicMock()
    mock_bnl.compare.side_effect = RuntimeError("R failed")
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.import_r_package",
        lambda pkg: mock_bnl,
    )
    with pytest.raises(RRuntimeError):
        bnlearn_compare(PDAG(["A", "B"], []), PDAG(["A", "B"], []))


# ---------------------------------------------------------------------------
# bnlearn_import
# ---------------------------------------------------------------------------


# Test bnlearn_import raises TypeError for non-string path.
def test_bnlearn_import_raises_typeerror_for_non_string():
    with pytest.raises(TypeError):
        bnlearn_import(123)


# Test bnlearn_import raises FileNotFoundError for missing file.
def test_bnlearn_import_raises_filenotfounderror_for_missing_file():
    with pytest.raises(FileNotFoundError):
        bnlearn_import("/nonexistent/path/test.rda")


# Test bnlearn_import raises ValueError for invalid BN structure.
def test_bnlearn_import_raises_valueerror_for_invalid_bn(
    monkeypatch, tmp_path
):
    rda_file = tmp_path / "test.rda"
    rda_file.touch()

    # Coefficients don't match parents - missing intercept
    class _MockCoeffs:
        names = ["wrong_key"]

        def __iter__(self):
            return iter([0.5])

        def __len__(self):
            return 1

    class _MockParents:
        def __iter__(self):
            return iter([])

        def __len__(self):
            return 0

    class _MockSd:
        def __getitem__(self, i):
            return 0.1

    def node_rx2(key):
        return {
            "parents": _MockParents(),
            "coefficients": _MockCoeffs(),
            "sd": _MockSd(),
        }[key]

    mock_node = MagicMock()
    mock_node.rx2 = MagicMock(side_effect=node_rx2)
    mock_bn = MagicMock()
    mock_bn.names = ["A"]
    mock_bn.rx2 = MagicMock(return_value=mock_node)
    mock_ro = MagicMock()
    mock_ro.globalenv.__getitem__ = MagicMock(return_value=mock_bn)

    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.get_robjects", lambda: mock_ro
    )
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.import_r_package",
        lambda p: MagicMock(),
    )
    with pytest.raises(ValueError):
        bnlearn_import(str(rda_file))


# Test bnlearn_import returns BN for valid mocked rda file.
def test_bnlearn_import_returns_bn_for_valid_rda(monkeypatch, tmp_path):
    rda_file = tmp_path / "test.rda"
    rda_file.touch()

    class _MockCoeffs:
        names = ["(Intercept)"]

        def __iter__(self):
            return iter([2.5])

        def __len__(self):
            return 1

    class _MockParents:
        def __iter__(self):
            return iter([])

        def __len__(self):
            return 0

    class _MockSd:
        def __getitem__(self, i):
            return 0.4

    def node_rx2(key):
        return {
            "parents": _MockParents(),
            "coefficients": _MockCoeffs(),
            "sd": _MockSd(),
        }[key]

    mock_node = MagicMock()
    mock_node.rx2 = MagicMock(side_effect=node_rx2)
    mock_bn = MagicMock()
    mock_bn.names = ["A"]
    mock_bn.rx2 = MagicMock(return_value=mock_node)
    mock_ro = MagicMock()
    mock_ro.globalenv.__getitem__ = MagicMock(return_value=mock_bn)

    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.get_robjects", lambda: mock_ro
    )
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.import_r_package",
        lambda p: MagicMock(),
    )
    result = bnlearn_import(str(rda_file))
    assert isinstance(result, BN)


# Test bnlearn_import wraps unexpected exception as RRuntimeError.
def test_bnlearn_import_wraps_unexpected_exception(monkeypatch, tmp_path):
    rda_file = tmp_path / "test.rda"
    rda_file.touch()
    monkeypatch.setattr(
        "causaliq_core.r.bnlearn.get_robjects",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    with pytest.raises(RRuntimeError):
        bnlearn_import(str(rda_file))
