"""Unit tests for tetrad module - parameter validation and type checking."""

import pytest

from causaliq_core.graph import DAG
from causaliq_core.graph.io.tetrad import read, write


# Test read fails on no arguments
def test_tetrad_read_type_error_no_arguments():
    with pytest.raises(TypeError):
        read()


# Test read fails on bad argument types
def test_tetrad_read_type_error_bad_types():
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


# Test read fails on bad file suffix
def test_tetrad_read_value_error_bad_suffix():
    with pytest.raises(ValueError):
        read("test.txt")


# Test write fails on no arguments
def test_tetrad_write_type_error_no_arguments():
    with pytest.raises(TypeError):
        write()


# Test write fails on bad/missing pdag
def test_tetrad_write_type_error_bad_pdag_types():
    with pytest.raises(TypeError):
        write(10, "/tmp/test.tetrad")
    with pytest.raises(TypeError):
        write(None, "/tmp/test.tetrad")
    with pytest.raises(TypeError):
        write("bad type", "/tmp/test.tetrad")


# Test write fails on bad/missing path
def test_tetrad_write_type_error_bad_path_types():
    dag = DAG(["A", "B"], [("A", "->", "B")])
    with pytest.raises(TypeError):
        write(dag, None)
    with pytest.raises(TypeError):
        write(dag)
    with pytest.raises(TypeError):
        write(dag, 45)
