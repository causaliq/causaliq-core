"""Unit tests for SDG encode/decode methods."""

import pytest

from causaliq_core.graph import DAG, PDAG, SDG

# =============================================================================
# Tests for SDG.encode() parameter validation
# =============================================================================


# Test encode returns bytes type.
def test_sdg_encode_returns_bytes() -> None:
    sdg = SDG(["A"], [])
    result = sdg.encode()
    assert isinstance(result, bytes)


# Test encode on empty nodes graph.
def test_sdg_encode_empty_graph() -> None:
    sdg = SDG([], [])
    result = sdg.encode()
    # Should have 2 bytes for num_nodes (0) + 2 bytes for num_edges (0)
    assert len(result) == 4
    assert result == b"\x00\x00\x00\x00"


# Test encode on single node graph.
def test_sdg_encode_single_node() -> None:
    sdg = SDG(["A"], [])
    result = sdg.encode()
    # 2 bytes num_nodes + 2 bytes name_len + 1 byte "A" + 2 bytes num_edges
    assert len(result) == 7


# =============================================================================
# Tests for SDG.decode() parameter validation
# =============================================================================


# Test decode fails on non-bytes argument.
def test_sdg_decode_type_error_not_bytes() -> None:
    with pytest.raises(TypeError):
        SDG.decode("not bytes")
    with pytest.raises(TypeError):
        SDG.decode(None)
    with pytest.raises(TypeError):
        SDG.decode(123)
    with pytest.raises(TypeError):
        SDG.decode(["bytes"])


# Test decode fails on data too short.
def test_sdg_decode_value_error_data_too_short() -> None:
    with pytest.raises(ValueError):
        SDG.decode(b"")
    with pytest.raises(ValueError):
        SDG.decode(b"\x00")


# Test decode fails on truncated node data.
def test_sdg_decode_value_error_truncated_node_length() -> None:
    # Says 1 node but no node data follows
    with pytest.raises(ValueError):
        SDG.decode(b"\x00\x01")


# Test decode fails on truncated node name.
def test_sdg_decode_value_error_truncated_node_name() -> None:
    # Says 1 node with name length 5 but only 2 bytes of name
    with pytest.raises(ValueError):
        SDG.decode(b"\x00\x01\x00\x05AB")


# Test decode fails on truncated edge count.
def test_sdg_decode_value_error_truncated_edge_count() -> None:
    # 1 node "A" but no edge count follows
    with pytest.raises(ValueError):
        SDG.decode(b"\x00\x01\x00\x01A")


# Test decode fails on truncated edge data.
def test_sdg_decode_value_error_truncated_edge_data() -> None:
    # 2 nodes, 1 edge but edge data incomplete
    data = (
        b"\x00\x02"  # 2 nodes
        b"\x00\x01A"  # node "A"
        b"\x00\x01B"  # node "B"
        b"\x00\x01"  # 1 edge
        b"\x00\x00"  # source index only, missing target and type
    )
    with pytest.raises(ValueError):
        SDG.decode(data)


# Test decode fails on invalid node index in edge.
def test_sdg_decode_value_error_invalid_node_index() -> None:
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
        SDG.decode(data)


# Test decode fails on invalid edge type.
def test_sdg_decode_value_error_invalid_edge_type() -> None:
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
        SDG.decode(data)


# =============================================================================
# Round-trip tests (encode -> decode)
# =============================================================================


