"""Unit tests for causaliq_core.r.convert."""

from unittest.mock import MagicMock

import numpy as np

from causaliq_core.r.convert import data_to_r_dataframe, r_arcs_to_edges


# Test r_arcs_to_edges returns empty list for empty input.
def test_r_arcs_to_edges_empty_input_returns_empty():
    assert r_arcs_to_edges([]) == []


# Test r_arcs_to_edges returns single directed arc correctly.
def test_r_arcs_to_edges_single_directed_arc():
    # Column-major: [from_A, to_B] => A -> B
    result = r_arcs_to_edges(["A", "B"])
    assert result == [("A", "->", "B")]


# Test r_arcs_to_edges handles two directed arcs.
def test_r_arcs_to_edges_two_directed_arcs():
    # A->B and A->C: froms=[A, A], tos=[B, C]
    result = r_arcs_to_edges(["A", "A", "B", "C"])
    assert set(result) == {("A", "->", "B"), ("A", "->", "C")}


# Test r_arcs_to_edges collapses opposing arcs to undirected edge.
def test_r_arcs_to_edges_undirected_edge():
    # Both A->B and B->A = undirected; froms=[A, B], tos=[B, A]
    result = r_arcs_to_edges(["A", "B", "B", "A"])
    assert len(result) == 1
    tail, etype, head = result[0]
    assert etype == "-"
    assert {tail, head} == {"A", "B"}


# Test r_arcs_to_edges selects alphabetically earlier node as tail.
def test_r_arcs_to_edges_undirected_tail_is_alphabetically_first():
    result = r_arcs_to_edges(["B", "A", "A", "B"])
    tail, _, head = result[0]
    assert tail == "A"
    assert head == "B"


# Test r_arcs_to_edges mixes directed and undirected correctly.
def test_r_arcs_to_edges_mixed_directed_and_undirected():
    # A->C directed; A-B undirected (A->B and B->A)
    # froms=[A, A, B], tos=[C, B, A]
    result = r_arcs_to_edges(["A", "A", "B", "C", "B", "A"])
    result_set = set(result)
    assert ("A", "->", "C") in result_set
    assert any(e[1] == "-" and {e[0], e[2]} == {"A", "B"} for e in result)
    assert len(result) == 2


# Test data_to_r_dataframe creates FloatVector for continuous column.
def test_data_to_r_dataframe_continuous_uses_float_vector(monkeypatch):
    mock_ro = MagicMock()
    monkeypatch.setattr(
        "causaliq_core.r.convert.get_robjects", lambda: mock_ro
    )
    sample = np.array([[1.0, 2.0], [3.0, 4.0]])
    data_to_r_dataframe(sample, ["A", "B"], {"A": "CONTINUOUS"})
    assert mock_ro.FloatVector.call_count == 2


# Test data_to_r_dataframe creates FactorVector for discrete column.
def test_data_to_r_dataframe_discrete_uses_factor_vector(monkeypatch):
    mock_ro = MagicMock()
    monkeypatch.setattr(
        "causaliq_core.r.convert.get_robjects", lambda: mock_ro
    )
    sample = np.array([[0.0, 1.0], [1.0, 0.0]])
    data_to_r_dataframe(
        sample,
        ["A", "B"],
        {"A": "DISCRETE", "B": "DISCRETE"},
    )
    assert mock_ro.FactorVector.call_count == 2
    assert mock_ro.FloatVector.call_count == 0


# Test data_to_r_dataframe treats unknown type as continuous.
def test_data_to_r_dataframe_unknown_type_treated_as_continuous(monkeypatch):
    mock_ro = MagicMock()
    monkeypatch.setattr(
        "causaliq_core.r.convert.get_robjects", lambda: mock_ro
    )
    sample = np.array([[1.0], [2.0]])
    data_to_r_dataframe(sample, ["X"], {})
    mock_ro.FloatVector.assert_called_once()


# Test data_to_r_dataframe calls DataFrame with all columns.
def test_data_to_r_dataframe_calls_dataframe(monkeypatch):
    mock_ro = MagicMock()
    monkeypatch.setattr(
        "causaliq_core.r.convert.get_robjects", lambda: mock_ro
    )
    sample = np.array([[1.0, 2.0]])
    data_to_r_dataframe(sample, ["A", "B"], {})
    mock_ro.DataFrame.assert_called_once()
    call_kwargs = mock_ro.DataFrame.call_args[0][0]
    assert set(call_kwargs.keys()) == {"A", "B"}
