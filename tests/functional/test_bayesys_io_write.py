"""Functional tests for bayesys module - writing to files."""

import os
import tempfile
from pathlib import Path

import pytest

from causaliq_core.graph import DAG, PDAG
from causaliq_core.graph.io.bayesys import read, write

# Path to test data
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "functional" / "graphs"
TMP_DIR = TEST_DATA_DIR / "tmp"


@pytest.fixture(scope="function")
def tmpfile():
    """Create a temporary file that gets automatically cleaned up."""
    # Ensure tmp directory exists
    TMP_DIR.mkdir(exist_ok=True)

    # Create temporary file
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", dir=TMP_DIR
    ) as f:
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


# Test write fails on nonexistent directory
def test_bayesys_write_filenotfounderror():
    dag = DAG(["A", "B"], [("A", "->", "B")])
    with pytest.raises(FileNotFoundError):
        write(dag, str(TEST_DATA_DIR / "nonexistent" / "ab.csv"))


# Test writing and reading A -> B DAG
def test_bayesys_write_ab_ok(tmpfile):
    dag = DAG(["A", "B"], [("A", "->", "B")])
    write(dag, tmpfile)

    # Read it back and verify
    read_graph = read(tmpfile)
    assert read_graph == dag
    assert read_graph.is_DAG()


# Test writing and reading A -> B -> C DAG
def test_bayesys_write_abc_ok(tmpfile):
    dag = DAG(["A", "B", "C"], [("A", "->", "B"), ("B", "->", "C")])
    write(dag, tmpfile)

    # Read it back and verify
    read_graph = read(tmpfile)
    assert read_graph == dag
    assert read_graph.is_DAG()


# Test writing and reading A -> C <- B DAG
def test_bayesys_write_ac_bc_ok(tmpfile):
    dag = DAG(["A", "B", "C"], [("A", "->", "C"), ("B", "->", "C")])
    write(dag, tmpfile)

    # Read it back and verify
    read_graph = read(tmpfile)
    assert read_graph == dag
    assert read_graph.is_DAG()


# Test writing and reading A - B PDAG
def test_bayesys_write_pdag_ab_ok(tmpfile):
    pdag = PDAG(["A", "B"], [("A", "-", "B")])
    write(pdag, tmpfile)

    # Read it back and verify
    read_graph = read(tmpfile)
    assert read_graph == pdag
    assert not read_graph.is_DAG()


# Test writing and reading A - B -> C PDAG
def test_bayesys_write_pdag_abc_ok(tmpfile):
    pdag = PDAG(["A", "B", "C"], [("A", "-", "B"), ("B", "->", "C")])
    write(pdag, tmpfile)

    # Read it back and verify
    read_graph = read(tmpfile)
    assert read_graph == pdag
    assert not read_graph.is_DAG()


# Test writing and reading a larger DAG
def test_bayesys_write_large_dag_ok(tmpfile):
    # Create a larger DAG with multiple nodes
    nodes = ["A", "B", "C", "D", "E"]
    edges = [
        ("A", "->", "B"),
        ("A", "->", "C"),
        ("B", "->", "D"),
        ("C", "->", "D"),
        ("D", "->", "E"),
    ]
    dag = DAG(nodes, edges)

    write(dag, tmpfile)

    # Read it back and verify
    read_graph = read(tmpfile)
    assert read_graph == dag
    assert read_graph.is_DAG()
    assert len(read_graph.nodes) == 5
    assert len(read_graph.edges) == 5


# Test writing and reading a DAG with disconnected components
def test_bayesys_write_disconnected_dag_ok(tmpfile):
    # Create DAG with disconnected components: A -> B and C -> D
    dag = DAG(["A", "B", "C", "D"], [("A", "->", "B"), ("C", "->", "D")])

    write(dag, tmpfile)

    # Read it back and verify
    read_graph = read(tmpfile)
    assert read_graph == dag
    assert read_graph.is_DAG()
    assert len(read_graph.nodes) == 4
    assert len(read_graph.edges) == 2
