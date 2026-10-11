"""
Compact binary codec for Simple Dependency Graphs (SDG).

The codec encodes a graph's nodes and edges to a compact binary
representation and back. It works directly with node names and edge types
so that it does not need to depend on the graph classes themselves.
"""

from typing import Dict, List, Tuple

from .enums import EdgeType

# Bytes used by each encoded edge: 2 + 2 node indexes + 1 edge type
EDGE_BYTES = 5

# Mapping of edge type identifier to EdgeType
_EDGE_TYPE_LOOKUP: Dict[int, EdgeType] = {et.value[0]: et for et in EdgeType}


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
        raise ValueError("SDG.compress() node name too long")
    return len(name_bytes).to_bytes(2, "big") + name_bytes


def _encode_edge(
    node_index: Dict[str, int], source: str, target: str, edge_type: EdgeType
) -> bytes:
    """Return the encoded form of one edge.

    Args:
        node_index: Mapping of node name to node index.
        source: Source node name.
        target: Target node name.
        edge_type: Type of the edge.

    Returns:
        Compact binary representation of the edge.
    """
    data = node_index[source].to_bytes(2, "big")
    data += node_index[target].to_bytes(2, "big")
    data += edge_type.value[0].to_bytes(1, "big")
    return data


def encode_sdg(
    nodes: List[str], edges: Dict[Tuple[str, str], EdgeType]
) -> bytes:
    """Encode an SDG's nodes and edges to compact binary.

    Format:

    - 2 bytes: number of nodes (uint16, big-endian)
    - For each node: 2 bytes name length + UTF-8 encoded name
    - 2 bytes: number of edges (uint16, big-endian)
    - For each edge: 2 bytes source index + 2 bytes target index +
      1 byte edge type

    Args:
        nodes: Node names in graph order.
        edges: Edge types keyed by node pair.

    Returns:
        Compact binary representation of the graph.

    Raises:
        ValueError: If the graph has more than 65535 nodes or edges, or if
            a node name is too long.
    """
    if len(nodes) > 65535:
        raise ValueError("SDG.compress() graph has too many nodes")
    if len(edges) > 65535:
        raise ValueError("SDG.compress() graph has too many edges")

    # Build node index for edge compression
    node_index = {node: i for i, node in enumerate(nodes)}

    # Compress number of nodes
    data = len(nodes).to_bytes(2, "big")

    # Compress each node name
    for node in nodes:
        data += _encode_node_name(node)

    # Compress number of edges
    data += len(edges).to_bytes(2, "big")

    # Compress each edge (source index, target index, edge type)
    for (source, target), edge_type in edges.items():
        data += _encode_edge(node_index, source, target, edge_type)

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
        raise ValueError("SDG.decompress() data truncated")
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
            raise ValueError("SDG.decompress() data truncated")
        node = data[pos : pos + name_len].decode("utf-8")
        pos += name_len
        nodes.append(node)

    return nodes, pos


def _decode_edge(
    data: bytes, pos: int, nodes: List[str]
) -> Tuple[str, str, str, int]:
    """Return the edge decoded at a position and the following position.

    Args:
        data: Binary data to decode.
        pos: Position of the edge.
        nodes: Node names decoded so far.

    Returns:
        Tuple of (source, target, edge symbol, position after the edge).

    Raises:
        ValueError: If the edge is truncated, refers to an unknown node or
            has an unknown edge type.
    """
    if pos + EDGE_BYTES > len(data):
        raise ValueError("SDG.decompress() data truncated")

    source_idx, pos = _decode_uint16(data, pos)
    target_idx, pos = _decode_uint16(data, pos)
    edge_type_id = int.from_bytes(data[pos : pos + 1], "big")
    pos += 1

    if source_idx >= len(nodes) or target_idx >= len(nodes):
        raise ValueError("SDG.decompress() invalid node index")
    if edge_type_id not in _EDGE_TYPE_LOOKUP:
        raise ValueError("SDG.decompress() invalid edge type")

    edge_type = _EDGE_TYPE_LOOKUP[edge_type_id]
    return nodes[source_idx], edge_type.value[3], nodes[target_idx], pos


def decode_sdg(data: bytes) -> Tuple[List[str], List[Tuple[str, str, str]]]:
    """Decode compact binary into node names and edge triples.

    Args:
        data: Binary data produced by :func:`encode_sdg`.

    Returns:
        Tuple of (node names, edge triples).

    Raises:
        TypeError: If data is not bytes.
        ValueError: If data is invalid or corrupted.
    """
    if not isinstance(data, bytes):
        raise TypeError("SDG.decompress() data must be bytes")

    if len(data) < 2:
        raise ValueError("SDG.decompress() data too short")

    nodes, pos = _decode_node_names(data)
    num_edges, pos = _decode_uint16(data, pos)

    edges = []
    for _ in range(num_edges):
        source, symbol, target, pos = _decode_edge(data, pos, nodes)
        edges.append((source, symbol, target))

    return nodes, edges
