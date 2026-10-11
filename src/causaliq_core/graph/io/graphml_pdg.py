#
#   Functions to read and write GraphML format PDG files
#
#   GraphML is an XML-based format for graphs. This module reads and writes
#   Probabilistic Dependency Graphs (PDGs) with edge probability
#   attributes (p_forward, p_backward, p_undirected, p_none).
#
#   Supports both filesystem paths and file-like objects (e.g., StringIO)
#   for interoperability with workflow caches and in-memory processing.
#
#   Reference: http://graphml.graphdrawing.org/
#
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Dict, Tuple

from causaliq_core.utils import FileFormatError

from .graphml_common import (
    GRAPHML_NS,
    FileLike,
    _check_graphml_write_target,
    _describe_graphml_source,
    _edge_endpoints,
    _graph_element,
    _open_graphml_root,
    _parse_nodes,
    _write_graphml_document,
    add_edge_key_definitions,
)

if TYPE_CHECKING:  # pragma: no cover
    from ..pdg import PDG, EdgeProbabilities  # noqa: F401

# Probability attribute names written to GraphML
_PDG_KEYS = ["p_forward", "p_backward", "p_undirected", "p_none"]

# Probability attribute names read from GraphML
_PROBABILITY_KEYS = set(_PDG_KEYS)


def read_pdg(file: FileLike) -> "PDG":
    """Read a PDG from a GraphML file or file-like object.

    Reads a Probabilistic Dependency Graph with edge probability attributes.
    The file should have undirected edges with p_forward, p_backward,
    p_undirected, and p_none data attributes.

    Args:
        file: File path (str or Path) or file-like object (e.g., StringIO).
            For file paths, suffix must be '.graphml'.

    Returns:
        PDG instance with edge probabilities.

    Raises:
        TypeError: If argument types incorrect.
        ValueError: If file path suffix not '.graphml'.
        FileNotFoundError: If specified file does not exist.
        FileFormatError: If file contents are not valid GraphML or
            missing required probability attributes.

    Example:
        >>> from io import StringIO
        >>> xml = '''<?xml version="1.0"?>
        ... <graphml xmlns="http://graphml.graphdrawing.org/xmlns">
        ...   <key id="p_forward" for="edge" attr.type="double"/>
        ...   <graph edgedefault="undirected">
        ...     <node id="A"/><node id="B"/>
        ...     <edge source="A" target="B">
        ...       <data key="p_forward">0.8</data>
        ...       <data key="p_backward">0.1</data>
        ...       <data key="p_undirected">0.05</data>
        ...       <data key="p_none">0.05</data>
        ...     </edge>
        ...   </graph>
        ... </graphml>'''
        >>> pdg = read_pdg(StringIO(xml))
    """
    from causaliq_core.graph.pdg import PDG  # noqa: F811

    is_path, source_desc = _describe_graphml_source(file, "read_pdg")
    root, ns = _open_graphml_root(file, is_path, "read_pdg", source_desc)
    graph_elem = _graph_element(root, ns, source_desc)

    nodes = _parse_nodes(graph_elem, ns, source_desc)
    if not nodes:
        raise FileFormatError(f"file {source_desc} has no nodes")

    edges = _parse_probability_edges(graph_elem, ns, source_desc)
    return PDG(nodes, edges)


def _parse_probability_edges(
    graph_elem: ET.Element, ns: dict, source_desc: str
) -> Dict[Tuple[str, str], "EdgeProbabilities"]:
    """Return the edge probabilities held by a GraphML graph element.

    Args:
        graph_elem: The graph element.
        ns: Namespace dictionary.
        source_desc: Source description for error messages.

    Returns:
        Edge probabilities keyed by canonical node pair.

    Raises:
        FileFormatError: If an edge is malformed, lacks probability
            attributes or holds an invalid probability value.
    """
    edges: Dict[Tuple[str, str], "EdgeProbabilities"] = {}
    edge_tag = "g:edge" if ns else "edge"

    for edge_elem in graph_elem.findall(edge_tag, ns):
        source, target, probs = _edge_probabilities(edge_elem, ns, source_desc)
        edges[(source, target)] = probs

    return edges


def _edge_probabilities(
    edge_elem: ET.Element, ns: dict, source_desc: str
) -> Tuple[str, str, "EdgeProbabilities"]:
    """Return the canonical node pair and probabilities of an edge element.

    Args:
        edge_elem: The edge element.
        ns: Namespace dictionary.
        source_desc: Source description for error messages.

    Returns:
        Tuple of (source, target, probabilities) in canonical node order.

    Raises:
        FileFormatError: If the edge lacks endpoints or probability
            attributes, or holds probabilities that are not a valid
            distribution.
    """
    source, target = _edge_endpoints(edge_elem, source_desc)
    values = _edge_probability_values(edge_elem, ns, source_desc)
    if not values:
        raise FileFormatError(
            f"file {source_desc} edge ({source}, {target}) "
            "missing probability attributes"
        )
    source, target, values = _canonical_probabilities(source, target, values)
    probs = _edge_distribution(values, source_desc, source, target)
    return source, target, probs


def _edge_probability_values(
    edge_elem: ET.Element, ns: dict, source_desc: str
) -> Dict[str, float]:
    """Return the raw probability values of an edge element.

    Args:
        edge_elem: The edge element.
        ns: Namespace dictionary.
        source_desc: Source description for error messages.

    Returns:
        Mapping of probability name to value, empty when none are present.

    Raises:
        FileFormatError: If a probability value cannot be parsed.
    """
    values: Dict[str, float] = {}
    data_tag = "g:data" if ns else "data"

    for data_elem in edge_elem.findall(data_tag, ns):
        key = data_elem.get("key")
        if key in _PROBABILITY_KEYS:
            values[key] = _probability_value(
                data_elem.text or "0.0", source_desc
            )

    return values


