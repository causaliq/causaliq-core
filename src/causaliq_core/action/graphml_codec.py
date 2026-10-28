"""
Compact binary encoding of tokenised GraphML graphs.

A graph is stored as a tokenised node list (2 bytes per node, via
:class:`~causaliq_core.cache.TokenCache`) followed by a compact binary
edge list (5 bytes per edge). The decoder rebuilds the node names and
the edge triples used to reconstruct the graph.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from causaliq_core.cache import TokenCache
from causaliq_core.graph import SDG


def _encode_sdg_edges(result: bytearray, sdg: SDG) -> None:
    """Append the encoded edges of an SDG to a byte buffer.

    Args:
        result: Buffer to append the encoded edges to.
        sdg: Graph whose edges are encoded.
    """
    node_index = {node: i for i, node in enumerate(sdg.nodes)}
    for (source, target), edge_type in sdg.edges.items():
        result.extend(node_index[source].to_bytes(2, "big"))
        result.extend(node_index[target].to_bytes(2, "big"))
        result.extend(edge_type.value[0].to_bytes(1, "big"))


def _decode_uint16(blob: bytes, pos: int) -> Tuple[int, int]:
    """Return the big-endian uint16 at a position and the next position.

    Args:
        blob: Binary data to decode.
        pos: Position of the value.

    Returns:
        Tuple of (value, position after the value).

    Raises:
        ValueError: If the data ends before the value.
    """
    if pos + 2 > len(blob):
        raise ValueError("Compressed graphml data truncated")
    return int.from_bytes(blob[pos : pos + 2], "big"), pos + 2


def _decode_graphml_nodes(
    blob: bytes, cache: TokenCache
) -> Tuple[List[str], int]:
    """Return the tokenised node names of a compressed graphml blob.

    Args:
        blob: Binary data to decode.
        cache: TokenCache for node name detokenisation.

    Returns:
        Tuple of (node names, position after the names).

    Raises:
        ValueError: If the data is truncated or holds an unknown token.
    """
    num_nodes, pos = _decode_uint16(blob, 0)

    nodes = []
    for _ in range(num_nodes):
        token_id, pos = _decode_uint16(blob, pos)
        node = cache.get_token(token_id)
        if node is None:
            raise ValueError(f"Unknown token ID: {token_id}")
        nodes.append(node)

    return nodes, pos


def _decode_graphml_edges(
    blob: bytes, pos: int, num_edges: int, nodes: List[str]
) -> List[Tuple[str, str, str]]:
    """Return the edges of a compressed graphml blob.

    Args:
        blob: Binary data to decode.
        pos: Position of the first edge.
        num_edges: Number of edges to decode.
        nodes: Node names decoded so far.

    Returns:
        List of edge triples.

    Raises:
        ValueError: If the data is truncated or holds an invalid node
            index or edge type.
    """
    from causaliq_core.graph import EdgeType

    edge_type_lookup = {et.value[0]: et for et in EdgeType}

    edges = []
    for _ in range(num_edges):
        if pos + 5 > len(blob):
            raise ValueError("Compressed graphml data truncated")
        source_idx, pos = _decode_uint16(blob, pos)
        target_idx, pos = _decode_uint16(blob, pos)
        edge_type_id = int.from_bytes(blob[pos : pos + 1], "big")
        pos += 1
        edges.append(
            _decode_graphml_edge(
                source_idx, target_idx, edge_type_id, nodes, edge_type_lookup
            )
        )

    return edges


def _decode_graphml_edge(
    source_idx: int,
    target_idx: int,
    edge_type_id: int,
    nodes: List[str],
    edge_type_lookup: Dict[int, Any],
) -> Tuple[str, str, str]:
    """Return one decoded edge triple from a compressed graphml blob.

    Args:
        source_idx: Index of the source node.
        target_idx: Index of the target node.
        edge_type_id: Encoded identifier of the edge type.
        nodes: Node names decoded so far.
        edge_type_lookup: Mapping of encoded identifier to EdgeType.

    Returns:
        Edge triple (source, symbol, target).

    Raises:
        ValueError: If a node index or the edge type is invalid.
    """
    if source_idx >= len(nodes) or target_idx >= len(nodes):
        raise ValueError("Compressed graphml has invalid node index")
    if edge_type_id not in edge_type_lookup:
        raise ValueError("Compressed graphml has invalid edge type")
    edge_type = edge_type_lookup[edge_type_id]
    return nodes[source_idx], edge_type.value[3], nodes[target_idx]