# Test round-trip for empty graph.
def test_sdg_encode_decode_roundtrip_empty() -> None:
    original = SDG([], [])
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip for single node.
def test_sdg_encode_decode_roundtrip_single_node() -> None:
    original = SDG(["A"], [])
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip for simple directed edge.
def test_sdg_encode_decode_roundtrip_directed() -> None:
    original = SDG(["A", "B"], [("A", "->", "B")])
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip for undirected edge.
def test_sdg_encode_decode_roundtrip_undirected() -> None:
    original = SDG(["A", "B"], [("A", "-", "B")])
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip for bidirected edge.
def test_sdg_encode_decode_roundtrip_bidirected() -> None:
    original = SDG(["A", "B"], [("A", "<->", "B")])
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip for semidirected edge.
def test_sdg_encode_decode_roundtrip_semidirected() -> None:
    original = SDG(["A", "B"], [("A", "o->", "B")])
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip for semiundirected edge.
def test_sdg_encode_decode_roundtrip_semiundirected() -> None:
    original = SDG(["A", "B"], [("A", "o-", "B")])
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip for nondirected edge.
def test_sdg_encode_decode_roundtrip_nondirected() -> None:
    original = SDG(["A", "B"], [("A", "o-o", "B")])
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip for multi-node graph.
def test_sdg_encode_decode_roundtrip_multi_node() -> None:
    original = SDG(
        ["A", "B", "C", "D"],
        [
            ("A", "->", "B"),
            ("B", "->", "C"),
            ("C", "->", "D"),
            ("A", "->", "D"),
        ],
    )
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip for mixed edge types.
def test_sdg_encode_decode_roundtrip_mixed_edges() -> None:
    original = SDG(
        ["A", "B", "C", "D"],
        [
            ("A", "->", "B"),
            ("B", "-", "C"),
            ("C", "<->", "D"),
        ],
    )
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip for graph with all edge types.
def test_sdg_encode_decode_roundtrip_all_edge_types() -> None:
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
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip preserves node ordering (alphabetical).
def test_sdg_encode_decode_roundtrip_node_order() -> None:
    # SDG sorts nodes alphabetically
    original = SDG(["Z", "M", "A", "B"], [("A", "->", "Z")])
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == ["A", "B", "M", "Z"]
    assert decoded.nodes == original.nodes


# Test round-trip with Unicode node names.
def test_sdg_encode_decode_roundtrip_unicode() -> None:
    original = SDG(["α", "β", "γ"], [("α", "->", "β"), ("β", "->", "γ")])
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip with longer node names.
def test_sdg_encode_decode_roundtrip_long_names() -> None:
    original = SDG(
        ["variable_one", "variable_two", "variable_three"],
        [("variable_one", "->", "variable_two")],
    )
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# =============================================================================
# Tests for DAG and PDAG compatibility
# =============================================================================


# Test round-trip for DAG returns SDG (since decode returns SDG).
def test_sdg_encode_decode_dag_returns_sdg() -> None:
    original = DAG(["A", "B", "C"], [("A", "->", "B"), ("B", "->", "C")])
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert isinstance(decoded, SDG)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# Test round-trip for PDAG returns SDG.
def test_sdg_encode_decode_pdag_returns_sdg() -> None:
    original = PDAG(["A", "B", "C"], [("A", "->", "B"), ("B", "-", "C")])
    encoded = original.encode()
    decoded = SDG.decode(encoded)
    assert isinstance(decoded, SDG)
    assert decoded.nodes == original.nodes
    assert decoded.edges == original.edges


# =============================================================================
# Tests for encoding size efficiency
# =============================================================================


# Test encoding is compact for simple graphs.
def test_sdg_encode_size_simple() -> None:
    # 2 nodes, 1 edge
    # Expected: 2 (num_nodes) + 2+1 (A) + 2+1 (B) + 2 (num_edges) + 5 (edge)
    # = 2 + 3 + 3 + 2 + 5 = 15 bytes
    sdg = SDG(["A", "B"], [("A", "->", "B")])
    encoded = sdg.encode()
    assert len(encoded) == 15


# Test encoding size scales with node names.
def test_sdg_encode_size_long_names() -> None:
    sdg1 = SDG(["A", "B"], [])
    sdg2 = SDG(["AAAA", "BBBB"], [])
    # Longer names should result in larger encoding
    assert len(sdg2.encode()) > len(sdg1.encode())


# =============================================================================
# Tests for encoding limit validation
# =============================================================================


# Test encode fails when node name too long (> 65535 bytes).
def test_sdg_encode_value_error_node_name_too_long(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdg = SDG(["A"], [])
    # Monkeypatch the node to have a very long name after construction
    sdg.nodes = ["x" * 65536]
    with pytest.raises(ValueError, match="node name too long"):
        sdg.encode()


# Test encode fails when too many nodes (> 65535).
def test_sdg_encode_value_error_too_many_nodes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sdg = SDG(["A"], [])
    # Monkeypatch to simulate too many nodes
    sdg.nodes = [f"N{i}" for i in range(65536)]
    with pytest.raises(ValueError, match="too many nodes"):
        sdg.encode()


# Test encode fails when too many edges (> 65535).
def test_sdg_encode_value_error_too_many_edges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from causaliq_core.graph import EdgeType

    sdg = SDG(["A", "B"], [("A", "->", "B")])
    # Monkeypatch to simulate too many edges
    sdg.edges = {(f"N{i}", f"N{i+1}"): EdgeType.DIRECTED for i in range(65536)}
    with pytest.raises(ValueError, match="too many edges"):
        sdg.encode()
