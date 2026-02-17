"""Unit tests for SDG compress/decompress methods."""

import pytest

from causaliq_core.graph import DAG, PDAG, SDG

# =============================================================================
# Tests for SDG.compress() parameter validation
# =============================================================================


# Test compress returns bytes type.
def test_sdg_compress_returns_bytes() -> None:
    sdg = SDG(["A"], [])
    result = sdg.compress()
    assert isinstance(result, bytes)


# Test compress on empty nodes graph.
def test_sdg_compress_empty_graph() -> None:
    sdg = SDG([], [])
    result = sdg.compress()
    # Should have 2 bytes for num_nodes (0) + 2 bytes for num_edges (0)
    assert len(result) == 4
    assert result == b"\x00\x00\x00\x00"


# Test compress on single node graph.
def test_sdg_compress_single_node() -> None:
    sdg = SDG(["A"], [])
    result = sdg.compress()
    # 2 bytes num_nodes + 2 bytes name_len + 1 byte "A" + 2 bytes num_edges
    assert len(result) == 7


# =============================================================================
# Tests for SDG.decompress() parameter validation
# =============================================================================


# Test decompress fails on non-bytes argument.
def test_sdg_decompress_type_error_not_bytes() -> None:
    with pytest.raises(TypeError):
        SDG.decompress("not bytes")
    with pytest.raises(TypeError):
        SDG.decompress(None)
    with pytest.raises(TypeError):
        SDG.decompress(123)
    with pytest.raises(TypeError):
        SDG.decompress(["bytes"])


# Test decompress fails on data too short.
def test_sdg_decompress_value_error_data_too_short() -> None:
    with pytest.raises(ValueError):
        SDG.decompress(b"")
    with pytest.raises(ValueError):
        SDG.decompress(b"\x00")


# Test decompress fails on truncated node data.
def test_sdg_decompress_value_error_truncated_node_length() -> None:
    # Says 1 node but no node data follows
    with pytest.raises(ValueError):
        SDG.decompress(b"\x00\x01")


# Test decompress fails on truncated node name.
def test_sdg_decompress_value_error_truncated_node_name() -> None:
    # Says 1 node with name length 5 but only 2 bytes of name
    with pytest.raises(ValueError):
        SDG.decompress(b"\x00\x01\x00\x05AB")


# Test decompress fails on truncated edge count.
def test_sdg_decompress_value_error_truncated_edge_count() -> None:
    # 1 node "A" but no edge count follows
    with pytest.raises(ValueError):
        SDG.decompress(b"\x00\x01\x00\x01A")


# Test decompress fails on truncated edge data.
def test_sdg_decompress_value_error_truncated_edge_data() -> None:
    # 2 nodes, 1 edge but edge data incomplete
    data = (
        b"\x00\x02"  # 2 nodes
        b"\x00\x01A"  # node "A"
        b"\x00\x01B"  # node "B"
        b"\x00\x01"  # 1 edge
        b"\x00\x00"  # source index only, missing target and type
    )
    with pytest.raises(ValueError):
        SDG.decompress(data)


# Test decompress fails on invalid node index in edge.
def test_sdg_decompress_value_error_invalid_node_index() -> None:
    # 2 nodes, 1 edge with invalid source index (99)
    data = (
        b"\x00\x02"  # 2 nodes
        b"\x00\x01A"  # node "A"
        b"\x00\x01B"  # node "B"
        b"\x00\x01"  # 1 edge
        b"\x00\x63"  # source index 99 (invalid)
        b"\x00\x01"  # target index 1
        b"\x01"  # edge type DIRECTED
    )
    with pytest.raises(ValueError):
        SDG.decompress(data)


# Test decompress fails on invalid edge type.
def test_sdg_decompress_value_error_invalid_edge_type() -> None:
    # 2 nodes, 1 edge with invalid edge type (99)
    data = (
        b"\x00\x02"  # 2 nodes
        b"\x00\x01A"  # node "A"
        b"\x00\x01B"  # node "B"
        b"\x00\x01"  # 1 edge
        b"\x00\x00"  # source index 0
        b"\x00\x01"  # target index 1
        b"\x63"  # edge type 99 (invalid)
    )
    with pytest.raises(ValueError):
        SDG.decompress(data)


# =============================================================================
# Round-trip tests (compress -> decompress)
# =============================================================================


