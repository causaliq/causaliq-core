"""Functional tests for tetrad module - reading from files."""

from pathlib import Path

import pytest

from causaliq_core.graph.io.tetrad import read
from causaliq_core.utils import FileFormatError

# Path to test data
TEST_DATA_DIR = Path("tests/data/functional/graphs")


# Test read fails on nonexistent file
def test_tetrad_read_filenotfound_error():
    with pytest.raises(FileNotFoundError):
        read("doesnotexist.tetrad")


# Test read fails on binary file
def test_tetrad_read_fileformat_error_binary():
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "null.sys.tetrad"))


# Test read fails on bad section header 1
def test_tetrad_read_fileformat_error_bad_section_1():
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "ab_bad_section_1.tetrad"))


# Test read fails on bad section header 2
def test_tetrad_read_fileformat_error_bad_section_2():
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "ab_bad_section_2.tetrad"))


# Test read fails on bad edge format
def test_tetrad_read_fileformat_error_bad_edge():
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "ab_bad_edge_1.tetrad"))


# Test reading single node A
def test_tetrad_read_a_ok():
    graph = read(str(TEST_DATA_DIR / "a.tetrad"))
    assert graph is not None
    assert len(graph.nodes) == 1
    assert "A" in graph.nodes
    assert graph.is_DAG()


# Test reading A -> B DAG
def test_tetrad_read_ab_ok():
    graph = read(str(TEST_DATA_DIR / "ab.tetrad"))
    assert graph is not None
    assert len(graph.nodes) == 2
    assert set(graph.nodes) == {"A", "B"}
    assert graph.is_DAG()


# Test reading A -> B -> C DAG
def test_tetrad_read_abc_ok():
    graph = read(str(TEST_DATA_DIR / "abc.tetrad"))
    assert graph is not None
    assert len(graph.nodes) == 3
    assert set(graph.nodes) == {"A", "B", "C"}
    assert graph.is_DAG()


# Test reading A -> C <- B DAG
def test_tetrad_read_dag_ac_bc_ok():
    graph = read(str(TEST_DATA_DIR / "ac_bc.tetrad"))
    assert graph is not None
    assert len(graph.nodes) == 3
    assert set(graph.nodes) == {"A", "B", "C"}
    assert graph.is_DAG()


# Test reading cyclic ABC DAG
def test_tetrad_read_dag_abc_acyclic_ok():
    graph = read(str(TEST_DATA_DIR / "abc_acyclic.tetrad"))
    assert graph is not None
    assert len(graph.nodes) == 3
    assert set(graph.nodes) == {"A", "B", "C"}
    assert graph.is_DAG()


# Test reading Cancer DAG
def test_tetrad_read_dag_cancer_ok():
    graph = read(str(TEST_DATA_DIR / "cancer.tetrad"))
    assert graph is not None
    assert len(graph.nodes) == 5  # Cancer has 5 nodes
    assert graph.is_DAG()


# Test reading Asia DAG
def test_tetrad_read_dag_asia_ok():
    graph = read(str(TEST_DATA_DIR / "asia.tetrad"))
    assert graph is not None
    assert len(graph.nodes) == 8  # Asia has 8 nodes
    assert graph.is_DAG()


# Test reading AND4_17 DAG
def test_tetrad_read_dag_and4_17_ok():
    graph = read(str(TEST_DATA_DIR / "and4_17.tetrad"))
    assert graph is not None
    assert len(graph.nodes) == 4
    assert graph.is_DAG()


# Test reading complete 4-node DAG
def test_tetrad_read_dag_complete4_ok():
    graph = read(str(TEST_DATA_DIR / "complete4.tetrad"))
    assert graph is not None
    assert len(graph.nodes) == 4
    assert graph.is_DAG()


# Test reading A - B PDAG
def test_tetrad_read_pdag_ab3_ok():
    pdag = read(str(TEST_DATA_DIR / "ab3_pdag.tetrad"))
    assert pdag is not None
    assert len(pdag.nodes) == 2
    assert set(pdag.nodes) == {"A", "B"}
    assert not pdag.is_DAG()  # Should be PDAG, not DAG


# Test reading A - B -> C PDAG
def test_tetrad_read_pdag_abc3_ok():
    pdag = read(str(TEST_DATA_DIR / "abc3_pdag.tetrad"))
    assert pdag is not None
    assert len(pdag.nodes) == 3
    assert set(pdag.nodes) == {"A", "B", "C"}
    assert not pdag.is_DAG()  # Should be PDAG, not DAG
