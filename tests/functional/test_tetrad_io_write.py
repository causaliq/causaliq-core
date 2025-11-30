"""Functional tests for tetrad module - writing to files."""

from pathlib import Path

import pytest

from causaliq_core.graph.dag import DAG
from causaliq_core.graph.io.tetrad import read, write
from causaliq_core.graph.pdag import PDAG

# Path to test data
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "functional" / "graphs"
TMP_DIR = TEST_DATA_DIR / "tmp"


@pytest.fixture
def tmp_dir():
    """Fixture to create and clean up temporary directory."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    yield TMP_DIR
    # Cleanup
    for file in TMP_DIR.glob("*.tetrad"):
        file.unlink()


# Test round-trip single node A
def test_tetrad_write_a_roundtrip(tmp_dir):
    # Read original
    graph = read(str(TEST_DATA_DIR / "a.tetrad"))

    # Write to temp file
    temp_file = tmp_dir / "test_a.tetrad"
    write(graph, str(temp_file))

    # Read back
    graph2 = read(str(temp_file))

    # Compare
    assert set(graph.nodes) == set(graph2.nodes)
    assert graph.is_DAG() == graph2.is_DAG()


# Test round-trip A -> B DAG
def test_tetrad_write_ab_roundtrip(tmp_dir):
    # Read original
    graph = read(str(TEST_DATA_DIR / "ab.tetrad"))

    # Write to temp file
    temp_file = tmp_dir / "test_ab.tetrad"
    write(graph, str(temp_file))

    # Read back
    graph2 = read(str(temp_file))

    # Compare
    assert set(graph.nodes) == set(graph2.nodes)
    assert graph.is_DAG() == graph2.is_DAG()


# Test round-trip A -> B -> C DAG
def test_tetrad_write_abc_roundtrip(tmp_dir):
    # Read original
    graph = read(str(TEST_DATA_DIR / "abc.tetrad"))

    # Write to temp file
    temp_file = tmp_dir / "test_abc.tetrad"
    write(graph, str(temp_file))

    # Read back
    graph2 = read(str(temp_file))

    # Compare
    assert set(graph.nodes) == set(graph2.nodes)
    assert graph.is_DAG() == graph2.is_DAG()


# Test round-trip A -> C <- B DAG
def test_tetrad_write_dag_ac_bc_roundtrip(tmp_dir):
    # Read original
    graph = read(str(TEST_DATA_DIR / "ac_bc.tetrad"))

    # Write to temp file
    temp_file = tmp_dir / "test_ac_bc.tetrad"
    write(graph, str(temp_file))

    # Read back
    graph2 = read(str(temp_file))

    # Compare
    assert set(graph.nodes) == set(graph2.nodes)
    assert graph.is_DAG() == graph2.is_DAG()


# Test round-trip cyclic ABC DAG
def test_tetrad_write_dag_abc_acyclic_roundtrip(tmp_dir):
    # Read original
    graph = read(str(TEST_DATA_DIR / "abc_acyclic.tetrad"))

    # Write to temp file
    temp_file = tmp_dir / "test_abc_acyclic.tetrad"
    write(graph, str(temp_file))

    # Read back
    graph2 = read(str(temp_file))

    # Compare
    assert set(graph.nodes) == set(graph2.nodes)
    assert graph.is_DAG() == graph2.is_DAG()


# Test round-trip A - B PDAG
def test_tetrad_write_pdag_ab3_roundtrip(tmp_dir):
    # Read original
    pdag = read(str(TEST_DATA_DIR / "ab3_pdag.tetrad"))

    # Write to temp file
    temp_file = tmp_dir / "test_ab3_pdag.tetrad"
    write(pdag, str(temp_file))

    # Read back
    pdag2 = read(str(temp_file))

    # Compare
    assert set(pdag.nodes) == set(pdag2.nodes)
    assert pdag.is_DAG() == pdag2.is_DAG()


# Test round-trip A - B -> C PDAG
def test_tetrad_write_pdag_abc3_roundtrip(tmp_dir):
    # Read original
    pdag = read(str(TEST_DATA_DIR / "abc3_pdag.tetrad"))

    # Write to temp file
    temp_file = tmp_dir / "test_abc3_pdag.tetrad"
    write(pdag, str(temp_file))

    # Read back
    pdag2 = read(str(temp_file))

    # Compare
    assert set(pdag.nodes) == set(pdag2.nodes)
    assert pdag.is_DAG() == pdag2.is_DAG()


# Test write programmatically created DAG
def test_tetrad_write_manual_dag(tmp_dir):
    # Create a simple DAG: A -> B -> C
    dag = DAG(["A", "B", "C"], [("A", "->", "B"), ("B", "->", "C")])

    # Write to temp file
    temp_file = tmp_dir / "test_manual.tetrad"
    write(dag, str(temp_file))

    # Verify file exists
    assert temp_file.exists()

    # Read back
    dag2 = read(str(temp_file))

    # Compare
    assert set(dag.nodes) == set(dag2.nodes)
    assert dag.is_DAG() == dag2.is_DAG()
    assert "A" in dag2.nodes
    assert "B" in dag2.nodes
    assert "C" in dag2.nodes


# Test write programmatically created PDAG
def test_tetrad_write_manual_pdag(tmp_dir):
    # Create a simple PDAG: A - B -> C
    pdag = PDAG(["A", "B", "C"], [("A", "-", "B"), ("B", "->", "C")])

    # Write to temp file
    temp_file = tmp_dir / "test_manual_pdag.tetrad"
    write(pdag, str(temp_file))

    # Verify file exists
    assert temp_file.exists()

    # Read back
    pdag2 = read(str(temp_file))

    # Compare
    assert set(pdag.nodes) == set(pdag2.nodes)
    assert "A" in pdag2.nodes
    assert "B" in pdag2.nodes
    assert "C" in pdag2.nodes


# Test write to directory that doesn't exist fails
def test_tetrad_write_bad_directory():
    dag = DAG(["A", "B"], [("A", "->", "B")])

    with pytest.raises(FileNotFoundError):
        write(dag, "/nonexistent/directory/test.tetrad")


# Test write to invalid path fails
def test_tetrad_write_bad_path():
    dag = DAG(["A", "B"], [("A", "->", "B")])

    # Test with path that contains null character
    with pytest.raises((OSError, ValueError)):
        write(dag, "bad\x00path.tetrad")
