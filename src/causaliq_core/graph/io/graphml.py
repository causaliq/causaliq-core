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

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, TextIO, Union

from causaliq_core.utils import FileFormatError, is_valid_path

from ..dag import DAG
from ..enums import EdgeMark, EdgeType
from ..pdag import PDAG
from ..sdg import SDG

# Type alias for file path or file-like object
FileLike = Union[str, Path, TextIO]

# GraphML namespace
GRAPHML_NS = "http://graphml.graphdrawing.org/xmlns"
NS = {"g": GRAPHML_NS}

# Map GraphML endpoint strings to EdgeMark enum
ENDPOINT_TO_MARK = {
    "arrow": EdgeMark.ARROW,
    "target": EdgeMark.ARROW,
    "head": EdgeMark.ARROW,
    "circle": EdgeMark.CIRCLE,
    "none": EdgeMark.LINE,
    "source": EdgeMark.LINE,
    "tail": EdgeMark.LINE,
    "line": EdgeMark.LINE,
}

# Build lookup from (source_mark, target_mark) to EdgeType
_MARKS_TO_EDGE_TYPE: Dict[tuple, EdgeType] = {}
for et in EdgeType:
    if et != EdgeType.NONE:
        _MARKS_TO_EDGE_TYPE[(et.value[1], et.value[2])] = et

# Valid edge type symbols from EdgeType enum
VALID_EDGE_SYMBOLS = {et.value[3] for et in EdgeType if et != EdgeType.NONE}


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
    # Validate file argument type
    is_path = isinstance(file, (str, Path))
    is_file_like = hasattr(file, "read")

    if not is_path and not is_file_like:
        raise TypeError(
            "graphml.read() file arg must be str, Path, or file-like object"
        )

    source_desc = str(file) if is_path else "<file-like object>"

    if is_path:
        path_str = str(file)
        if path_str.lower().split(".")[-1] != "graphml":
            raise ValueError("graphml.read() bad file suffix")
        is_valid_path(path_str)

    try:
        if is_path:
            tree = ET.parse(str(file))
        else:
            # File-like object - read content and parse
            tree = ET.parse(file)  # type: ignore[arg-type]
        root = tree.getroot()
    except ET.ParseError as e:
        raise FileFormatError(f"file {source_desc} invalid XML: {e}")

    # Handle namespaced and non-namespaced GraphML
    if root.tag == f"{{{GRAPHML_NS}}}graphml":
        ns = NS
    elif root.tag == "graphml":
        ns = {}
    else:
        raise FileFormatError(
            f"file {source_desc} not a GraphML file "
            f"(root element: {root.tag})"
        )

    # Find the graph element
    graph_elem = root.find("g:graph", ns) if ns else root.find("graph")
    if graph_elem is None:
        raise FileFormatError(f"file {source_desc} has no graph element")

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

    # Determine graph type and return appropriate class
    if has_non_pdag:
        return SDG(nodes, edges)
    elif has_undirected:
        return PDAG(nodes, edges)
    else:
        return DAG(nodes, edges)


def _parse_key_definitions(
    root: ET.Element, ns: dict
) -> Dict[str, Dict[str, Optional[str]]]:
    """Parse GraphML key definitions for edge attributes.

    Args:
        root: Root element of the GraphML document.
        ns: Namespace dictionary.

    Returns:
        Dictionary mapping key id to attribute info.
    """
    keys: Dict[str, Dict[str, Optional[str]]] = {}
    key_tag = "g:key" if ns else "key"
    for key_elem in root.findall(key_tag, ns):
        key_id = key_elem.get("id")
        attr_name = key_elem.get("attr.name")
        attr_for = key_elem.get("for")
        if key_id and attr_for == "edge":
            keys[key_id] = {"name": attr_name}
    return keys


def _parse_nodes(
    graph_elem: ET.Element, ns: dict, source_desc: str
) -> list[str]:
    """Parse node elements from the graph.

    Args:
        graph_elem: The graph element.
        ns: Namespace dictionary.
        source_desc: Source description for error messages.

    Returns:
        List of node names.
    """
    nodes = []
    node_tag = "g:node" if ns else "node"
    for node_elem in graph_elem.findall(node_tag, ns):
        node_id = node_elem.get("id")
        if node_id is None:
            raise FileFormatError(f"file {source_desc} has node without id")
        if node_id in nodes:
            raise FileFormatError(
                f"file {source_desc} has duplicate node id: {node_id}"
            )
        nodes.append(node_id)
    return nodes


