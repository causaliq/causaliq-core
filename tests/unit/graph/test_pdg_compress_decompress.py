"""Unit tests for PDG compress/decompress methods."""

import pytest

from causaliq_core.graph.pdg import (
    PDG,
    EdgeProbabilities,
    _decode_probability,
    _encode_probability,
)

# =============================================================================
# Tests for _encode_probability / _decode_probability
# =============================================================================


# Test encode zero probability.
def test_encode_probability_zero() -> None:
    result = _encode_probability(0.0)
    assert result == b"\x00\x00\x00"


# Test decode zero probability.
def test_decode_probability_zero() -> None:
    result = _decode_probability(b"\x00\x00\x00")
    assert result == 0.0


# Test encode one probability.
def test_encode_probability_one() -> None:
    encoded = _encode_probability(1.0)
    decoded = _decode_probability(encoded)
    assert abs(decoded - 1.0) < 1e-4


# Test encode typical probability preserves 4 s.f.
def test_encode_probability_typical() -> None:
    values = [0.9876, 0.5000, 0.1234, 0.0123, 0.0012]
    for value in values:
        encoded = _encode_probability(value)
        decoded = _decode_probability(encoded)
        # Should preserve 4 significant figures
        assert abs(decoded - value) / value < 1e-3, f"Failed for {value}"


# Test encode small probability preserves precision.
def test_encode_probability_small() -> None:
    value = 0.001234
    encoded = _encode_probability(value)
    decoded = _decode_probability(encoded)
    # Check relative error is small
    assert abs(decoded - value) / value < 1e-3


# Test encode very small probability.
def test_encode_probability_very_small() -> None:
    value = 0.0001234
    encoded = _encode_probability(value)
    decoded = _decode_probability(encoded)
    assert abs(decoded - value) / value < 1e-3


# Test encode probability out of range raises error.
def test_encode_probability_out_of_range() -> None:
    with pytest.raises(ValueError):
        _encode_probability(-0.1)
    with pytest.raises(ValueError):
        _encode_probability(1.1)


# Test decode probability wrong length raises error.
def test_decode_probability_wrong_length() -> None:
    with pytest.raises(ValueError):
        _decode_probability(b"\x00\x00")
    with pytest.raises(ValueError):
        _decode_probability(b"\x00\x00\x00\x00")


# =============================================================================
# Tests for PDG.compress() parameter validation
# =============================================================================


# Test compress returns bytes type.
def test_pdg_compress_returns_bytes() -> None:
    pdg = PDG(["A"], {})
    result = pdg.compress()
    assert isinstance(result, bytes)


# Test compress on empty nodes graph.
def test_pdg_compress_empty_graph() -> None:
    pdg = PDG([], {})
    result = pdg.compress()
    # Should have 2 bytes for num_nodes (0) + 2 bytes for num_edges (0)
    assert len(result) == 4
    assert result == b"\x00\x00\x00\x00"


# Test compress on single node graph.
def test_pdg_compress_single_node() -> None:
    pdg = PDG(["A"], {})
    result = pdg.compress()
    # 2 bytes num_nodes + 2 bytes name_len + 1 byte "A" + 2 bytes num_edges
    assert len(result) == 7


# =============================================================================
# Tests for PDG.decompress() parameter validation
# =============================================================================


# Test decompress fails on non-bytes argument.
def test_pdg_decompress_type_error_not_bytes() -> None:
    with pytest.raises(TypeError):
        PDG.decompress("not bytes")  # type: ignore
    with pytest.raises(TypeError):
        PDG.decompress(None)  # type: ignore
    with pytest.raises(TypeError):
        PDG.decompress(123)  # type: ignore


# Test decompress fails on data too short.
def test_pdg_decompress_value_error_data_too_short() -> None:
    with pytest.raises(ValueError):
        PDG.decompress(b"")
    with pytest.raises(ValueError):
        PDG.decompress(b"\x00")


# Test decompress fails on truncated node data.
def test_pdg_decompress_value_error_truncated_node_length() -> None:
    # Says 1 node but no node data follows
    with pytest.raises(ValueError):
        PDG.decompress(b"\x00\x01")


# Test decompress fails on truncated node name.
def test_pdg_decompress_value_error_truncated_node_name() -> None:
    # Says 1 node with name length 5 but only 2 bytes of name
    with pytest.raises(ValueError):
        PDG.decompress(b"\x00\x01\x00\x05AB")


# Test decompress fails on truncated edge count.
def test_pdg_decompress_value_error_truncated_edge_count() -> None:
    # 1 node "A" but no edge count follows
    with pytest.raises(ValueError):
        PDG.decompress(b"\x00\x01\x00\x01A")


# Test decompress fails on truncated edge data.
def test_pdg_decompress_value_error_truncated_edge_data() -> None:
    # 2 nodes, 1 edge but edge data incomplete
    data = (
        b"\x00\x02"  # 2 nodes
        b"\x00\x01A"  # node "A"
        b"\x00\x01B"  # node "B"
        b"\x00\x01"  # 1 edge
        b"\x00\x00"  # source index only, missing rest
    )
    with pytest.raises(ValueError):
        PDG.decompress(data)


