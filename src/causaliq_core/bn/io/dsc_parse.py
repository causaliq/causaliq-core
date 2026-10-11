#
#   Parsing of DSC format BN specification files
#
#   This module holds the line patterns, the line parser and the
#   consistency checks used by the DSC reader in dsc.py.
#

import re
from typing import Any, Dict, List, Optional, Tuple

from causaliq_core.utils import FileFormatError, values_same

from ..dist import CPT

# Patterns matching different types of line in DSC file

NAME = "[a-zA-Z0-9\\-\\_\\.]+"
NETWORK = re.compile('belief network "(' + NAME + ')"$')
NODE = re.compile("node (" + NAME + ") {$")
TYPE = re.compile("  type \\: discrete \\[ (\\d+) \\] = { (.+) };$")
PROB = re.compile("probability \\( (" + NAME + ") \\) {$")
PMF = re.compile("   (.+)\\;$")
COND_PROB = re.compile("probability \\( (" + NAME + ") \\| (.+) \\) {$")
COND_PMF = re.compile("  \\((.+)\\) \\: (.+);$")


# Allowed transitions between one type of line and the next in DSC file

TRANSITIONS = {
    "start": ["network"],
    "network": ["node"],
    "node": ["type"],
    "type": ["close"],
    "close": ["node", "prob", "cond_prob"],
    "prob": ["pmf"],
    "pmf": ["close"],
    "cond_prob": ["cond_pmf"],
    "cond_pmf": ["cond_pmf", "close"],
}


