"""
Unit tests for the causaliq_core.graph module.

Tests cover:
- EdgeMark and EdgeType enums
- BAYESYS_VERSIONS constant
- adjmat() function for adjacency matrix creation
"""

import pandas as pd
import pytest

from causaliq_core.graph import EdgeMark, EdgeType, adjmat


# Test that EdgeMark members have correct values
def test_edge_mark_values():
    assert EdgeMark.NONE.value == 0
    assert EdgeMark.LINE.value == 1
    assert EdgeMark.ARROW.value == 2
    assert EdgeMark.CIRCLE.value == 3


# Test that EdgeType members have correct tuple values and refs to EdgeMark
def test_edge_type_values():
    assert EdgeType.NONE.value == (0, EdgeMark.NONE, EdgeMark.NONE, "")
    assert EdgeType.DIRECTED.value == (
        1,
        EdgeMark.LINE,
        EdgeMark.ARROW,
        "->",
    )
    assert EdgeType.UNDIRECTED.value == (
        2,
        EdgeMark.LINE,
        EdgeMark.LINE,
        "-",
    )
    assert EdgeType.BIDIRECTED.value == (
        3,
        EdgeMark.ARROW,
        EdgeMark.ARROW,
        "<->",
    )
    assert EdgeType.SEMIDIRECTED.value == (
        4,
        EdgeMark.CIRCLE,
        EdgeMark.ARROW,
        "o->",
    )
    assert EdgeType.NONDIRECTED.value == (
        5,
        EdgeMark.CIRCLE,
        EdgeMark.CIRCLE,
        "o-o",
    )
    assert EdgeType.SEMIUNDIRECTED.value == (
        6,
        EdgeMark.CIRCLE,
        EdgeMark.LINE,
        "o-",
    )


# Test all EdgeType tuples use EdgeMark enum for their 2nd and 3rd elements
def test_edge_type_edge_mark_references():
    for edge_type in EdgeType:
        _, mark1, mark2, _ = edge_type.value
        assert isinstance(mark1, EdgeMark)
        assert isinstance(mark2, EdgeMark)


# Test adjmat function with valid input
def test_adjmat_valid():
    columns = {
        "A": [0, 0, 0],  # A has no outgoing edges
        "B": [1, 0, 0],  # B has edge to A
        "C": [0, 1, 0],  # C has edge to B
    }
    result = adjmat(columns)

    # Check it's a DataFrame
    assert isinstance(result, pd.DataFrame)

    # Check dimensions
    assert result.shape == (3, 3)

    # Check index and columns
    assert list(result.index) == ["A", "B", "C"]
    assert list(result.columns) == ["A", "B", "C"]

    # Check values (result[row][col] means edge from col to row)
    assert result.loc["A", "A"] == 0  # No A→A edge
    assert result.loc["A", "B"] == 1  # B→A edge exists
    assert result.loc["B", "C"] == 1  # C→B edge exists


def test_adjmat_type_errors():
    # Test with non-dict
    with pytest.raises(TypeError, match="adjmat called with bad arg type"):
        adjmat([1, 2, 3])

    # Test with dict but non-list values
    with pytest.raises(TypeError, match="adjmat called with bad arg type"):
        adjmat({"A": "not_a_list"})

    # Test with dict of lists but non-int values
    with pytest.raises(TypeError, match="adjmat called with bad arg type"):
        adjmat({"A": ["not_an_int"]})


def test_adjmat_value_errors():
    # Test with wrong column length
    with pytest.raises(
        ValueError, match="some columns wrong length for adjmat"
    ):
        adjmat({"A": [0, 1], "B": [0, 1, 2]})  # Mismatched lengths

    # Test with invalid edge type values (correct column lengths)
    with pytest.raises(ValueError, match="invalid integer values for adjmat"):
        adjmat({"A": [99, 0], "B": [0, 99]})  # 99 is not a valid edge type


def test_adjmat_all_edge_types():
    # Test with all valid edge type values
    valid_values = [e.value[0] for e in EdgeType]
    n = len(valid_values)
    columns = {f"col_{i}": valid_values for i in range(n)}

    result = adjmat(columns)
    assert isinstance(result, pd.DataFrame)
    assert result.shape == (n, n)


# Legacy tests migrated from legacy/core/test/test_common.py
# These provide additional coverage beyond our new tests


def test_legacy_adjmat_type_error_no_args():
    # Test calling adjmat() with no arguments
    with pytest.raises(TypeError, match="adjmat called with bad arg type"):
        adjmat()


def test_legacy_adjmat_type_error_various_types():
    # Test with various invalid argument types
    with pytest.raises(TypeError, match="adjmat called with bad arg type"):
        adjmat(3)
    with pytest.raises(TypeError, match="adjmat called with bad arg type"):
        adjmat("invalid")
    with pytest.raises(TypeError, match="adjmat called with bad arg type"):
        adjmat([2, 3, 4])
    with pytest.raises(TypeError, match="adjmat called with bad arg type"):
        adjmat([[0, 0], [0, 0]])


def test_legacy_adjmat_type_error_mixed_dict():
    # Test dict with mixed value types (some lists, some not)
    with pytest.raises(TypeError, match="adjmat called with bad arg type"):
        adjmat({"A": [1], "B": "should be a list"})


def test_legacy_adjmat_type_error_string_in_list():
    # Test with string values in the list
    with pytest.raises(TypeError, match="adjmat called with bad arg type"):
        adjmat({"A": ["should be int"]})


def test_legacy_adjmat_value_error_wrong_lengths():
    # Test with mismatched column lengths
    with pytest.raises(
        ValueError, match="some columns wrong length for adjmat"
    ):
        adjmat({"A": [0, 1]})  # 2 elements but only 1 column
    with pytest.raises(
        ValueError, match="some columns wrong length for adjmat"
    ):
        adjmat(
            {"A": [0], "B": [1]}
        )  # Each column should have 2 elements for 2 columns


def test_legacy_adjmat_value_error_invalid_edge_values():
    # Test with invalid edge type integers
    with pytest.raises(ValueError, match="invalid integer values for adjmat"):
        adjmat({"A": [7]})  # 7 is not a valid edge type
    with pytest.raises(ValueError, match="invalid integer values for adjmat"):
        adjmat({"A": [-1]})  # -1 is not a valid edge type
    with pytest.raises(ValueError, match="invalid integer values for adjmat"):
        adjmat({"A": [0, 1], "B": [-99, 0]})  # -99 is not valid


def test_legacy_adjmat_1x1_matrix():
    # Test 1x1 adjacency matrix creation
    expected = (
        pd.DataFrame({"": ["A"], "A": [0]}).set_index("").astype(dtype="int8")
    )
    result = adjmat({"A": [0]})

    assert isinstance(result, pd.DataFrame)
    assert result.equals(expected)


def test_legacy_adjmat_2x2_matrix():
    # Test 2x2 adjacency matrix creation
    expected = (
        pd.DataFrame({"": ["A", "B"], "A": [0, 1], "B": [0, 0]})
        .set_index("")
        .astype(dtype="int8")
    )
    result = adjmat({"A": [0, 1], "B": [0, 0]})

    assert isinstance(result, pd.DataFrame)
    assert result.equals(expected)