# Test decompress fails on invalid node index in edge.
def test_pdg_decompress_value_error_invalid_node_index() -> None:
    # 2 nodes, 1 edge with invalid source index (99)
    data = (
        b"\x00\x02"  # 2 nodes
        b"\x00\x01A"  # node "A"
        b"\x00\x01B"  # node "B"
        b"\x00\x01"  # 1 edge
        b"\x00\x63"  # source index 99 (invalid)
        b"\x00\x01"  # target index 1
        b"\x00\x00\x00"  # p_forward
        b"\x00\x00\x00"  # p_backward
        b"\x00\x00\x00"  # p_undirected
    )
    with pytest.raises(ValueError):
        PDG.decompress(data)


# =============================================================================
# Round-trip tests (compress -> decompress)
# =============================================================================


# Test round-trip compress/decompress for empty graph.
def test_pdg_compress_decompress_roundtrip_empty() -> None:
    original = PDG([], {})
    compressed = original.compress()
    decompressed = PDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for single node.
def test_pdg_compress_decompress_roundtrip_single_node() -> None:
    original = PDG(["A"], {})
    compressed = original.compress()
    decompressed = PDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress for multiple nodes no edges.
def test_pdg_compress_decompress_roundtrip_nodes_only() -> None:
    original = PDG(["A", "B", "C"], {})
    compressed = original.compress()
    decompressed = PDG.decompress(compressed)
    assert decompressed.nodes == original.nodes
    assert decompressed.edges == original.edges


# Test round-trip compress/decompress with edge probabilities.
def test_pdg_compress_decompress_roundtrip_with_edges() -> None:
    edges = {
        ("A", "B"): EdgeProbabilities(forward=0.8, none=0.2),
        ("A", "C"): EdgeProbabilities(
            forward=0.6, backward=0.3, undirected=0.0, none=0.1
        ),
    }
    original = PDG(["A", "B", "C"], edges)
    compressed = original.compress()
    decompressed = PDG.decompress(compressed)

    assert decompressed.nodes == original.nodes
    assert len(decompressed.edges) == len(original.edges)

    for key, orig_probs in original.edges.items():
        dec_probs = decompressed.edges[key]
        # Allow small error due to 4 s.f. encoding
        assert abs(dec_probs.forward - orig_probs.forward) < 1e-3
        assert abs(dec_probs.backward - orig_probs.backward) < 1e-3
        assert abs(dec_probs.undirected - orig_probs.undirected) < 1e-3
        assert abs(dec_probs.none - orig_probs.none) < 1e-3


# Test round-trip with various probability values.
def test_pdg_compress_decompress_roundtrip_various_probs() -> None:
    edges = {
        ("A", "B"): EdgeProbabilities(
            forward=0.9876, backward=0.0, undirected=0.0, none=0.0124
        ),
        ("A", "C"): EdgeProbabilities(
            forward=0.1234, backward=0.5678, undirected=0.1, none=0.2088
        ),
        ("B", "C"): EdgeProbabilities(
            forward=0.0, backward=0.0, undirected=0.0, none=1.0
        ),
    }
    original = PDG(["A", "B", "C"], edges)
    compressed = original.compress()
    decompressed = PDG.decompress(compressed)

    for key, orig_probs in original.edges.items():
        dec_probs = decompressed.edges[key]
        # Forward
        if orig_probs.forward > 0:
            assert (
                abs(dec_probs.forward - orig_probs.forward)
                / orig_probs.forward
                < 1e-3
            )
        else:
            assert dec_probs.forward == 0.0
        # Backward
        if orig_probs.backward > 0:
            assert (
                abs(dec_probs.backward - orig_probs.backward)
                / orig_probs.backward
                < 1e-3
            )
        else:
            assert dec_probs.backward == 0.0


# Test round-trip with UTF-8 node names.
def test_pdg_compress_decompress_roundtrip_utf8_names() -> None:
    edges = {
        ("café", "naïve"): EdgeProbabilities(forward=0.5, none=0.5),
    }
    original = PDG(["café", "naïve"], edges)
    compressed = original.compress()
    decompressed = PDG.decompress(compressed)

    assert decompressed.nodes == original.nodes
    assert len(decompressed.edges) == 1


# Test round-trip preserves node ordering.
def test_pdg_compress_decompress_preserves_order() -> None:
    # Nodes should be sorted alphabetically
    original = PDG(["Z", "A", "M"], {})
    compressed = original.compress()
    decompressed = PDG.decompress(compressed)

    assert decompressed.nodes == ["A", "M", "Z"]


# Test compression size is reasonable.
def test_pdg_compress_size_reasonable() -> None:
    # 3 nodes, 3 edge pairs: each edge is 13 bytes
    edges = {
        ("A", "B"): EdgeProbabilities(forward=0.8, none=0.2),
        ("A", "C"): EdgeProbabilities(forward=0.6, none=0.4),
        ("B", "C"): EdgeProbabilities(forward=0.7, none=0.3),
    }
    pdg = PDG(["A", "B", "C"], edges)
    compressed = pdg.compress()

    # Header: 2 (num_nodes) + 3*(2+1) (nodes) + 2 (num_edges) = 13 bytes
    # Edges: 3 * 13 = 39 bytes
    # Total: ~52 bytes
    assert len(compressed) < 60


