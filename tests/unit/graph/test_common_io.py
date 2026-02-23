"""Unit tests for common module - parameter validation and type checking."""

import pytest

from causaliq_core.graph.dag import DAG
from causaliq_core.graph.io.common import (
    read_graph,
    read_pdg,
    write_graph,
    write_pdg,
)


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


# Test read_pdg fails on bad argument types.
def test_common_read_pdg_type_error_bad_types():
    with pytest.raises(TypeError, match="bad arg type"):
        read_pdg(37)
    with pytest.raises(TypeError, match="bad arg type"):
        read_pdg(None)
    with pytest.raises(TypeError, match="bad arg type"):
        read_pdg(["bad type"])


# Test read_pdg fails on non-graphml suffix.
def test_common_read_pdg_value_error_wrong_suffix():
    with pytest.raises(ValueError, match="must have .graphml suffix"):
        read_pdg("test.csv")
    with pytest.raises(ValueError, match="must have .graphml suffix"):
        read_pdg("test.tetrad")
    with pytest.raises(ValueError, match="must have .graphml suffix"):
        read_pdg("test.txt")


# Test write_pdg fails on bad argument types.
def test_common_write_pdg_type_error_bad_types():
    with pytest.raises(TypeError, match="bad arg types"):
        write_pdg(None, "/tmp/test.graphml")
    with pytest.raises(TypeError, match="bad arg types"):
        write_pdg("bad type", "/tmp/test.graphml")


# Test write_pdg fails on bad path type.
def test_common_write_pdg_type_error_bad_path():
    from causaliq_core.graph.pdg import PDG, EdgeProbabilities

    pdg = PDG(
        ["A", "B"],
        {("A", "B"): EdgeProbabilities(forward=0.8, backward=0.1, none=0.1)},
    )
    with pytest.raises(TypeError, match="bad arg types"):
        write_pdg(pdg, None)
    with pytest.raises(TypeError, match="bad arg types"):
        write_pdg(pdg, 45)


# Test write_pdg fails on non-graphml suffix.
def test_common_write_pdg_value_error_wrong_suffix():
    from causaliq_core.graph.pdg import PDG, EdgeProbabilities

    pdg = PDG(
        ["A", "B"],
        {("A", "B"): EdgeProbabilities(forward=0.8, backward=0.1, none=0.1)},
    )
    with pytest.raises(ValueError, match="must have .graphml suffix"):
        write_pdg(pdg, "test.csv")
    with pytest.raises(ValueError, match="must have .graphml suffix"):
        write_pdg(pdg, "test.tetrad")
