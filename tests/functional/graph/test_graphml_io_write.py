"""Functional tests for graphml module - writing to files and round-trips."""

from pathlib import Path

import pytest

from causaliq_core.graph import DAG, PDAG, SDG, EdgeType
from causaliq_core.graph.io.graphml import read, write

# Path to test data and output directory.
TEST_DATA_DIR = Path("tests/data/functional/graphs")
TEST_OUTPUT_DIR = Path("tests/data/functional/graphs/tmp")


@pytest.fixture(autouse=True)
def setup_output_dir() -> None:
    """Ensure output directory exists before tests."""
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Tests for graphml.write() basic functionality
# =============================================================================


# Test write creates valid GraphML file for single node DAG.
def test_graphml_write_single_node_dag() -> None:
    dag = DAG(["A"], [])
    output_path = str(TEST_OUTPUT_DIR / "write_single_node.graphml")
    write(dag, output_path)

    # Verify file exists and can be read back
    assert Path(output_path).exists()
    result = read(output_path)
    assert isinstance(result, DAG)
    assert result.nodes == ["A"]
    assert len(result.edges) == 0


# Test write creates valid GraphML file for simple DAG.
def test_graphml_write_simple_dag() -> None:
    dag = DAG(["A", "B"], [("A", "->", "B")])
    output_path = str(TEST_OUTPUT_DIR / "write_simple_dag.graphml")
    write(dag, output_path)

    # Verify file exists and can be read back
    assert Path(output_path).exists()
    result = read(output_path)
    assert isinstance(result, DAG)
    assert set(result.nodes) == {"A", "B"}
    assert ("A", "B") in result.edges


# Test write creates valid GraphML file for PDAG with undirected edge.
def test_graphml_write_pdag_undirected() -> None:
    pdag = PDAG(["A", "B", "C"], [("A", "->", "B"), ("B", "-", "C")])
    output_path = str(TEST_OUTPUT_DIR / "write_pdag.graphml")
    write(pdag, output_path)

    result = read(output_path)
    assert isinstance(result, PDAG)
    assert set(result.nodes) == {"A", "B", "C"}
    assert result.edges[("A", "B")] == EdgeType.DIRECTED
    assert result.edges[("B", "C")] == EdgeType.UNDIRECTED


# Test write creates valid GraphML file for SDG with bidirected edges.
def test_graphml_write_sdg_bidirected() -> None:
    sdg = SDG(["A", "B", "C"], [("A", "<->", "B"), ("B", "->", "C")])
    output_path = str(TEST_OUTPUT_DIR / "write_sdg_bidirected.graphml")
    write(sdg, output_path)

    result = read(output_path)
    assert isinstance(result, SDG)
    assert set(result.nodes) == {"A", "B", "C"}
    assert result.edges[("A", "B")] == EdgeType.BIDIRECTED
    assert result.edges[("B", "C")] == EdgeType.DIRECTED


# =============================================================================
# Round-trip tests (read -> write -> read)
# =============================================================================


# Test round-trip for simple DAG preserves structure.
def test_graphml_roundtrip_ab_dag() -> None:
    original = read(str(TEST_DATA_DIR / "ab.graphml"))
    output_path = str(TEST_OUTPUT_DIR / "roundtrip_ab.graphml")
    write(original, output_path)

    result = read(output_path)
    assert result.nodes == original.nodes
    assert result.edges == original.edges


# Test round-trip for DAG with three nodes preserves structure.
def test_graphml_roundtrip_abc_dag() -> None:
    original = read(str(TEST_DATA_DIR / "abc.graphml"))
    output_path = str(TEST_OUTPUT_DIR / "roundtrip_abc.graphml")
    write(original, output_path)

    result = read(output_path)
    assert result.nodes == original.nodes
    assert result.edges == original.edges


# Test round-trip for PDAG preserves undirected edges.
def test_graphml_roundtrip_pdag() -> None:
    original = read(str(TEST_DATA_DIR / "abc_pdag.graphml"))
    output_path = str(TEST_OUTPUT_DIR / "roundtrip_pdag.graphml")
    write(original, output_path)

    result = read(output_path)
    assert set(result.nodes) == set(original.nodes)
    assert result.edges == original.edges


# Test round-trip for PAG preserves complex edge types.
def test_graphml_roundtrip_pag() -> None:
    original = read(str(TEST_DATA_DIR / "abc_pag.graphml"))
    output_path = str(TEST_OUTPUT_DIR / "roundtrip_pag.graphml")
    write(original, output_path)

    result = read(output_path)
    assert set(result.nodes) == set(original.nodes)
    assert result.edges == original.edges