def _parse_edges(
    graph_elem: ET.Element,
    ns: dict,
    edge_keys: Dict[str, Dict[str, Optional[str]]],
    source_desc: str,
) -> tuple[list[tuple[str, str, str]], bool, bool]:
    """Parse edge elements from the graph.

    Args:
        graph_elem: The graph element.
        ns: Namespace dictionary.
        edge_keys: Key definitions for edge attributes.
        source_desc: Source description for error messages.

    Returns:
        Tuple of (edges list, has_undirected, has_non_pdag edges).
    """
    edges = []
    has_undirected = False
    has_non_pdag = False

    edge_tag = "g:edge" if ns else "edge"
    data_tag = "g:data" if ns else "data"

    for edge_elem in graph_elem.findall(edge_tag, ns):
        source = edge_elem.get("source")
        target = edge_elem.get("target")

        if source is None or target is None:
            raise FileFormatError(
                f"file {source_desc} has edge without source or target"
            )

        # Check for directed attribute (GraphML standard)
        directed = edge_elem.get("directed")

        # Parse edge data elements for endpoint marks
        source_mark = EdgeMark.LINE  # default: tail/line
        target_mark = EdgeMark.ARROW  # default: arrow/head (directed)
        edge_type_explicit = False  # True if edgeType data element found

        for data_elem in edge_elem.findall(data_tag, ns):
            key = data_elem.get("key")
            if key in edge_keys:
                attr_name = edge_keys[key].get("name", "")
                value = data_elem.text or ""

                if attr_name == "sourceEndpoint":
                    source_mark = _endpoint_to_mark(value)
                elif attr_name == "targetEndpoint":
                    target_mark = _endpoint_to_mark(value)
                elif attr_name == "edgeType":
                    # Direct edge type symbol (e.g., "->", "-", "<->")
                    edge_symbol = _validate_edge_symbol(value, source_desc)
                    edges.append((source, edge_symbol, target))
                    if edge_symbol == EdgeType.UNDIRECTED.value[3]:
                        has_undirected = True
                    elif edge_symbol not in (
                        EdgeType.DIRECTED.value[3],
                        EdgeType.UNDIRECTED.value[3],
                    ):
                        has_non_pdag = True
                    edge_type_explicit = True

        # If no explicit edgeType, determine from endpoint marks or directed
        if not edge_type_explicit:
            # Handle directed="false" attribute
            if directed == "false":
                edge_symbol = EdgeType.UNDIRECTED.value[3]
                has_undirected = True
            else:
                edge_symbol = _marks_to_symbol(source_mark, target_mark)
                if edge_symbol == EdgeType.UNDIRECTED.value[3]:
                    has_undirected = True
                elif edge_symbol not in (
                    EdgeType.DIRECTED.value[3],
                    EdgeType.UNDIRECTED.value[3],
                ):
                    has_non_pdag = True

            edges.append((source, edge_symbol, target))

    return edges, has_undirected, has_non_pdag


def _endpoint_to_mark(endpoint: str) -> EdgeMark:
    """Convert GraphML endpoint value to EdgeMark enum.

    Args:
        endpoint: Endpoint value (none, source, target, arrow, circle, etc.).

    Returns:
        EdgeMark enum value.
    """
    endpoint = endpoint.lower().strip()
    return ENDPOINT_TO_MARK.get(endpoint, EdgeMark.LINE)


def _marks_to_symbol(source_mark: EdgeMark, target_mark: EdgeMark) -> str:
    """Convert endpoint marks to edge type symbol using EdgeType enum.

    Args:
        source_mark: EdgeMark at source end.
        target_mark: EdgeMark at target end.

    Returns:
        Edge type symbol (e.g., ->, -, <->, o->).
    """
    # Try direct lookup
    edge_type = _MARKS_TO_EDGE_TYPE.get((source_mark, target_mark))
    if edge_type:
        return edge_type.value[3]

    # Handle reverse cases by swapping marks
    # e.g., (ARROW, LINE) is reverse of DIRECTED, (LINE, CIRCLE) needs reversal
    edge_type = _MARKS_TO_EDGE_TYPE.get((target_mark, source_mark))
    if edge_type:
        # Return the symbol but caller should reverse edge direction
        return edge_type.value[3]

    # Default to directed if unknown combination
    return EdgeType.DIRECTED.value[3]


