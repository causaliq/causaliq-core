#
#   Functions to read and write GraphML format graph files
#
#   GraphML is an XML-based format for graphs. This module supports reading
#   and writing SDG, PDAG, and DAG graphs in GraphML format.
#
#   Supports both filesystem paths and file-like objects (e.g., StringIO)
#   for interoperability with workflow caches and in-memory processing.
#
#   Reference: http://graphml.graphdrawing.org/
#
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

from causaliq_core.utils import FileFormatError

from ..dag import DAG
from ..enums import EdgeMark, EdgeType
from ..pdag import PDAG
from ..sdg import SDG
from .graphml_common import (  # noqa: F401
    _MARKS_TO_EDGE_TYPE,
    ENDPOINT_TO_MARK,
    GRAPHML_NS,
    NS,
    VALID_EDGE_SYMBOLS,
    FileLike,
    _check_graphml_write_target,
    _describe_graphml_source,
    _edge_endpoints,
    _endpoint_to_mark,
    _graph_element,
    _marks_to_symbol,
    _open_graphml_root,
    _parse_key_definitions,
    _parse_nodes,
    _validate_edge_symbol,
    _write_graphml_document,
    add_edge_key_definitions,
    is_valid_path,
)
from .graphml_pdg import read_pdg, write_pdg  # noqa: F401

if TYPE_CHECKING:  # pragma: no cover
    from ..pdg import PDG  # noqa: F401

# Map EdgeMark to GraphML endpoint value
_MARK_TO_ENDPOINT = {
    EdgeMark.LINE: "none",
    EdgeMark.ARROW: "arrow",
    EdgeMark.CIRCLE: "circle",
}


def read(file: FileLike) -> Union[SDG, PDAG, DAG]:
    """Read a graph from a GraphML file or file-like object.

    Supports standard GraphML files with optional edge endpoint attributes
    to represent different edge types (directed, undirected, bidirected,
    etc.). Without endpoint attributes, edges default to directed.

    Args:
        file: File path (str or Path) or file-like object (e.g., StringIO).
            For file paths, suffix must be '.graphml'.

    Returns:
        SDG, PDAG or DAG depending on edge types in the graph.

    Raises:
        TypeError: If argument types incorrect.
        ValueError: If file path suffix not '.graphml'.
        FileNotFoundError: If specified file does not exist.
        FileFormatError: If file contents are not valid GraphML.

    Example:
        >>> from io import StringIO
        >>> xml = '<graphml><graph><node id="A"/></graph></graphml>'
        >>> graph = read(StringIO(xml))
    """
    is_path, source_desc = _describe_graphml_source(file, "read")
    root, ns = _open_graphml_root(file, is_path, "read", source_desc)
    graph_elem = _graph_element(root, ns, source_desc)

    # Collect key definitions for edge attributes
    edge_keys = _parse_key_definitions(root, ns)

    # Parse nodes
    nodes = _parse_nodes(graph_elem, ns, source_desc)
    if not nodes:
        raise FileFormatError(f"file {source_desc} has no nodes")

    # Parse edges
    edges, has_undirected, has_non_pdag = _parse_edges(
        graph_elem, ns, edge_keys, source_desc
    )

    return _graph_for_edges(nodes, edges, has_undirected, has_non_pdag)


def _graph_for_edges(
    nodes: List[str],
    edges: List[Tuple[str, str, str]],
    has_undirected: bool,
    has_non_pdag: bool,
) -> Union[SDG, PDAG, DAG]:
    """Return the graph class matching the edge types found.

    Args:
        nodes: Node names of the graph.
        edges: Edge triples of the graph.
        has_undirected: Whether an undirected edge was found.
        has_non_pdag: Whether an edge outside PDAG semantics was found.

    Returns:
        SDG, PDAG or DAG depending on the edge types in the graph.
    """
    if has_non_pdag:
        return SDG(nodes, edges)
    if has_undirected:
        return PDAG(nodes, edges)
    return DAG(nodes, edges)


class _EdgeTypes:
    """Edge semantics found while parsing a GraphML graph.

    Attributes:
        has_undirected: Whether an undirected edge has been found.
        has_non_pdag: Whether an edge outside PDAG semantics was found.
    """

    def __init__(self) -> None:
        self.has_undirected = False
        self.has_non_pdag = False

    def record(self, edge_symbol: str) -> None:
        """Record the semantics implied by an edge type symbol.

        Args:
            edge_symbol: Edge type symbol (e.g. "->", "-", "<->").
        """
        if edge_symbol == EdgeType.UNDIRECTED.value[3]:
            self.has_undirected = True
            return
        if edge_symbol in (
            EdgeType.DIRECTED.value[3],
            EdgeType.UNDIRECTED.value[3],
        ):
            return
        self.has_non_pdag = True