def _parse_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse line in DSC format file.

    Args:
        line: Line (with line terminator removed).

    Returns:
        Dict containing type of line and type specific attributes,
        or None if parsing fails.
    """
    if line == "}":  # close of node, prob or cond prob section
        return {"state": "close"}

    for pattern, parser in _LINE_PARSERS:
        result = pattern.match(line)
        if result:
            return parser(result)

    return None


def _parse_prob_line(result: Any) -> Dict[str, Any]:
    """Return the parsed probability section header.

    Args:
        result: Match of the PROB pattern.

    Returns:
        Parsed line.
    """
    return {"state": "prob", "node": result.group(1)}


def _parse_cond_pmf_line(result: Any) -> Optional[Dict[str, Any]]:
    """Return the parsed conditional probability entry.

    Args:
        result: Match of the COND_PMF pattern.

    Returns:
        Parsed line, or None if the entry is invalid.
    """
    try:
        parent_values = [int(s) for s in result.group(1).split(", ")]
        cond_pmf = [float(s) for s in result.group(2).split(", ")]
        if min(parent_values) < 0:
            raise ValueError("Parent value index is < 0")
        if not values_same(sum(cond_pmf), 1, sf=6):
            raise ValueError("Probabilities must sum to 1")
    except ValueError:
        return None
    return {
        "state": "cond_pmf",
        "parent_values": parent_values,
        "cond_pmf": cond_pmf,
    }


def _parse_cond_prob_line(result: Any) -> Dict[str, Any]:
    """Return the parsed conditional probability section header.

    Args:
        result: Match of the COND_PROB pattern.

    Returns:
        Parsed line.
    """
    return {
        "state": "cond_prob",
        "node": result.group(1),
        "parents": result.group(2).split(", "),
    }


def _parse_node_line(result: Any) -> Dict[str, Any]:
    """Return the parsed node section header.

    Args:
        result: Match of the NODE pattern.

    Returns:
        Parsed line.
    """
    return {"state": "node", "node": result.group(1)}


def _parse_type_line(result: Any) -> Optional[Dict[str, Any]]:
    """Return the parsed node type and values line.

    Args:
        result: Match of the TYPE pattern.

    Returns:
        Parsed line, or None if the values are invalid.
    """
    num_values = int(result.group(1))
    values = []
    for value in result.group(2).split(", "):
        if not value.startswith('"') or not value.endswith('"'):
            return None  # if value not double-quoted
        value = value[1:-1]
        if '"' in value or value in values:
            return None  # if value contains " or is a duplicate
        values.append(value)
    if len(values) != num_values:
        return None  # if number of values not correct
    return {"state": "type", "values": values}


def _parse_pmf_line(result: Any) -> Optional[Dict[str, Any]]:
    """Return the parsed non-conditional probabilities line.

    Args:
        result: Match of the PMF pattern.

    Returns:
        Parsed line, or None if the probabilities are invalid.
    """
    try:
        pmf = [float(s) for s in result.group(1).split(", ")]
        if not values_same(sum(pmf), 1, sf=6):
            raise ValueError("Probabilities must sum to 1")
    except ValueError:
        return None
    return {"state": "pmf", "pmf": pmf}


def _parse_network_line(result: Any) -> Dict[str, Any]:
    """Return the parsed belief network header.

    Args:
        result: Match of the NETWORK pattern.

    Returns:
        Parsed line.
    """
    return {"state": "network", "name": result.group(1)}


# Line parsers, in the order in which the line types are checked
_LINE_PARSERS = [
    (PROB, _parse_prob_line),
    (COND_PMF, _parse_cond_pmf_line),
    (COND_PROB, _parse_cond_prob_line),
    (NODE, _parse_node_line),
    (TYPE, _parse_type_line),
    (PMF, _parse_pmf_line),
    (NETWORK, _parse_network_line),
]


def _process_parsed(
    parsed: Dict[str, Any],
    nodes: List[str],
    edges: List[Tuple[str, str, str]],
    cptdata: Any,
    node: Any,
) -> Any:
    """Process parsed line, checking it is consistent with previous lines.

    Args:
        parsed: Parsed input line as returned by _parse_line.
        nodes: Currently identified node names.
        edges: Currently identified edges (node1, '->', node2).
        cptdata: Data to construct CPTs {parents, probs}.
        node: Current node being processed (from previous line).

    Returns:
        Tuple containing updated nodes, edges and cpts.

    Raises:
        FileFormatError: If error in file detected.
    """
    state = parsed["state"]
    node = parsed["node"] if "node" in parsed else node

    node = _STATE_HANDLERS[state](parsed, nodes, edges, cptdata, node)

    return (nodes, edges, cptdata, node)


def _check_cond_pmf_entry(
    parsed: Dict[str, Any], cptdata: Any, node: Any, parent_values: List[int]
) -> None:
    """Check a cond_pmf entry against the entries already recorded.

    Args:
        parsed: Parsed input line.
        cptdata: Data to construct CPTs {parents, probs}.
        node: Node whose cond_pmf entry is being checked.
        parent_values: Parental value indexes of the entry.

    Raises:
        FileFormatError: If the entry is inconsistent with earlier lines.
    """
    if len(parent_values) != len(cptdata[node]["parents"]):
        raise FileFormatError("Parent value index has wrong length")
    if len(parsed["cond_pmf"]) != len(cptdata[node]["values"]):
        raise FileFormatError("cond pmf has wrong length")
    if tuple(parent_values) in cptdata[node]["cond_pmf"]:
        raise FileFormatError("duplicate cond_pmf parental value keys")
    for idx, parent in enumerate(cptdata[node]["parents"]):
        if parent_values[idx] >= len(cptdata[parent]["values"]):
            raise FileFormatError("Invalid parental value index")


def _apply_cond_pmf(
    parsed: Dict[str, Any],
    nodes: List[str],
    edges: List[Tuple[str, str, str]],
    cptdata: Any,
    node: Any,
) -> Any:
    """Record an entry in a node's conditional probability table.

    Args:
        parsed: Parsed input line.
        nodes: Currently identified node names.
        edges: Currently identified edges (node1, '->', node2).
        cptdata: Data to construct CPTs {parents, probs}.
        node: Current node being processed (from previous line).

    Returns:
        The node being processed.

    Raises:
        FileFormatError: If the entry is inconsistent with earlier lines.
    """
    if "cond_pmf" not in cptdata[node]:
        cptdata[node]["cond_pmf"] = {}
    parent_values = parsed["parent_values"]
    _check_cond_pmf_entry(parsed, cptdata, node, parent_values)
    cptdata[node]["cond_pmf"][tuple(parent_values)] = parsed["cond_pmf"]
    return node


def _apply_node(
    parsed: Dict[str, Any],
    nodes: List[str],
    edges: List[Tuple[str, str, str]],
    cptdata: Any,
    node: Any,
) -> Any:
    """Record the start of the definition of a node.

    Args:
        parsed: Parsed input line.
        nodes: Currently identified node names.
        edges: Currently identified edges (node1, '->', node2).
        cptdata: Data to construct CPTs {parents, probs}.
        node: Current node being processed (from previous line).

    Returns:
        The node being processed.

    Raises:
        FileFormatError: If the node has been defined already.
    """
    if node in nodes:
        raise FileFormatError("Duplicate node {}".format(node))
    nodes.append(node)
    return node


def _apply_prob(
    parsed: Dict[str, Any],
    nodes: List[str],
    edges: List[Tuple[str, str, str]],
    cptdata: Any,
    node: Any,
) -> Any:
    """Record the start of a probability entry for a parentless node.

    Args:
        parsed: Parsed input line.
        nodes: Currently identified node names.
        edges: Currently identified edges (node1, '->', node2).
        cptdata: Data to construct CPTs {parents, probs}.
        node: Current node being processed (from previous line).

    Returns:
        The node being processed.

    Raises:
        FileFormatError: If the node is unknown.
    """
    if node not in nodes:
        raise FileFormatError("Unknown node {} in prob".format(node))
    cptdata[node]["parents"] = None
    return node


def _check_cond_prob_parent(parent: str, nodes: List[str], node: Any) -> None:
    """Check a parent named in a conditional probability header.

    Args:
        parent: Parent node named in the header.
        nodes: Currently identified node names.
        node: Node whose header is being checked.

    Raises:
        FileFormatError: If the parent is unknown.
    """
    if parent not in nodes:
        raise FileFormatError("Unknown node {} in cond prob".format(node))


def _apply_cond_prob(
    parsed: Dict[str, Any],
    nodes: List[str],
    edges: List[Tuple[str, str, str]],
    cptdata: Any,
    node: Any,
) -> Any:
    """Record the start of a probability entry for a node with parents.

    Args:
        parsed: Parsed input line.
        nodes: Currently identified node names.
        edges: Currently identified edges (node1, '->', node2).
        cptdata: Data to construct CPTs {parents, probs}.
        node: Current node being processed (from previous line).

    Returns:
        The node being processed.

    Raises:
        FileFormatError: If the node or one of its parents is unknown.
    """
    if node not in nodes:
        raise FileFormatError("Unknown node {} in cond prob".format(node))
    for parent in parsed["parents"]:
        _check_cond_prob_parent(parent, nodes, node)
        edges.append((parent, "->", node))
    cptdata[node]["parents"] = parsed["parents"]
    return node


def _apply_type(
    parsed: Dict[str, Any],
    nodes: List[str],
    edges: List[Tuple[str, str, str]],
    cptdata: Any,
    node: Any,
) -> Any:
    """Record the type and allowed values of a node.

    Args:
        parsed: Parsed input line.
        nodes: Currently identified node names.
        edges: Currently identified edges (node1, '->', node2).
        cptdata: Data to construct CPTs {parents, probs}.
        node: Current node being processed (from previous line).

    Returns:
        The node being processed.
    """
    cptdata[node] = {"values": parsed["values"]}
    return node


def _has_parents(cptdata: Any, node: Any) -> bool:
    """Return whether a node's probability data has been given parents.

    Args:
        cptdata: Data to construct CPTs {parents, probs}.
        node: Node being checked.

    Returns:
        True if the node has parents.
    """
    return "parents" in cptdata[node] and cptdata[node]["parents"] is not None


def _check_cond_pmf_complete(cptdata: Any, node: Any) -> None:
    """Check a node has an entry for every parental value combination.

    Args:
        cptdata: Data to construct CPTs {parents, probs}.
        node: Node whose cond_pmf entries are checked.

    Raises:
        FileFormatError: If any combination has no entry.
    """
    num_parental_combos = 1
    for parent in cptdata[node]["parents"]:
        num_parental_combos *= len(cptdata[parent]["values"])
    if len(cptdata[node]["cond_pmf"]) != num_parental_combos:
        raise FileFormatError("Missing cond_pmf entries")


def _apply_close(
    parsed: Dict[str, Any],
    nodes: List[str],
    edges: List[Tuple[str, str, str]],
    cptdata: Any,
    node: Any,
) -> Any:
    """Record the close of a node, prob or cond_prob section.

    Args:
        parsed: Parsed input line.
        nodes: Currently identified node names.
        edges: Currently identified edges (node1, '->', node2).
        cptdata: Data to construct CPTs {parents, probs}.
        node: Current node being processed (from previous line).

    Returns:
        None, as no node is being processed after a close.

    Raises:
        FileFormatError: If cond_pmf entries are missing.
    """
    if _has_parents(cptdata, node):
        _check_cond_pmf_complete(cptdata, node)
    return None


def _apply_pmf(
    parsed: Dict[str, Any],
    nodes: List[str],
    edges: List[Tuple[str, str, str]],
    cptdata: Any,
    node: Any,
) -> Any:
    """Record the probabilities of a parentless node.

    Args:
        parsed: Parsed input line.
        nodes: Currently identified node names.
        edges: Currently identified edges (node1, '->', node2).
        cptdata: Data to construct CPTs {parents, probs}.
        node: Current node being processed (from previous line).

    Returns:
        The node being processed.

    Raises:
        FileFormatError: If the PMF has the wrong number of entries.
    """
    pmf = parsed["pmf"]
    if len(pmf) != len(cptdata[node]["values"]):
        raise FileFormatError("node {} PMF wrong number of entries ")
    cptdata[node]["pmf"] = pmf
    return node


def _apply_network(
    parsed: Dict[str, Any],
    nodes: List[str],
    edges: List[Tuple[str, str, str]],
    cptdata: Any,
    node: Any,
) -> Any:
    """Ignore the belief network header line.

    Args:
        parsed: Parsed input line.
        nodes: Currently identified node names.
        edges: Currently identified edges (node1, '->', node2).
        cptdata: Data to construct CPTs {parents, probs}.
        node: Current node being processed (from previous line).

    Returns:
        The node being processed, unchanged.
    """
    return node


# Handler applying each type of parsed line
_STATE_HANDLERS = {
    "close": _apply_close,
    "cond_pmf": _apply_cond_pmf,
    "cond_prob": _apply_cond_prob,
    "network": _apply_network,
    "node": _apply_node,
    "pmf": _apply_pmf,
    "prob": _apply_prob,
    "type": _apply_type,
}


def _parse_dsc_lines(
    f: Any,
) -> Tuple[List[str], List[Tuple[str, str, str]], Any, str]:
    """Parse every line of an open DSC format file.

    Args:
        f: Open DSC format file.

    Returns:
        Tuple of (nodes, edges, cptdata, state of the last line parsed).

    Raises:
        FileFormatError: If a line is invalid, or the file is not UTF-8.
    """
    line_num = 0
    prev_state = "start"
    nodes: List[str] = []
    edges: List[Tuple[str, str, str]] = []
    cptdata: Any = {}
    node = None

    try:
        for line in f:
            line_num += 1
            nodes, edges, cptdata, node, prev_state = _parse_dsc_line(
                line_num,
                line.replace("\n", ""),
                nodes,
                edges,
                cptdata,
                node,
                prev_state,
            )
    except UnicodeDecodeError:
        raise FileFormatError("File contains unexpected char")

    return nodes, edges, cptdata, prev_state


def _parse_dsc_line(
    line_num: int,
    line: str,
    nodes: List[str],
    edges: List[Tuple[str, str, str]],
    cptdata: Any,
    node: Any,
    prev_state: str,
) -> Tuple[List[str], List[Tuple[str, str, str]], Any, Any, str]:
    """Parse one line of a DSC format file into the parse state.

    Args:
        line_num: Number of the line in the file.
        line: Line with its line terminator removed.
        nodes: Currently identified node names.
        edges: Currently identified edges (node1, '->', node2).
        cptdata: Data to construct CPTs {parents, probs}.
        node: Current node being processed (from previous line).
        prev_state: State of the previous line.

    Returns:
        Tuple of (nodes, edges, cptdata, node, state of this line).

    Raises:
        FileFormatError: If the line is invalid.
    """
    parsed = _parse_line(line)
    if not parsed or parsed["state"] not in TRANSITIONS[prev_state]:
        raise FileFormatError("Line {} invalid: {}".format(line_num, line))
    nodes, edges, cptdata, node = _process_parsed(
        parsed, nodes, edges, cptdata, node
    )
    return nodes, edges, cptdata, node, parsed["state"]


def _parented_cpt_data(data: Any, cptdata: Any) -> List[Tuple[Any, Any]]:
    """Return the conditional PMFs of a node with parents.

    Args:
        data: CPT data of the node {values, parents, cond_pmf}.
        cptdata: CPT data of every node {node: data}.

    Returns:
        List of (parental values, PMF) entries.
    """
    cond_pmfs = []
    for pvs_idx, probs in (data["cond_pmf"]).items():
        pmf = {v: pr for v, pr in zip(data["values"], probs)}
        pvs = {
            pa: cptdata[pa]["values"][idx]
            for pa, idx in zip(data["parents"], pvs_idx)
        }
        cond_pmfs.append((pvs, pmf))
    return cond_pmfs


def _reformat_cptdata(cptdata: Any) -> Any:
    """Assemble cptdata in format required by BN constructor.

    Args:
        cptdata: CPT data from DSC file {node: cptdata}.

    Returns:
        CPT data in required format {node: cptdata}.
    """
    result = {}
    for node, data in cptdata.items():
        if data["parents"] is None:
            pmf = {v: p for v, p in zip(data["values"], data["pmf"])}
            result.update({node: (CPT, pmf)})
        else:
            result.update({node: (CPT, _parented_cpt_data(data, cptdata))})
    return result
