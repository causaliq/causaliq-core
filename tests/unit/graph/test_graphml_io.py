"""Unit tests for graphml module - parameter validation and type checking."""

import pytest

from causaliq_core.graph import DAG
from causaliq_core.graph.enums import EdgeMark
from causaliq_core.graph.io.graphml import _marks_to_symbol, read, write


# Test read fails on no arguments.
def test_graphml_read_type_error_no_arguments() -> None:
    with pytest.raises(TypeError):
        read()


# Test read fails on bad argument types.
def test_graphml_read_type_error_bad_types() -> None:
    with pytest.raises(TypeError):
        read(37)
    with pytest.raises(TypeError):
        read(None)
    with pytest.raises(TypeError):
        read(["bad type"])
    with pytest.raises(TypeError):
        read({"bad": "type"})
    with pytest.raises(TypeError):
        read(True)


# Test read fails on bad file suffix.
def test_graphml_read_value_error_bad_suffix() -> None:
    with pytest.raises(ValueError):
        read("test.txt")
    with pytest.raises(ValueError):
        read("test.xml")
    with pytest.raises(ValueError):
        read("test.csv")


# Test _marks_to_symbol handles reverse lookups.
def test_marks_to_symbol_reverse_lookup() -> None:
    # ARROW -> LINE is reverse of LINE -> ARROW (DIRECTED)
    result = _marks_to_symbol(EdgeMark.ARROW, EdgeMark.LINE)
    assert result == "->"

    # LINE -> CIRCLE is reverse of CIRCLE -> LINE (SEMIUNDIRECTED)
    result = _marks_to_symbol(EdgeMark.LINE, EdgeMark.CIRCLE)
    assert result == "o-"

    # ARROW -> CIRCLE is reverse of CIRCLE -> ARROW (SEMIDIRECTED)
    result = _marks_to_symbol(EdgeMark.ARROW, EdgeMark.CIRCLE)
    assert result == "o->"


# Test _marks_to_symbol defaults to directed for unknown combinations.
def test_marks_to_symbol_unknown_defaults_to_directed() -> None:
    # NONE marks don't match any EdgeType, should default to directed
    result = _marks_to_symbol(EdgeMark.NONE, EdgeMark.NONE)
    assert result == "->"

    result = _marks_to_symbol(EdgeMark.NONE, EdgeMark.LINE)
    assert result == "->"

    result = _marks_to_symbol(EdgeMark.LINE, EdgeMark.NONE)
    assert result == "->"


# =============================================================================
# Tests for graphml.write() parameter validation
# =============================================================================


# Test write fails on no arguments.
def test_graphml_write_type_error_no_arguments() -> None:
    with pytest.raises(TypeError):
        write()


# Test write fails on bad graph argument types.
def test_graphml_write_type_error_bad_graph_type() -> None:
    with pytest.raises(TypeError):
        write(None, "test.graphml")
    with pytest.raises(TypeError):
        write("not a graph", "test.graphml")
    with pytest.raises(TypeError):
        write(37, "test.graphml")
    with pytest.raises(TypeError):
        write(["A", "B"], "test.graphml")


# Test write fails on bad path argument types.
def test_graphml_write_type_error_bad_path_type() -> None:
    dag = DAG(["A", "B"], [("A", "->", "B")])
    with pytest.raises(TypeError):
        write(dag, None)
    with pytest.raises(TypeError):
        write(dag, 37)
    with pytest.raises(TypeError):
        write(dag, ["test.graphml"])


# Test write fails on bad file suffix.
def test_graphml_write_value_error_bad_suffix() -> None:
    dag = DAG(["A", "B"], [("A", "->", "B")])
    with pytest.raises(ValueError):
        write(dag, "test.txt")
    with pytest.raises(ValueError):
        write(dag, "test.xml")
    with pytest.raises(ValueError):
        write(dag, "test.csv")