def _parse_edges(
    graph_elem: ET.Element,
    ns: dict,
    edge_keys: Dict[str, Dict[str, Optional[str]]],
    source_desc: str,
) -> Tuple[List[Tuple[str, str, str]], bool, bool]:
    """Parse edge elements from the graph.

    Args:
        graph_elem: The graph element.
        ns: Namespace dictionary.
        edge_keys: Key definitions for edge attributes.
        source_desc: Source description for error messages.

    Returns:
        Tuple of (edges list, has_undirected, has_non_pdag edges).
    """
    edges: List[Tuple[str, str, str]] = []
    types = _EdgeTypes()

    edge_tag = "g:edge" if ns else "edge"

    for edge_elem in graph_elem.findall(edge_tag, ns):
        source, target = _edge_endpoints(edge_elem, source_desc)
        for edge in _edge_triples(
            edge_elem, ns, edge_keys, source_desc, source, target, types
        ):
            edges.append(edge)

    return edges, types.has_undirected, types.has_non_pdag


def _edge_triples(
    edge_elem: ET.Element,
    ns: dict,
    edge_keys: Dict[str, Dict[str, Optional[str]]],
    source_desc: str,
    source: str,
    target: str,
    types: "_EdgeTypes",
) -> List[Tuple[str, str, str]]:
    """Return the edge triples described by one GraphML edge element.

    Args:
        edge_elem: The edge element.
        ns: Namespace dictionary.
        edge_keys: Key definitions for edge attributes.
        source_desc: Source description for error messages.
        source: Source node name of the edge.
        target: Target node name of the edge.
        types: Edge semantics accumulated so far.

    Returns:
        List of edge triples, empty when the edge has no explicit type.
    """
    explicit = _explicit_edge_triples(
        edge_elem, ns, edge_keys, source_desc, source, target, types
    )
    if explicit:
        return explicit

    # Determine the edge type from endpoint marks or the directed attribute
    symbol = _marked_or_default_symbol(edge_elem, ns, edge_keys)
    types.record(symbol)
    return [(source, symbol, target)]


def _explicit_edge_triples(
    edge_elem: ET.Element,
    ns: dict,
    edge_keys: Dict[str, Dict[str, Optional[str]]],
    source_desc: str,
    source: str,
    target: str,
    types: "_EdgeTypes",
) -> List[Tuple[str, str, str]]:
    """Return edge triples given by explicit edgeType data elements.

    Args:
        edge_elem: The edge element.
        ns: Namespace dictionary.
        edge_keys: Key definitions for edge attributes.
        source_desc: Source description for error messages.
        source: Source node name of the edge.
        target: Target node name of the edge.
        types: Edge semantics accumulated so far.

    Returns:
        List of edge triples, empty when no edgeType data is present.
    """
    triples: List[Tuple[str, str, str]] = []
    data_tag = "g:data" if ns else "data"

    for data_elem in edge_elem.findall(data_tag, ns):
        symbol = _explicit_edge_symbol(data_elem, edge_keys, source_desc)
        if symbol is not None:
            types.record(symbol)
            triples.append((source, symbol, target))

    return triples


def _explicit_edge_symbol(
    data_elem: ET.Element,
    edge_keys: Dict[str, Dict[str, Optional[str]]],
    source_desc: str,
) -> Optional[str]:
    """Return the edge symbol given by an edgeType data element.

    Args:
        data_elem: A data element of the edge.
        edge_keys: Key definitions for edge attributes.
        source_desc: Source description for error messages.

    Returns:
        The validated edge symbol, or None when the element holds none.
    """
    key = data_elem.get("key") or ""
    attr_name = edge_keys.get(key, {}).get("name") or ""
    if attr_name == "edgeType":
        return _validate_edge_symbol(data_elem.text or "", source_desc)
    return None


def _marked_or_default_symbol(
    edge_elem: ET.Element,
    ns: dict,
    edge_keys: Dict[str, Dict[str, Optional[str]]],
) -> str:
    """Return the edge symbol from endpoint marks or the directed attribute.

    Args:
        edge_elem: The edge element.
        ns: Namespace dictionary.
        edge_keys: Key definitions for edge attributes.

    Returns:
        The edge type symbol for the edge.
    """
    if edge_elem.get("directed") == "false":
        return EdgeType.UNDIRECTED.value[3]
    source_mark, target_mark = _endpoint_marks(edge_elem, ns, edge_keys)
    return _marks_to_symbol(source_mark, target_mark)


def _endpoint_marks(
    edge_elem: ET.Element,
    ns: dict,
    edge_keys: Dict[str, Dict[str, Optional[str]]],
) -> Tuple[EdgeMark, EdgeMark]:
    """Return the endpoint marks described by an edge's data elements.

    Args:
        edge_elem: The edge element.
        ns: Namespace dictionary.
        edge_keys: Key definitions for edge attributes.

    Returns:
        Tuple of (source mark, target mark).
    """
    source_mark = EdgeMark.LINE  # default: tail/line
    target_mark = EdgeMark.ARROW  # default: arrow/head (directed)
    marks: Dict[str, EdgeMark] = {}
    data_tag = "g:data" if ns else "data"

    for data_elem in edge_elem.findall(data_tag, ns):
        attr_name, mark = _endpoint_mark_for(data_elem, edge_keys)
        marks[attr_name] = mark

    return (
        marks.get("sourceEndpoint", source_mark),
        marks.get("targetEndpoint", target_mark),
    )


