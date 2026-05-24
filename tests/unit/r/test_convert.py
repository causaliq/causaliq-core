"""Unit tests for causaliq_core.r.convert."""

import numpy as np

from causaliq_core.r.convert import data_to_r_dataframe, r_arcs_to_edges


# Test r_arcs_to_edges returns empty list for empty input.
def test_r_arcs_to_edges_empty_input_returns_empty():
    assert r_arcs_to_edges([]) == []


# Test r_arcs_to_edges returns single directed arc correctly.
def test_r_arcs_to_edges_single_directed_arc():
    result = r_arcs_to_edges([("A", "B")])
    assert result == [("A", "->", "B")]


# Test r_arcs_to_edges handles two directed arcs.
def test_r_arcs_to_edges_two_directed_arcs():
    result = r_arcs_to_edges([("A", "B"), ("A", "C")])
    assert set(result) == {("A", "->", "B"), ("A", "->", "C")}


# Test r_arcs_to_edges collapses opposing arcs to undirected edge.
def test_r_arcs_to_edges_undirected_edge():
    result = r_arcs_to_edges([("A", "B"), ("B", "A")])
    assert len(result) == 1
    tail, etype, head = result[0]
    assert etype == "-"
    assert {tail, head} == {"A", "B"}


# Test r_arcs_to_edges selects alphabetically earlier node as tail.
def test_r_arcs_to_edges_undirected_tail_is_alphabetically_first():
    result = r_arcs_to_edges([("B", "A"), ("A", "B")])
    tail, _, head = result[0]
    assert tail == "A"
    assert head == "B"


# Test r_arcs_to_edges mixes directed and undirected correctly.
def test_r_arcs_to_edges_mixed_directed_and_undirected():
    result = r_arcs_to_edges([("A", "C"), ("A", "B"), ("B", "A")])
    assert ("A", "->", "C") in set(result)
    assert any(e[1] == "-" and {e[0], e[2]} == {"A", "B"} for e in result)
    assert len(result) == 2


# Test data_to_r_dataframe returns str type.
def test_data_to_r_dataframe_returns_string():
    sample = np.array([[1.0, 2.0], [3.0, 4.0]])
    result = data_to_r_dataframe(sample, ["A", "B"], {"A": "CONTINUOUS"})
    assert isinstance(result, str)


# Test data_to_r_dataframe contains data.frame call.
def test_data_to_r_dataframe_contains_data_frame():
    sample = np.array([[1.0], [2.0]])
    result = data_to_r_dataframe(sample, ["X"], {})
    assert "data.frame" in result


# Test data_to_r_dataframe uses c() for continuous columns.
def test_data_to_r_dataframe_continuous_uses_c_constructor():
    sample = np.array([[1.0, 2.0], [3.0, 4.0]])
    result = data_to_r_dataframe(sample, ["A", "B"], {"A": "CONTINUOUS"})
    assert "as.factor" not in result
    assert result.count("c(") == 2


# Test data_to_r_dataframe uses as.factor for discrete columns.
def test_data_to_r_dataframe_discrete_uses_as_factor():
    sample = np.array([[0.0, 1.0], [1.0, 0.0]])
    result = data_to_r_dataframe(
        sample,
        ["A", "B"],
        {"A": "DISCRETE", "B": "DISCRETE"},
    )
    assert result.count("as.factor") == 2


# Test data_to_r_dataframe treats unknown type as continuous.
def test_data_to_r_dataframe_unknown_type_treated_as_continuous():
    sample = np.array([[1.0], [2.0]])
    result = data_to_r_dataframe(sample, ["X"], {})
    assert "as.factor" not in result
    assert "c(" in result


# Test data_to_r_dataframe assigns to the given varname.
def test_data_to_r_dataframe_assigns_to_varname():
    sample = np.array([[1.0], [2.0]])
    result = data_to_r_dataframe(sample, ["X"], {}, varname="my_data")
    assert result.startswith("my_data <- data.frame(")