def _probability_value(text: str, source_desc: str) -> float:
    """Return a probability parsed from edge data text.

    Args:
        text: Text content of the edge data element.
        source_desc: Source description for error messages.

    Returns:
        The parsed probability value.

    Raises:
        FileFormatError: If the text is not a valid number.
    """
    try:
        return float(text)
    except ValueError:
        raise FileFormatError(
            f"file {source_desc} has invalid probability value: " f"{text}"
        )


def _canonical_probabilities(
    source: str, target: str, values: Dict[str, float]
) -> Tuple[str, str, Dict[str, float]]:
    """Return the node pair and probabilities in canonical order.

    Args:
        source: Source node name as read from the file.
        target: Target node name as read from the file.
        values: Raw probability values keyed by probability name.

    Returns:
        Tuple of (source, target, values) in canonical node order.
    """
    if source > target:
        swapped = dict(values)
        swapped["p_forward"] = values.get("p_backward", 0.0)
        swapped["p_backward"] = values.get("p_forward", 0.0)
        return target, source, swapped
    return source, target, values


def _edge_distribution(
    values: Dict[str, float], source_desc: str, source: str, target: str
) -> "EdgeProbabilities":
    """Return the edge probabilities described by raw probability values.

    Args:
        values: Raw probability values keyed by probability name.
        source_desc: Source description for error messages.
        source: Source node name in canonical order.
        target: Target node name in canonical order.

    Returns:
        The edge probability distribution.

    Raises:
        FileFormatError: If the probabilities are not a valid distribution.
    """
    from causaliq_core.graph.pdg import EdgeProbabilities  # noqa: F811

    try:
        return EdgeProbabilities(
            forward=values.get("p_forward", 0.0),
            backward=values.get("p_backward", 0.0),
            undirected=values.get("p_undirected", 0.0),
            none=values.get("p_none", 0.0),
        )
    except ValueError as e:
        raise FileFormatError(
            f"file {source_desc} edge ({source}, {target}): {e}"
        )


def write_pdg(pdg: "PDG", file: FileLike) -> None:
    """Write a PDG to a GraphML file or file-like object.

    Exports the PDG with undirected edges and probability data attributes
    (p_forward, p_backward, p_undirected, p_none).

    Only edges with p_exist > 0 (i.e., p_none < 1.0) are written.

    Args:
        pdg: PDG to write.
        file: File path (str or Path) or file-like object (e.g., StringIO).
            For file paths, suffix must be '.graphml'.

    Raises:
        TypeError: If argument types incorrect.
        ValueError: If file path suffix not '.graphml'.

    Example:
        >>> from io import StringIO
        >>> from causaliq_core.graph.pdg import PDG, EdgeProbabilities
        >>> pdg = PDG(["A", "B"], {
        ...     ("A", "B"): EdgeProbabilities(forward=0.8, none=0.2)
        ... })
        >>> buffer = StringIO()
        >>> write_pdg(pdg, buffer)
        >>> print(buffer.getvalue())
    """
    from causaliq_core.graph.pdg import PDG  # noqa: F811

    if not isinstance(pdg, PDG):
        raise TypeError("graphml.write_pdg() pdg arg must be PDG")

    is_path = _check_graphml_write_target(file, "write_pdg")

    # Build XML document
    root = ET.Element("graphml", xmlns=GRAPHML_NS)

    # Add key definitions for probability attributes
    add_edge_key_definitions(root, _PDG_KEYS, "double")

    # Create graph element with undirected default
    graph_elem = ET.SubElement(root, "graph", id="G", edgedefault="undirected")

    # Add nodes in order
    for node in pdg.nodes:
        ET.SubElement(graph_elem, "node", id=node)

    # Add edges with probability attributes (only if p_exist > 0)
    _add_pdg_edges(graph_elem, pdg.edges)

    _write_graphml_document(root, file, is_path)


def _add_pdg_edges(
    graph_elem: ET.Element, edges: Dict[Tuple[str, str], "EdgeProbabilities"]
) -> None:
    """Add edge elements with probability data to the graph element.

    Only edges with p_exist > 0 (i.e., p_none < 1.0) are written.

    Args:
        graph_elem: The graph element.
        edges: Edge probabilities keyed by node pair.
    """
    edge_id = 0

    for (source, target), probs in edges.items():
        if probs.p_exist == 0:
            continue  # Skip edges with no probability of existing

        edge_id += 1
        edge_elem = ET.SubElement(
            graph_elem, "edge", id=f"e{edge_id}", source=source, target=target
        )
        _add_probability_data(edge_elem, probs)


def _add_probability_data(
    edge_elem: ET.Element, probs: "EdgeProbabilities"
) -> None:
    """Add probability data elements to an edge element.

    Args:
        edge_elem: The edge element.
        probs: Edge probabilities to write.
    """
    for key_id, value in (
        ("p_forward", probs.forward),
        ("p_backward", probs.backward),
        ("p_undirected", probs.undirected),
        ("p_none", probs.none),
    ):
        data_elem = ET.SubElement(edge_elem, "data", key=key_id)
        data_elem.text = f"{value:.8g}"
