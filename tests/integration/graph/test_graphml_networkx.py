"""Integration tests for GraphML interoperability with NetworkX.

These tests verify that GraphML files produced by causaliq-core can be
read by NetworkX, and that GraphML files produced by NetworkX can be
read by causaliq-core.
"""

import tempfile
from pathlib import Path

import networkx as nx

from causaliq_core.graph import DAG
from causaliq_core.graph.io.graphml import read

# Path to test data.
TEST_DATA_DIR = Path("tests/data/functional/graphs")

# =============================================================================
# Tests: causaliq-core GraphML files readable by NetworkX
# =============================================================================


# Test NetworkX can read our single node GraphML.
def test_networkx_reads_causaliq_single_node() -> None:
    filepath = str(TEST_DATA_DIR / "a.graphml")
    G = nx.read_graphml(filepath)
    assert len(G.nodes) == 1
    assert "A" in G.nodes


# Test NetworkX can read our two node DAG GraphML.
def test_networkx_reads_causaliq_ab_dag() -> None:
    filepath = str(TEST_DATA_DIR / "ab.graphml")
    G = nx.read_graphml(filepath)
    assert len(G.nodes) == 2
    assert set(G.nodes) == {"A", "B"}
    assert len(G.edges) == 1
    assert ("A", "B") in G.edges


# Test NetworkX can read our three node DAG GraphML.
def test_networkx_reads_causaliq_abc_dag() -> None:
    filepath = str(TEST_DATA_DIR / "abc.graphml")
    G = nx.read_graphml(filepath)
    assert len(G.nodes) == 3
    assert set(G.nodes) == {"A", "B", "C"}
    assert len(G.edges) == 2


# Test NetworkX can read our Asia network GraphML.
def test_networkx_reads_causaliq_asia() -> None:
    filepath = str(TEST_DATA_DIR / "asia.graphml")
    G = nx.read_graphml(filepath)
    assert len(G.nodes) == 8
    expected_nodes = {
        "asia",
        "tub",
        "smoke",
        "lung",
        "bronc",
        "either",
        "xray",
        "dysp",
    }
    assert set(G.nodes) == expected_nodes


# Test NetworkX can read non-namespaced GraphML.
def test_networkx_reads_causaliq_no_namespace() -> None:
    filepath = str(TEST_DATA_DIR / "ab_no_namespace.graphml")
    G = nx.read_graphml(filepath)
    assert len(G.nodes) == 2
    assert set(G.nodes) == {"A", "B"}


# Test NetworkX can read PDAG with endpoint attributes.
def test_networkx_reads_causaliq_pdag_endpoints() -> None:
    filepath = str(TEST_DATA_DIR / "abc_pdag_edgetype.graphml")
    G = nx.read_graphml(filepath)
    assert len(G.nodes) == 3
    assert set(G.nodes) == {"A", "B", "C"}
    # NetworkX reads the edges, endpoint data is preserved as edge attrs
    assert len(G.edges) == 2


# =============================================================================
# Tests: NetworkX-generated GraphML files readable by causaliq-core
# =============================================================================


# Test causaliq-core can read NetworkX-generated DAG.
def test_causaliq_reads_networkx_dag() -> None:
    # Create a DAG in NetworkX
    G = nx.DiGraph()
    G.add_nodes_from(["X", "Y", "Z"])
    G.add_edge("X", "Y")
    G.add_edge("Y", "Z")

    # Write to temporary GraphML file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".graphml", delete=False
    ) as f:
        filepath = f.name

    try:
        nx.write_graphml(G, filepath)

        # Read with causaliq-core
        graph = read(filepath)
        assert graph is not None
        assert isinstance(graph, DAG)
        assert len(graph.nodes) == 3
        assert set(graph.nodes) == {"X", "Y", "Z"}
    finally:
        Path(filepath).unlink(missing_ok=True)


# Test causaliq-core can read NetworkX-generated graph with many nodes.
def test_causaliq_reads_networkx_larger_dag() -> None:
    # Create a larger DAG in NetworkX
    G = nx.DiGraph()
    nodes = [f"V{i}" for i in range(10)]
    G.add_nodes_from(nodes)
    # Create chain: V0 -> V1 -> V2 -> ... -> V9
    for i in range(9):
        G.add_edge(f"V{i}", f"V{i+1}")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".graphml", delete=False
    ) as f:
        filepath = f.name

    try:
        nx.write_graphml(G, filepath)

        graph = read(filepath)
        assert graph is not None
        assert isinstance(graph, DAG)
        assert len(graph.nodes) == 10
        assert graph.is_DAG()
    finally:
        Path(filepath).unlink(missing_ok=True)


# Test causaliq-core can read NetworkX graph with node attributes.
def test_causaliq_reads_networkx_with_node_attrs() -> None:
    G = nx.DiGraph()
    G.add_node("A", label="Node A", weight=1.0)
    G.add_node("B", label="Node B", weight=2.0)
    G.add_edge("A", "B")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".graphml", delete=False
    ) as f:
        filepath = f.name

    try:
        nx.write_graphml(G, filepath)

        # Our reader should handle extra attributes gracefully
        graph = read(filepath)
        assert graph is not None
        assert isinstance(graph, DAG)
        assert len(graph.nodes) == 2
        assert set(graph.nodes) == {"A", "B"}
    finally:
        Path(filepath).unlink(missing_ok=True)


# Test causaliq-core can read NetworkX graph with edge attributes.
def test_causaliq_reads_networkx_with_edge_attrs() -> None:
    G = nx.DiGraph()
    G.add_nodes_from(["A", "B", "C"])
    G.add_edge("A", "B", weight=0.5)
    G.add_edge("B", "C", weight=0.8)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".graphml", delete=False
    ) as f:
        filepath = f.name

    try:
        nx.write_graphml(G, filepath)

        graph = read(filepath)
        assert graph is not None
        assert isinstance(graph, DAG)
        assert len(graph.nodes) == 3
    finally:
        Path(filepath).unlink(missing_ok=True)


# =============================================================================
# Round-trip tests: causaliq -> NetworkX -> causaliq
# =============================================================================


# Test round-trip: read our file, write with NetworkX, read back.
def test_roundtrip_via_networkx() -> None:
    # Read original with causaliq-core
    original_path = str(TEST_DATA_DIR / "abc.graphml")
    original = read(original_path)

    # Read same file with NetworkX and write to new file
    G = nx.read_graphml(original_path)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".graphml", delete=False
    ) as f:
        filepath = f.name

    try:
        nx.write_graphml(G, filepath)

        # Read the NetworkX-written file with causaliq-core
        roundtrip = read(filepath)

        # Verify structure is preserved
        assert set(roundtrip.nodes) == set(original.nodes)
        assert len(roundtrip.nodes) == len(original.nodes)
    finally:
        Path(filepath).unlink(missing_ok=True)


# Test round-trip preserves Asia network structure.
def test_roundtrip_asia_via_networkx() -> None:
    original_path = str(TEST_DATA_DIR / "asia.graphml")
    original = read(original_path)

    G = nx.read_graphml(original_path)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".graphml", delete=False
    ) as f:
        filepath = f.name

    try:
        nx.write_graphml(G, filepath)
        roundtrip = read(filepath)

        assert set(roundtrip.nodes) == set(original.nodes)
        assert isinstance(roundtrip, DAG)
    finally:
        Path(filepath).unlink(missing_ok=True)
