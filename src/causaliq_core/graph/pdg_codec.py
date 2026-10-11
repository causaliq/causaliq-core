"""
Compact binary codec for Probabilistic Dependency Graphs (PDG).

The codec encodes a PDG to a compact binary representation and back. It
works directly with node names and probability tuples so that it does not
need to depend on the PDG class itself.

Probabilities are encoded with 4 significant figures using a mantissa and
exponent format: value = mantissa x 10^exponent. The p_none value is
derived from the constraint that the probabilities sum to 1.0.
"""

from typing import Dict, List, Tuple

# Type alias for (forward, backward, undirected, none) probabilities
EdgeProbs = Tuple[float, float, float, float]

# Bytes used by each encoded probability value
PROBABILITY_BYTES = 3

# Bytes used by each encoded edge: 2 node indexes + 3 probabilities
EDGE_BYTES = 13


def _significant_figures(value: float) -> Tuple[int, int]:
    """Return the mantissa and exponent giving 4 significant figures.

    Args:
        value: Probability value in the range (0.0, 1.0).

    Returns:
        Tuple of (mantissa, exponent) with mantissa in [1000, 9999].
    """
    import math

    log_val = math.log10(value)
    # Exponent to get mantissa in [1000, 9999]
    exponent = int(math.floor(log_val)) - 3

    # Calculate mantissa
    mantissa = round(value / (10**exponent))

    # Ensure mantissa is in valid range
    if mantissa >= 10000:
        mantissa = mantissa // 10
        exponent += 1
    elif mantissa < 1000 and mantissa > 0:  # pragma: no cover
        mantissa = mantissa * 10
        exponent -= 1

    return mantissa, exponent


def _encode_probability(value: float) -> bytes:
    """Encode probability to 3 bytes with 4 significant figures.

    Format: 2 bytes mantissa (uint16) + 1 byte exponent (int8).
    Value = mantissa × 10^exponent.

    Args:
        value: Probability value in range [0.0, 1.0].

    Returns:
        3-byte encoding.

    Example:
        >>> _encode_probability(0.9876)  # mantissa=9876, exp=-4
        >>> _encode_probability(0.001234)  # mantissa=1234, exp=-6
        >>> _encode_probability(0.0)  # mantissa=0, exp=0
    """
    if value == 0.0:
        return b"\x00\x00\x00"

    if value < 0 or value > 1.0:
        raise ValueError(f"Probability must be in [0, 1], got {value}")

    # Special case for exactly 1.0
    if value == 1.0:
        # 1.0 = 1000 × 10^-3
        mantissa = 1000
        exponent = -3
        return mantissa.to_bytes(2, "big") + exponent.to_bytes(
            1, "big", signed=True
        )

    # Find exponent: we want mantissa in range [1000, 9999] for 4 s.f.
    mantissa, exponent = _significant_figures(value)

    # Clamp mantissa to uint16 range
    mantissa = max(0, min(9999, mantissa))

    # Clamp exponent to int8 range
    exponent = max(-128, min(127, exponent))

    return bytes(
        mantissa.to_bytes(2, "big") + exponent.to_bytes(1, "big", signed=True)
    )


def _decode_probability(data: bytes) -> float:
    """Decode probability from 3-byte format.

    Args:
        data: 3 bytes (mantissa uint16 + exponent int8).

    Returns:
        Decoded probability value.
    """
    if len(data) != 3:
        raise ValueError("Probability encoding must be 3 bytes")

    mantissa = int.from_bytes(data[0:2], "big")
    exponent = int.from_bytes(data[2:3], "big", signed=True)

    if mantissa == 0:
        return 0.0

    return float(mantissa * (10**exponent))


def _encode_node_name(node: str) -> bytes:
    """Return the length-prefixed UTF-8 encoding of a node name.

    Args:
        node: Node name to encode.

    Returns:
        Two-byte length followed by the encoded name.

    Raises:
        ValueError: If the encoded name is longer than 65535 bytes.
    """
    name_bytes = node.encode("utf-8")
    if len(name_bytes) > 65535:
        raise ValueError("PDG.compress() node name too long")
    return len(name_bytes).to_bytes(2, "big") + name_bytes


def _encode_edge(
    node_index: Dict[str, int],
    source: str,
    target: str,
    probs: EdgeProbs,
) -> bytes:
    """Return the encoded form of one node pair's probabilities.

    Args:
        node_index: Mapping of node name to node index.
        source: Source node name.
        target: Target node name.
        probs: Edge probabilities to encode.

    Returns:
        Compact binary representation of the edge pair.
    """
    data = node_index[source].to_bytes(2, "big")
    data += node_index[target].to_bytes(2, "big")
    data += _encode_probability(probs[0])
    data += _encode_probability(probs[1])
    data += _encode_probability(probs[2])
    return data