def _endpoint_mark_for(
    data_elem: ET.Element,
    edge_keys: Dict[str, Dict[str, Optional[str]]],
) -> Tuple[str, EdgeMark]:
    """Return the endpoint attribute name and mark of a data element.

    Args:
        data_elem: A data element of the edge.
        edge_keys: Key definitions for edge attributes.

    Returns:
        Tuple of (attribute name, endpoint mark).
    """
    key = data_elem.get("key") or ""
    attr_name = edge_keys.get(key, {}).get("name") or ""
    return attr_name, _endpoint_to_mark(data_elem.text or "")


def write(
    graph: Union[SDG, PDAG, DAG],
    file: FileLike,
    graph_id: str = "G",
) -> None:
    """Write a graph to a GraphML file or file-like object.

    Exports the graph with node ordering preserved and edge types encoded
    using sourceEndpoint/targetEndpoint data attributes.

    Args:
        graph: SDG, PDAG or DAG to write.
        file: File path (str or Path) or file-like object (e.g., StringIO).
            For file paths, suffix must be '.graphml'.
        graph_id: ID attribute for the graph element. Defaults to "G".

    Raises:
        TypeError: If argument types incorrect.
        ValueError: If file path suffix not '.graphml'.

    Example:
        >>> from io import StringIO
        >>> buffer = StringIO()
        >>> write(graph, buffer)
        >>> xml_content = buffer.getvalue()
    """
    if not isinstance(graph, SDG):
        raise TypeError("graphml.write() graph arg must be SDG, PDAG or DAG")

    is_path = _check_graphml_write_target(file, "write")

    # DAG: all edges directed, use edgedefault="directed"
    # PDAG/SDG: mixed edges, use edgedefault="undirected"
    is_dag = isinstance(graph, DAG)
    edge_default = "directed" if is_dag else "undirected"

    # Build XML document
    root = ET.Element("graphml", xmlns=GRAPHML_NS)

    # Add key definitions for edge endpoint attributes
    add_edge_key_definitions(
        root, ("sourceEndpoint", "targetEndpoint"), "string"
    )

    # Create graph element
    graph_elem = _add_graph_element(root, graph_id, edge_default)

    # Add nodes in order
    for node in graph.nodes:
        ET.SubElement(graph_elem, "node", id=node)

    # Add edges with endpoint attributes
    _add_graph_edges(graph_elem, graph.edges, is_dag)

    _write_graphml_document(root, file, is_path)


def _add_graph_element(
    root: ET.Element, graph_id: str, edge_default: str
) -> ET.Element:
    """Add the graph element to a GraphML document.

    Args:
        root: Root element of the document being built.
        graph_id: ID attribute for the graph element.
        edge_default: Default edge direction for the graph element.

    Returns:
        The graph element.
    """
    return ET.SubElement(root, "graph", id=graph_id, edgedefault=edge_default)


def _add_graph_edges(
    graph_elem: ET.Element,
    edges: Dict[Tuple[str, str], EdgeType],
    is_dag: bool,
) -> None:
    """Add edge elements with endpoint data to the graph element.

    Args:
        graph_elem: The graph element.
        edges: Edge types keyed by node pair.
        is_dag: Whether the graph is a DAG.
    """
    edge_id = 0

    for (source, target), edge_type in edges.items():
        edge_id += 1
        edge_elem = _add_edge_element(
            graph_elem, edge_id, source, target, edge_type, is_dag
        )
        _add_endpoint_data(edge_elem, edge_type)


def _add_edge_element(
    graph_elem: ET.Element,
    edge_id: int,
    source: str,
    target: str,
    edge_type: EdgeType,
    is_dag: bool,
) -> ET.Element:
    """Add an edge element, marking directed edges where needed.

    For non-DAG graphs, simple directed edges (->) are marked with
    directed="true" for third-party tool compatibility.

    Args:
        graph_elem: The graph element.
        edge_id: One-based identifier of the edge.
        source: Source node name.
        target: Target node name.
        edge_type: Type of the edge.
        is_dag: Whether the graph is a DAG.

    Returns:
        The edge element.
    """
    attributes = {"id": f"e{edge_id}", "source": source, "target": target}
    if not is_dag and edge_type == EdgeType.DIRECTED:
        attributes["directed"] = "true"
    return ET.SubElement(graph_elem, "edge", attributes)


def _add_endpoint_data(edge_elem: ET.Element, edge_type: EdgeType) -> None:
    """Add sourceEndpoint and targetEndpoint data to an edge element.

    Args:
        edge_elem: The edge element.
        edge_type: Type of the edge.
    """
    for key_id, mark in (
        ("sourceEndpoint", edge_type.value[1]),
        ("targetEndpoint", edge_type.value[2]),
    ):
        data_elem = ET.SubElement(edge_elem, "data", key=key_id)
        data_elem.text = _MARK_TO_ENDPOINT[mark]