# Test round-trip compress/decompress for empty graph.
def test_sdg_compress_decompress_roundtrip_empty() -> None:
    original = SDG([], [])
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for single node.
def test_sdg_compress_decompress_roundtrip_single_node() -> None:
    original = SDG(["A"], [])
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for simple directed edge.
def test_sdg_compress_decompress_roundtrip_directed() -> None:
    original = SDG(["A", "B"], [("A", "->", "B")])
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for undirected edge.
def test_sdg_compress_decompress_roundtrip_undirected() -> None:
    original = SDG(["A", "B"], [("A", "-", "B")])
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for bidirected edge.
def test_sdg_compress_decompress_roundtrip_bidirected() -> None:
    original = SDG(["A", "B"], [("A", "<->", "B")])
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for semidirected edge.
def test_sdg_compress_decompress_roundtrip_semidirected() -> None:
    original = SDG(["A", "B"], [("A", "o->", "B")])
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for semiundirected edge.
def test_sdg_compress_decompress_roundtrip_semiundirected() -> None:
    original = SDG(["A", "B"], [("A", "o-", "B")])
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for nondirected edge.
def test_sdg_compress_decompress_roundtrip_nondirected() -> None:
    original = SDG(["A", "B"], [("A", "o-o", "B")])
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for multi-node graph.
def test_sdg_compress_decompress_roundtrip_multi_node() -> None:
    original = SDG(
        ["A", "B", "C", "D"],
        [
            ("A", "->", "B"),
            ("B", "->", "C"),
            ("C", "->", "D"),
            ("A", "->", "D"),
        ],
    )
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for mixed edge types.
def test_sdg_compress_decompress_roundtrip_mixed_edges() -> None:
    original = SDG(
        ["A", "B", "C", "D"],
        [
            ("A", "->", "B"),
            ("B", "-", "C"),
            ("C", "<->", "D"),
        ],
    )
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for graph with all edge types.
def test_sdg_compress_decompress_roundtrip_all_edge_types() -> None:
    original = SDG(
        ["A", "B", "C", "D", "E", "F", "G"],
        [
            ("A", "->", "B"),  # DIRECTED
            ("B", "-", "C"),  # UNDIRECTED
            ("C", "<->", "D"),  # BIDIRECTED
            ("D", "o->", "E"),  # SEMIDIRECTED
            ("E", "o-o", "F"),  # NONDIRECTED
            ("F", "o-", "G"),  # SEMIUNDIRECTED
        ],
    )
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip preserves node ordering (alphabetical).
def test_sdg_compress_decompress_roundtrip_node_order() -> None:
    # SDG sorts nodes alphabetically
    original = SDG(["Z", "M", "A", "B"], [("A", "->", "Z")])
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == ["A", "B", "M", "Z"]
    assert decompressed.nodes == original.nodes


# Test round-trip with Unicode node names.
def test_sdg_compress_decompress_roundtrip_unicode() -> None:
    original = SDG(["α", "β", "γ"], [("α", "->", "β"), ("β", "->", "γ")])
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip with longer node names.
def test_sdg_compress_decompress_roundtrip_long_names() -> None:
    original = SDG(
        ["variable_one", "variable_two", "variable_three"],
        [("variable_one", "->", "variable_two")],
    )
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# =============================================================================
# Tests for DAG and PDAG compatibility
# =============================================================================


# Test round-trip compress/decompress for DAG returns SDG
def test_sdg_compress_decompress_dag_returns_sdg() -> None:
    original = DAG(["A", "B", "C"], [("A", "->", "B"), ("B", "->", "C")])
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert isinstance(decompressed, SDG)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for PDAG returns SDG.
def test_sdg_compress_decompress_pdag_returns_sdg() -> None:
    original = PDAG(["A", "B", "C"], [("A", "->", "B"), ("B", "-", "C")])
    compressed = original.compress()
    decompressed = SDG.decompress(compressed)
    assert isinstance(decompressed, SDG)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# =============================================================================
# Tests for compression size efficiency
# =============================================================================


# Test compression is compact for simple graphs.
def test_sdg_compress_size_simple() -> None:
    # 2 nodes, 1 edge
    # Expected: 2 (num_nodes) + 2+1 (A) + 2+1 (B) + 2 (num_edges) + 5 (edge)
    # = 2 + 3 + 3 + 2 + 5 = 15 bytes
    sdg = SDG(["A", "B"], [("A", "->", "B")])
    compressed = sdg.compress()
    assert len(compressed) == 15


# Test compression size scales with node names.
def test_sdg_compress_size_long_names() -> None:
    sdg1 = SDG(["A", "B"], [])
    sdg2 = SDG(["AAAA", "BBBB"], [])
    # Longer names should result in larger encoding
    assert len(sdg2.compress()) > len(sdg1.compress())


# =============================================================================
# Tests for compression limit validation
# =============================================================================


# Test compress fails when node name too long (> 65535 bytes).
def test_sdg_compress_value_error_node_name_too_long(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdg = SDG(["A"], [])
    # Monkeypatch the node to have a very long name after construction
    sdg.nodes = ["x" * 65536]
    with pytest.raises(ValueError, match="node name too long"):
        sdg.compress()


# Test compress fails when too many nodes (> 65535).
def test_sdg_compress_value_error_too_many_nodes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdg = SDG(["A"], [])
    # Monkeypatch to simulate too many nodes
    sdg.nodes = [f"N{i}" for i in range(65536)]
    with pytest.raises(ValueError, match="too many nodes"):
        sdg.compress()


# Test compress fails when too many edges (> 65535).
def test_sdg_compress_value_error_too_many_edges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from causaliq_core.graph import EdgeType

    sdg = SDG(["A", "B"], [("A", "->", "B")])
    # Monkeypatch to simulate too many edges
    sdg.edges = {(f"N{i}", f"N{i+1}"): EdgeType.DIRECTED for i in range(65536)}
    with pytest.raises(ValueError, match="too many edges"):
        sdg.compress()
