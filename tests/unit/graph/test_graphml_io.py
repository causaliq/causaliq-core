"""Unit tests for graphml module - parameter validation and type checking."""

from io import StringIO

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


# =============================================================================
# Tests for StringIO support
# =============================================================================


# Test write to StringIO produces valid XML.
def test_graphml_write_stringio_produces_xml() -> None:
    dag = DAG(["A", "B"], [("A", "->", "B")])
    buffer = StringIO()
    write(dag, buffer)
    xml_content = buffer.getvalue()
    assert "<?xml" in xml_content
    assert "<graphml" in xml_content
    assert 'id="A"' in xml_content
    assert 'id="B"' in xml_content


# Test read from StringIO parses valid XML.
def test_graphml_read_stringio_parses_xml() -> None:
    xml_content = """<?xml version="1.0" encoding="utf-8"?>
    <graphml xmlns="http://graphml.graphdrawing.org/xmlns">
        <graph id="G" edgedefault="directed">
            <node id="A"/>
            <node id="B"/>
            <edge source="A" target="B"/>
        </graph>
    </graphml>"""
    buffer = StringIO(xml_content)
    graph = read(buffer)
    assert "A" in graph.nodes
    assert "B" in graph.nodes
    assert len(graph.edges) == 1


# Test roundtrip write then read via StringIO.
def test_graphml_stringio_roundtrip() -> None:
    original = DAG(["X", "Y", "Z"], [("X", "->", "Y"), ("Y", "->", "Z")])

    # Write to StringIO
    buffer = StringIO()
    write(original, buffer)

    # Read from StringIO (must seek to start)
    buffer.seek(0)
    restored = read(buffer)

    assert list(restored.nodes) == list(original.nodes)
    assert len(restored.edges) == len(original.edges)
