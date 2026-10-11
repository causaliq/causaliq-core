#
#   Common helpers for reading and writing GraphML format graph files
#
#   GraphML is an XML-based format for graphs. This module holds the
#   namespace, endpoint and parsing helpers shared by the SDG/PDAG/DAG and
#   PDG GraphML readers and writers.
#
#   Reference: http://graphml.graphdrawing.org/
#
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Iterable, List, Optional, TextIO, Tuple, Union

from causaliq_core.utils import FileFormatError, is_valid_path

from ..enums import EdgeMark, EdgeType

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

# Map EdgeMark to GraphML endpoint value
_MARK_TO_ENDPOINT = {
    EdgeMark.LINE: "none",
    EdgeMark.ARROW: "arrow",
    EdgeMark.CIRCLE: "circle",
}


def _describe_graphml_source(file: FileLike, func: str) -> Tuple[bool, str]:
    """Return whether a source is a path and how to describe it.

    Args:
        file: File path or file-like object supplied by the caller.
        func: Name of the calling function, used in error messages.

    Returns:
        Tuple of (whether the source is a path, description of the source).

    Raises:
        TypeError: If the source is neither a path nor file-like object.
    """
    is_path = isinstance(file, (str, Path))
    is_file_like = hasattr(file, "read")
    if not is_path and not is_file_like:
        raise TypeError(
            f"graphml.{func}() file arg must be str, Path, "
            "or file-like object"
        )
    return is_path, str(file) if is_path else "<file-like object>"


def _check_graphml_suffix(file: FileLike, func: str) -> None:
    """Validate the .graphml suffix of a file path argument.

    Args:
        file: File path supplied by the caller.
        func: Name of the calling function, used in error messages.

    Raises:
        ValueError: If the path does not have a .graphml suffix.
    """
    if str(file).lower().split(".")[-1] != "graphml":
        raise ValueError(f"graphml.{func}() bad file suffix")


def _check_graphml_path(file: FileLike, func: str) -> None:
    """Validate a GraphML file path argument that must already exist.

    Args:
        file: File path supplied by the caller.
        func: Name of the calling function, used in error messages.

    Raises:
        ValueError: If the path does not have a .graphml suffix.
        FileNotFoundError: If the path does not exist.
    """
    _check_graphml_suffix(file, func)
    is_valid_path(str(file))


def _check_graphml_write_target(file: FileLike, func: str) -> bool:
    """Validate the output target of a GraphML writer.

    Args:
        file: File path or file-like object to write to.
        func: Name of the calling function, used in error messages.

    Returns:
        bool: Whether the target is a file path.

    Raises:
        TypeError: If the target is neither a path nor file-like object.
        ValueError: If a file path does not have a .graphml suffix.
    """
    is_path = isinstance(file, (str, Path))
    if not is_path and not hasattr(file, "write"):
        raise TypeError(
            f"graphml.{func}() file arg must be str, Path, "
            "or file-like object"
        )
    if is_path:
        _check_graphml_suffix(file, func)
    return is_path


def _open_graphml_root(
    file: FileLike, is_path: bool, func: str, source_desc: str
) -> Tuple[ET.Element, dict]:
    """Parse a GraphML source and resolve its namespace.

    Args:
        file: File path or file-like object.
        is_path: Whether file is a path rather than a file-like object.
        func: Name of the calling function, used in error messages.
        source_desc: Source description for error messages.

    Returns:
        Tuple of (root element, namespace dictionary).

    Raises:
        ValueError: If a file path does not have a .graphml suffix.
        FileNotFoundError: If a file path does not exist.
        FileFormatError: If the contents are not valid GraphML.
    """
    if is_path:
        _check_graphml_path(file, func)
    try:
        if is_path:
            tree = ET.parse(str(file))
        else:
            tree = ET.parse(file)  # type: ignore[arg-type]
        root = tree.getroot()
    except ET.ParseError as e:
        raise FileFormatError(f"file {source_desc} invalid XML: {e}")
    return root, _graphml_namespace(root, source_desc)


def _graphml_namespace(root: ET.Element, source_desc: str) -> dict:
    """Return the namespace mapping for a GraphML root element.

    Args:
        root: Root element of the parsed document.
        source_desc: Source description for error messages.

    Returns:
        Namespace dictionary, empty for non-namespaced GraphML.

    Raises:
        FileFormatError: If the root element is not GraphML.
    """
    if root.tag == f"{{{GRAPHML_NS}}}graphml":
        return NS
    if root.tag == "graphml":
        return {}
    raise FileFormatError(
        f"file {source_desc} not a GraphML file " f"(root element: {root.tag})"
    )


def _graph_element(root: ET.Element, ns: dict, source_desc: str) -> ET.Element:
    """Return the graph element of a GraphML document.

    Args:
        root: Root element of the parsed document.
        ns: Namespace dictionary.
        source_desc: Source description for error messages.

    Returns:
        The graph element.

    Raises:
        FileFormatError: If the document has no graph element.
    """
    graph_elem = root.find("g:graph", ns) if ns else root.find("graph")
    if graph_elem is None:
        raise FileFormatError(f"file {source_desc} has no graph element")
    return graph_elem


def add_edge_key_definitions(
    root: ET.Element, key_ids: Iterable[str], attr_type: str
) -> None:
    """Add key definitions for edge attributes to a GraphML document.

    Args:
        root: Root element of the document being built.
        key_ids: Identifiers and attribute names of the keys to add.
        attr_type: GraphML attribute type of the keys.
    """
    for key_id in key_ids:
        key_elem = ET.SubElement(root, "key", id=key_id)
        key_elem.set("for", "edge")
        key_elem.set("attr.name", key_id)
        key_elem.set("attr.type", attr_type)


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
) -> List[str]:
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


def _write_graphml_document(
    root: ET.Element, file: FileLike, is_path: bool
) -> None:
    """Write a GraphML document to a path or file-like object.

    Args:
        root: Root element of the document.
        file: File path or file-like object to write to.
        is_path: Whether file is a path rather than a file-like object.
    """
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")

    if is_path:
        with open(str(file), "wb") as f:
            tree.write(f, encoding="utf-8", xml_declaration=True)
        return

    # File-like object - write as string
    # ET.write() doesn't support StringIO directly, so we convert
    xml_str = ET.tostring(root, encoding="unicode")
    xml_declaration = '<?xml version="1.0" encoding="utf-8"?>\n'
    file.write(xml_declaration + xml_str)  # type: ignore[union-attr]


def _edge_endpoints(
    edge_elem: ET.Element, source_desc: str
) -> Tuple[str, str]:
    """Return the source and target node names of an edge element.

    Args:
        edge_elem: The edge element.
        source_desc: Source description for error messages.

    Returns:
        Tuple of (source node name, target node name).

    Raises:
        FileFormatError: If the edge has no source or target.
    """
    source = edge_elem.get("source")
    target = edge_elem.get("target")
    if source is None or target is None:
        raise FileFormatError(
            f"file {source_desc} has edge without source or target"
        )
    return source, target