def encode_pdg(
    nodes: List[str], edges: Dict[Tuple[str, str], EdgeProbs]
) -> bytes:
    """Encode a PDG's nodes and edge probabilities to compact binary.

    Format:

    - 2 bytes: number of nodes (uint16, big-endian)
    - For each node: 2 bytes name length + UTF-8 encoded name
    - 2 bytes: number of edge pairs with probabilities (uint16)
    - For each edge pair: 2 bytes source index, 2 bytes target index and
      3 bytes for each of p_forward, p_backward and p_undirected

    Args:
        nodes: Node names in graph order.
        edges: Edge probabilities, keyed by (source, target).

    Returns:
        Compact binary representation of the PDG.

    Raises:
        ValueError: If the graph has more than 65535 nodes or edge pairs,
            or if a node name is too long.
    """
    if len(nodes) > 65535:
        raise ValueError("PDG.compress() graph has too many nodes")
    if len(edges) > 65535:
        raise ValueError("PDG.compress() graph has too many edge pairs")

    # Build node index for edge compression
    node_index = {node: i for i, node in enumerate(nodes)}

    # Compress number of nodes
    data = len(nodes).to_bytes(2, "big")

    # Compress each node name
    for node in nodes:
        data += _encode_node_name(node)

    # Compress number of edge pairs
    data += len(edges).to_bytes(2, "big")

    # Compress each edge pair (source idx, target idx, 3 probabilities)
    for (source, target), probs in edges.items():
        data += _encode_edge(node_index, source, target, probs)

    return data


def _decode_uint16(data: bytes, pos: int) -> Tuple[int, int]:
    """Return the big-endian uint16 at a position and the next position.

    Args:
        data: Binary data to read.
        pos: Position of the value.

    Returns:
        Tuple of (value, position after the value).

    Raises:
        ValueError: If the data ends before the value.
    """
    if pos + 2 > len(data):
        raise ValueError("PDG.decompress() data truncated")
    return int.from_bytes(data[pos : pos + 2], "big"), pos + 2


def _decode_node_names(data: bytes) -> Tuple[List[str], int]:
    """Return the node names encoded in data and the next position.

    Args:
        data: Binary data to decode.

    Returns:
        Tuple of (node names, position after the names).

    Raises:
        ValueError: If the data is truncated.
    """
    num_nodes, pos = _decode_uint16(data, 0)

    nodes = []
    for _ in range(num_nodes):
        name_len, pos = _decode_uint16(data, pos)
        if pos + name_len > len(data):
            raise ValueError("PDG.decompress() data truncated")
        node = data[pos : pos + name_len].decode("utf-8")
        pos += name_len
        nodes.append(node)

    return nodes, pos


def _none_probability(
    p_forward: float, p_backward: float, p_undirected: float
) -> float:
    """Return p_none implied by the other three probabilities.

    Args:
        p_forward: Probability of a forward edge.
        p_backward: Probability of a backward edge.
        p_undirected: Probability of an undirected edge.

    Returns:
        The remaining probability, clamped to zero for tiny negatives.

    Raises:
        ValueError: If the probabilities sum to more than 1.0.
    """
    p_none = 1.0 - (p_forward + p_backward + p_undirected)

    # Handle floating point precision issues
    if p_none >= 0:
        return p_none
    if p_none > -1e-9:  # pragma: no cover
        return 0.0
    raise ValueError("PDG.decompress() probabilities sum to more than 1.0")


def _decode_probabilities(data: bytes, pos: int) -> Tuple[EdgeProbs, int]:
    """Return three encoded probabilities and the following position.

    Args:
        data: Binary data to decode.
        pos: Position of the first probability.

    Returns:
        Tuple of (probabilities, position after the third probability).

    Raises:
        ValueError: If the probabilities sum to more than 1.0.
    """
    p_forward = _decode_probability(data[pos : pos + 3])
    p_backward = _decode_probability(data[pos + 3 : pos + 6])
    p_undirected = _decode_probability(data[pos + 6 : pos + 9])
    p_none = _none_probability(p_forward, p_backward, p_undirected)
    probs = (p_forward, p_backward, p_undirected, p_none)
    return probs, pos + 3 * PROBABILITY_BYTES


def _decode_edge(
    data: bytes, pos: int, nodes: List[str]
) -> Tuple[str, str, EdgeProbs, int]:
    """Return the edge decoded at a position and the following position.

    Args:
        data: Binary data to decode.
        pos: Position of the edge.
        nodes: Node names decoded so far.

    Returns:
        Tuple of (source, target, probabilities, position after the edge).

    Raises:
        ValueError: If the edge is truncated, refers to an unknown node
            or holds probabilities that sum to more than 1.0.
    """
    if pos + EDGE_BYTES > len(data):  # 2+2+3+3+3 = 13 bytes per edge
        raise ValueError("PDG.decompress() data truncated")

    source_idx, pos = _decode_uint16(data, pos)
    target_idx, pos = _decode_uint16(data, pos)

    if source_idx >= len(nodes) or target_idx >= len(nodes):
        raise ValueError("PDG.decompress() invalid node index")

    probs, pos = _decode_probabilities(data, pos)
    return nodes[source_idx], nodes[target_idx], probs, pos


def decode_pdg(
    data: bytes,
) -> Tuple[List[str], Dict[Tuple[str, str], EdgeProbs]]:
    """Decode compact binary into node names and edge probabilities.

    Args:
        data: Binary data produced by :func:`encode_pdg`.

    Returns:
        Tuple of (node names, {(source, target): probabilities}).

    Raises:
        TypeError: If data is not bytes.
        ValueError: If data is invalid or corrupted.
    """
    if not isinstance(data, bytes):
        raise TypeError("PDG.decompress() data must be bytes")

    if len(data) < 2:
        raise ValueError("PDG.decompress() data too short")

    nodes, pos = _decode_node_names(data)
    num_edges, pos = _decode_uint16(data, pos)

    edges: Dict[Tuple[str, str], EdgeProbs] = {}
    for _ in range(num_edges):
        source, target, probs, pos = _decode_edge(data, pos, nodes)
        edges[(source, target)] = probs

    return nodes, edges
