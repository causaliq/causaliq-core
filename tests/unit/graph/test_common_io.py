"""Unit tests for common module - parameter validation and type checking."""

import pytest

from causaliq_core.graph.dag import DAG
from causaliq_core.graph.io.common import read_graph, write_graph


# Test read fails on no arguments
def test_common_read_type_error_no_arguments():
    with pytest.raises(TypeError):
        read_graph()


# Test read fails on bad argument types
def test_common_read_type_error_bad_types():
    with pytest.raises(TypeError):
        read_graph(37)
    with pytest.raises(TypeError):
        read_graph(None)
    with pytest.raises(TypeError):
        read_graph(["bad type"])
    with pytest.raises(TypeError):
        read_graph({"bad": "type"})
    with pytest.raises(TypeError):
        read_graph(True)


# Test read fails on unsupported file suffix
def test_common_read_value_error_unsupported_suffix():
    with pytest.raises(ValueError, match="unsupported file suffix"):
        read_graph("test.txt")
    with pytest.raises(ValueError, match="unsupported file suffix"):
        read_graph("test.json")
    with pytest.raises(ValueError, match="unsupported file suffix"):
        read_graph("test.xml")


# Test write fails on no arguments
def test_common_write_type_error_no_arguments():
    with pytest.raises(TypeError):
        write_graph()


# Test write fails on bad/missing graph
def test_common_write_type_error_bad_graph_types():
    with pytest.raises(TypeError):
        write_graph(10, "/tmp/test.csv")
    with pytest.raises(TypeError):
        write_graph(None, "/tmp/test.csv")
    with pytest.raises(TypeError):
        write_graph("bad type", "/tmp/test.csv")


# Test write fails on bad/missing path
def test_common_write_type_error_bad_path_types():
    dag = DAG(["A", "B"], [("A", "->", "B")])
    with pytest.raises(TypeError):
        write_graph(dag, None)
    with pytest.raises(TypeError):
        write_graph(dag)
    with pytest.raises(TypeError):
        write_graph(dag, 45)


# Test write fails on unsupported file suffix
def test_common_write_value_error_unsupported_suffix():
    dag = DAG(["A", "B"], [("A", "->", "B")])
    with pytest.raises(ValueError, match="unsupported file suffix"):
        write_graph(dag, "test.txt")
    with pytest.raises(ValueError, match="unsupported file suffix"):
        write_graph(dag, "test.json")
    with pytest.raises(ValueError, match="unsupported file suffix"):
        write_graph(dag, "test.xml")