def _validate_edge_symbol(symbol: str, source_desc: str) -> str:
    """Validate an edge type symbol against EdgeType enum.

    Args:
        symbol: Edge type symbol to validate.
        source_desc: Source description for error messages.

    Returns:
        Validated symbol.

    Raises:
        FileFormatError: If symbol is invalid.
    """
    symbol = symbol.strip()
    if symbol not in VALID_EDGE_SYMBOLS:
        raise FileFormatError(
            f"file {source_desc} has invalid edge type: {symbol}"
        )
    return symbol


# Map EdgeMark to GraphML endpoint value
_MARK_TO_ENDPOINT = {
    EdgeMark.LINE: "none",
    EdgeMark.ARROW: "arrow",
    EdgeMark.CIRCLE: "circle",
}


def write(graph: Union[SDG, PDAG, DAG], file: FileLike) -> None:
    """Write a graph to a GraphML file or file-like object.

    Exports the graph with node ordering preserved and edge types encoded
    using sourceEndpoint/targetEndpoint data attributes.

    Args:
        graph: SDG, PDAG or DAG to write.
        file: File path (str or Path) or file-like object (e.g., StringIO).
            For file paths, suffix must be '.graphml'.

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

    # Validate file argument type
    is_path = isinstance(file, (str, Path))
    is_file_like = hasattr(file, "write")

    if not is_path and not is_file_like:
        raise TypeError(
            "graphml.write() file arg must be str, Path, or file-like object"
        )

    if is_path:
        path_str = str(file)
        if path_str.lower().split(".")[-1] != "graphml":
            raise ValueError("graphml.write() bad file suffix")

    # Build XML document
    root = ET.Element("graphml", xmlns=GRAPHML_NS)

    # Add key definitions for edge endpoint attributes
    source_key = ET.SubElement(root, "key", id="sourceEndpoint")
    source_key.set("for", "edge")
    source_key.set("attr.name", "sourceEndpoint")
    source_key.set("attr.type", "string")

    target_key = ET.SubElement(root, "key", id="targetEndpoint")
    target_key.set("for", "edge")
    target_key.set("attr.name", "targetEndpoint")
    target_key.set("attr.type", "string")

    # Create graph element (edgedefault doesn't matter as we specify per-edge)
    graph_elem = ET.SubElement(root, "graph", id="G", edgedefault="directed")

    # Add nodes in order
    for node in graph.nodes:
        ET.SubElement(graph_elem, "node", id=node)

    # Add edges with endpoint attributes
    edge_id = 0
    for (source, target), edge_type in graph.edges.items():
        edge_id += 1
        edge_elem = ET.SubElement(
            graph_elem, "edge", id=f"e{edge_id}", source=source, target=target
        )

        # Get endpoint marks from EdgeType
        source_mark = edge_type.value[1]
        target_mark = edge_type.value[2]

        # Add endpoint data elements
        source_data = ET.SubElement(edge_elem, "data", key="sourceEndpoint")
        source_data.text = _MARK_TO_ENDPOINT[source_mark]

        target_data = ET.SubElement(edge_elem, "data", key="targetEndpoint")
        target_data.text = _MARK_TO_ENDPOINT[target_mark]

    # Write to file with XML declaration and proper formatting
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")

    if is_path:
        with open(str(file), "wb") as f:
            tree.write(f, encoding="utf-8", xml_declaration=True)
    else:
        # File-like object - write as string
        # ET.write() doesn't support StringIO directly, so we convert
        xml_str = ET.tostring(root, encoding="unicode")
        xml_declaration = '<?xml version="1.0" encoding="utf-8"?>\n'
        file.write(xml_declaration + xml_str)  # type: ignore[union-attr]
