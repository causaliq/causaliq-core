"""Unit tests for bayesys module - parameter validation and type checking."""

import pytest

from causaliq_core.graph import DAG
from causaliq_core.graph.io.bayesys import read, write


# Test read fails on no arguments
def test_bayesys_read_typeerror_no_arguments():
    with pytest.raises(TypeError):
        read()


# Test read fails on bad argument types for path
def test_bayesys_read_typeerror_bad_path_types():
    with pytest.raises(TypeError):
        read(1)
    with pytest.raises(TypeError):
        read(0.7)
    with pytest.raises(TypeError):
        read(False)


# Test write fails on no arguments
def test_bayesys_write_type_error_no_arguments():
    with pytest.raises(TypeError):
        write()


# Test write fails on bad/missing pdag
def test_bayesys_write_type_error_bad_pdag_types():
    with pytest.raises(TypeError):
        write(10, "/tmp/test.csv")
    with pytest.raises(TypeError):
        write(None, "/tmp/test.csv")
    with pytest.raises(TypeError):
        write("bad type", "/tmp/test.csv")


# Test write fails on bad/missing path
def test_bayesys_write_type_error_bad_path_types():
    dag = DAG(["A", "B"], [("A", "->", "B")])
    with pytest.raises(TypeError):
        write(dag, None)
    with pytest.raises(TypeError):
        write(dag)
    with pytest.raises(TypeError):
        write(dag, 45)