# Test round-trip for Asia network preserves all nodes and edges.
def test_graphml_roundtrip_asia() -> None:
    original = read(str(TEST_DATA_DIR / "asia.graphml"))
    output_path = str(TEST_OUTPUT_DIR / "roundtrip_asia.graphml")
    write(original, output_path)

    result = read(output_path)
    assert set(result.nodes) == set(original.nodes)
    assert len(result.edges) == len(original.edges)
    assert result.edges == original.edges


# Test round-trip preserves all 9 edge endpoint combinations.
def test_graphml_roundtrip_all_edge_endpoints() -> None:
    original = read(str(TEST_DATA_DIR / "all_edge_endpoints.graphml"))
    output_path = str(TEST_OUTPUT_DIR / "roundtrip_all_endpoints.graphml")
    write(original, output_path)

    result = read(output_path)
    assert set(result.nodes) == set(original.nodes)
    assert len(result.edges) == len(original.edges)
    # Check each edge type is preserved
    for edge_key, edge_type in original.edges.items():
        assert edge_key in result.edges, f"Missing edge: {edge_key}"
        assert result.edges[edge_key] == edge_type, (
            f"Edge {edge_key} type mismatch: "
            f"expected {edge_type}, got {result.edges[edge_key]}"
        )


# =============================================================================
# Tests for all edge types
# =============================================================================


# Test write and read preserves directed edge (->).
def test_graphml_write_edge_directed() -> None:
    dag = DAG(["A", "B"], [("A", "->", "B")])
    output_path = str(TEST_OUTPUT_DIR / "write_edge_directed.graphml")
    write(dag, output_path)

    result = read(output_path)
    assert result.edges[("A", "B")] == EdgeType.DIRECTED


# Test write and read preserves undirected edge (-).
def test_graphml_write_edge_undirected() -> None:
    pdag = PDAG(["A", "B"], [("A", "-", "B")])
    output_path = str(TEST_OUTPUT_DIR / "write_edge_undirected.graphml")
    write(pdag, output_path)

    result = read(output_path)
    assert result.edges[("A", "B")] == EdgeType.UNDIRECTED


# Test write and read preserves bidirected edge (<->).
def test_graphml_write_edge_bidirected() -> None:
    sdg = SDG(["A", "B"], [("A", "<->", "B")])
    output_path = str(TEST_OUTPUT_DIR / "write_edge_bidirected.graphml")
    write(sdg, output_path)

    result = read(output_path)
    assert result.edges[("A", "B")] == EdgeType.BIDIRECTED


# Test write and read preserves semidirected edge (o->).
def test_graphml_write_edge_semidirected() -> None:
    sdg = SDG(["A", "B"], [("A", "o->", "B")])
    output_path = str(TEST_OUTPUT_DIR / "write_edge_semidirected.graphml")
    write(sdg, output_path)

    result = read(output_path)
    assert result.edges[("A", "B")] == EdgeType.SEMIDIRECTED


# Test write and read preserves semiundirected edge (o-).
def test_graphml_write_edge_semiundirected() -> None:
    sdg = SDG(["A", "B"], [("A", "o-", "B")])
    output_path = str(TEST_OUTPUT_DIR / "write_edge_semiundirected.graphml")
    write(sdg, output_path)

    result = read(output_path)
    assert result.edges[("A", "B")] == EdgeType.SEMIUNDIRECTED


# Test write and read preserves nondirected edge (o-o).
def test_graphml_write_edge_nondirected() -> None:
    sdg = SDG(["A", "B"], [("A", "o-o", "B")])
    output_path = str(TEST_OUTPUT_DIR / "write_edge_nondirected.graphml")
    write(sdg, output_path)

    result = read(output_path)
    assert result.edges[("A", "B")] == EdgeType.NONDIRECTED


# =============================================================================
# Tests for node ordering preservation
# =============================================================================


# Test write preserves node ordering.
def test_graphml_write_preserves_node_order() -> None:
    # SDG sorts nodes alphabetically, so we test that this is preserved
    dag = DAG(["Z", "A", "M", "B"], [("A", "->", "B"), ("M", "->", "Z")])
    output_path = str(TEST_OUTPUT_DIR / "write_node_order.graphml")
    write(dag, output_path)

    result = read(output_path)
    # Nodes should be in alphabetical order (as SDG sorts them)
    assert result.nodes == ["A", "B", "M", "Z"]
