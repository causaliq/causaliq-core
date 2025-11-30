"""Unit tests for common module - parameter validation and type checking."""

import pytest

from causaliq_core.graph.dag import DAG
from causaliq_core.graph.io.common import read, write


# Test read fails on no arguments
def test_common_read_type_error_no_arguments():
    with pytest.raises(TypeError):
        read()


# Test read fails on bad argument types
def test_common_read_type_error_bad_types():
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


# Test read fails on unsupported file suffix
def test_common_read_value_error_unsupported_suffix():
    with pytest.raises(ValueError, match="unsupported file suffix"):
        read("test.txt")
    with pytest.raises(ValueError, match="unsupported file suffix"):
        read("test.json")
    with pytest.raises(ValueError, match="unsupported file suffix"):
        read("test.xml")


# Test write fails on no arguments
def test_common_write_type_error_no_arguments():
    with pytest.raises(TypeError):
        write()


# Test write fails on bad/missing graph
def test_common_write_type_error_bad_graph_types():
    with pytest.raises(TypeError):
        write(10, "/tmp/test.csv")
    with pytest.raises(TypeError):
        write(None, "/tmp/test.csv")
    with pytest.raises(TypeError):
        write("bad type", "/tmp/test.csv")


# Test write fails on bad/missing path
def test_common_write_type_error_bad_path_types():
    dag = DAG(["A", "B"], [("A", "->", "B")])
    with pytest.raises(TypeError):
        write(dag, None)
    with pytest.raises(TypeError):
        write(dag)
    with pytest.raises(TypeError):
        write(dag, 45)


# Test write fails on unsupported file suffix
def test_common_write_value_error_unsupported_suffix():
    dag = DAG(["A", "B"], [("A", "->", "B")])
    with pytest.raises(ValueError, match="unsupported file suffix"):
        write(dag, "test.txt")
    with pytest.raises(ValueError, match="unsupported file suffix"):
        write(dag, "test.json")
    with pytest.raises(ValueError, match="unsupported file suffix"):
        write(dag, "test.xml")
