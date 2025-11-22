"""
Unit tests for EdgeMark and EdgeType enums in causaliq_core.graph.
"""

from causaliq_core.graph import EdgeMark, EdgeType


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
