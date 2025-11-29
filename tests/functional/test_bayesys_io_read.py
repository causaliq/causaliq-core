"""Functional tests for bayesys module - reading from files."""

from pathlib import Path

import pytest

from causaliq_core.graph.io.bayesys import read
from causaliq_core.utils import FileFormatError

# Path to test data
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "functional" / "graphs"


# Test read fails on nonexistent file
def test_bayesys_read_filenotfounderror():
    with pytest.raises(FileNotFoundError):
        read("doesnotexist.txt")


# Test read fails on binary file
def test_binaryfile():
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "null.sys"))


# Test read fails on empty file
def test_emptyfile():
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "empty.txt"))


# Test read fails on file with missing columns
def test_missingcolumns():
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "missing_columns.csv"))


# Test read fails on bad header format 1
def test_badheader1():
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "bad_header1.csv"))


# Test read fails on bad header format 2
def test_badheader2():
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "bad_header2.csv"))


# Test read fails on bad line ID (non-sequential)
def test_bad_line_id():
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "bad_line_id.csv"))


# Test known bad header 1 fails with strict=True
def test_badheader_known1_strict():
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "bad_header_known1.csv"))


# Test known bad header 2 fails with strict=True
def test_badheader_known2_strict():
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "bad_header_known2.csv"))


# Test known bad header 1 works with strict=False
def test_badheader_known1_notstrict():
    graph = read(str(TEST_DATA_DIR / "bad_header_known1.csv"), strict=False)
    # Should create valid Asia network
    assert graph is not None
    assert len(graph.nodes) == 8


# Test known bad header 2 works with strict=False
def test_badheader_known2_notstrict():
    graph = read(str(TEST_DATA_DIR / "bad_header_known2.csv"), strict=False)
    # Should create valid Asia network
    assert graph is not None
    assert len(graph.nodes) == 8


# Test reading Asia DAG file
def test_asia_ok():
    graph = read(str(TEST_DATA_DIR / "asia.csv"))
    assert graph is not None
    assert len(graph.nodes) == 8
    # Verify it's a DAG (fully directed)
    assert graph.is_DAG()


# Test reading Asia DAG with all_nodes specification
def test_asia_all_nodes_ok():
    all_nodes = [
        "asia",
        "tub",
        "smoke",
        "lung",
        "bronc",
        "either",
        "xray",
        "dysp",
    ]
    graph = read(str(TEST_DATA_DIR / "asia.csv"), all_nodes)
    assert graph is not None
    assert set(graph.nodes) == set(all_nodes)


# Test read fails when file contains nodes not in all_nodes
def test_all_nodes_validation_error():
    # xy_nodes.csv contains X and Y, but all_nodes only allows A and B
    all_nodes = ["A", "B"]
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "xy_nodes.csv"), all_nodes)


# Test reading Asia DAG file with quoted values
def test_asia_quoted_ok():
    graph = read(str(TEST_DATA_DIR / "asia_quoted.csv"))
    assert graph is not None
    assert len(graph.nodes) == 8


# Test reading simple triple chain A->B->C
def test_triple_chain_ok():
    graph = read(str(TEST_DATA_DIR / "abc.csv"))
    assert graph is not None
    assert len(graph.nodes) == 3
    assert set(graph.nodes) == {"A", "B", "C"}


# Test reading triple chain with all_nodes specification
def test_triple_chain_all_nodes_ok():
    all_nodes = ["A", "B", "C"]
    graph = read(str(TEST_DATA_DIR / "abc.csv"), all_nodes)
    assert graph is not None
    assert set(graph.nodes) == set(all_nodes)


# Test reading Alarm network
def test_bayesys_read_alarm_ok():
    graph = read(str(TEST_DATA_DIR / "alarm.csv"))
    assert graph is not None
    assert len(graph.nodes) == 37  # Alarm has 37 nodes


# Test reading Diarrhoea network
def test_bayesys_read_diarrhoea_ok():
    graph = read(str(TEST_DATA_DIR / "diarrhoea.csv"))
    assert graph is not None
    assert len(graph.nodes) == 28  # Diarrhoea has 28 nodes


# Test reading A - B PDAG
def test_bayesys_read_pdag_ab3_ok():
    pdag = read(str(TEST_DATA_DIR / "ab_pdag.csv"))
    assert pdag is not None
    assert len(pdag.nodes) == 2
    assert set(pdag.nodes) == {"A", "B"}
    assert not pdag.is_DAG()  # Should be PDAG, not DAG


# Test reading A - B -> C PDAG
def test_bayesys_read_pdag_abc3_ok():
    pdag = read(str(TEST_DATA_DIR / "abc3_pdag.csv"))
    assert pdag is not None
    assert len(pdag.nodes) == 3
    assert set(pdag.nodes) == {"A", "B", "C"}
    assert not pdag.is_DAG()  # Should be PDAG, not DAG
