"""Unit tests for graphml module - parameter validation and type checking."""

import pytest

from causaliq_core.graph.enums import EdgeMark
from causaliq_core.graph.io.graphml import _marks_to_symbol, read


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