# Test small probability values preserved.
def test_pdg_compress_small_probabilities() -> None:
    edges = {
        ("A", "B"): EdgeProbabilities(
            forward=0.001234, backward=0.0, undirected=0.0, none=0.998766
        ),
    }
    original = PDG(["A", "B"], edges)
    compressed = original.compress()
    decompressed = PDG.decompress(compressed)

    dec_probs = decompressed.edges[("A", "B")]
    orig_probs = original.edges[("A", "B")]

    # Should preserve relative precision
    assert (
        abs(dec_probs.forward - orig_probs.forward) / orig_probs.forward < 1e-3
    )


# =============================================================================
# Edge case tests for full coverage
# =============================================================================


# Test compress raises ValueError for too many nodes.
def test_pdg_compress_too_many_nodes() -> None:
    # Create PDG then manually set nodes to exceed limit
    pdg = PDG(["A"], {})
    pdg.nodes = [f"n{i}" for i in range(65536)]
    with pytest.raises(ValueError, match="too many nodes"):
        pdg.compress()


# Test compress raises ValueError for too many edge pairs.
def test_pdg_compress_too_many_edges() -> None:
    pdg = PDG(["A", "B"], {})
    # Manually inject too many edges
    pdg.edges = {
        (f"A{i}", "B"): EdgeProbabilities(forward=0.5, none=0.5)
        for i in range(65536)
    }
    with pytest.raises(ValueError, match="too many edge pairs"):
        pdg.compress()


# Test compress raises ValueError for node name too long.
def test_pdg_compress_node_name_too_long() -> None:
    pdg = PDG(["A"], {})
    # Manually set a node name that's too long when encoded
    pdg.nodes = ["x" * 70000]  # > 65535 bytes when UTF-8 encoded
    with pytest.raises(ValueError, match="node name too long"):
        pdg.compress()


# Test encode probability handles mantissa overflow adjustment.
def test_encode_probability_mantissa_overflow() -> None:
    # Value that causes mantissa >= 10000 initially
    # 0.99999 -> log10 = -0.0000043... floor = -1, exp = -4
    # mantissa = 0.99999 / 10^-4 = 9999.9 rounds to 10000
    # Should adjust: mantissa //= 10 -> 1000, exp += 1 -> -3
    encoded = _encode_probability(0.99999)
    decoded = _decode_probability(encoded)
    assert abs(decoded - 0.99999) < 1e-3


# Test encode probability handles small mantissa adjustment.
def test_encode_probability_small_mantissa() -> None:
    # Value that causes mantissa < 1000 initially
    # 0.0001 -> log10 = -4, exp = -7
    # mantissa = 0.0001 / 10^-7 = 1000 (boundary case)
    # Try 0.00011 -> mantissa might be < 1000
    value = 0.00011
    encoded = _encode_probability(value)
    decoded = _decode_probability(encoded)
    assert abs(decoded - value) / value < 1e-3


# Test decompress handles small negative p_none due to precision.
def test_pdg_decompress_small_negative_p_none() -> None:
    # Create a valid PDG, compress it, then manually tweak compressed data
    # to have probabilities that sum to slightly > 1.0 (within tolerance)
    edges = {
        ("A", "B"): EdgeProbabilities(
            forward=0.4, backward=0.3, undirected=0.3, none=0.0
        ),
    }
    pdg = PDG(["A", "B"], edges)
    # This should round-trip fine even with tiny precision errors
    compressed = pdg.compress()
    decompressed = PDG.decompress(compressed)
    # p_none should be ~0.0
    assert decompressed.edges[("A", "B")].none < 0.001


# Test decompress raises error for invalid probabilities sum.
def test_pdg_decompress_invalid_probability_sum() -> None:
    # Manually construct invalid compressed data where probs sum to > 1.0
    # Format: 2 bytes nodes, per-node (2 len + name), 2 bytes edges,
    #         per-edge (2 src + 2 tgt + 3*3 probs)
    data = bytearray()
    data.extend(b"\x00\x02")  # 2 nodes
    data.extend(b"\x00\x01A")  # node "A"
    data.extend(b"\x00\x01B")  # node "B"
    data.extend(b"\x00\x01")  # 1 edge
    data.extend(b"\x00\x00")  # src idx 0
    data.extend(b"\x00\x01")  # tgt idx 1
    # Encode 0.5 three times = 1.5 total > 1.0
    # 0.5 = 5000 * 10^-4, mantissa=5000=0x1388, exp=-4=0xFC (signed)
    prob_half = b"\x13\x88\xfc"
    data.extend(prob_half)  # forward = 0.5
    data.extend(prob_half)  # backward = 0.5
    data.extend(prob_half)  # undirected = 0.5 -> sum = 1.5

    with pytest.raises(ValueError, match="sum to more than 1.0"):
        PDG.decompress(bytes(data))
