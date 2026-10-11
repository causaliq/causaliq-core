#
#   Functions to read and write DSC format BN specification files
#

from typing import Any, Dict, List, Tuple

from causaliq_core.utils import FileFormatError, is_valid_path

from .dsc_parse import (  # noqa: F401
    TRANSITIONS,
    _parse_dsc_lines,
    _parse_line,
    _process_parsed,
    _reformat_cptdata,
)

# Format of output sections

CLOSE_SECT = "}}\n"
NETWORK_SECT = 'belief network "{}"\n'
NODE_SECT = 'node {} {{\n  type : discrete [ {} ] = {{ "{}" }};\n' + CLOSE_SECT
PROB_HDR = "probability ( {}{} ) {{\n"
CPT_ENTRY = "  ({}) : {};\n"


def read(path: str) -> Tuple[List[str], List[Tuple[str, str, str]], Any]:
    """Reads in a BN from a DSC format BN specification file.

    Args:
        path: Full path name of file.

    Returns:
        Tuple containing nodes, edges, and cptdata.

    Raises:
        TypeError: If path is not a string.
        FileNotFoundError: If file does not exist.
        FileFormatError: If file contents not valid.
    """

    is_valid_path(path)

    with open(path, encoding="utf-8") as f:
        nodes, edges, cptdata, prev_state = _parse_dsc_lines(f)

        if prev_state != "close":
            raise FileFormatError('DSC file empty or didn\'t end with "}"')

        cptdata = _reformat_cptdata(cptdata)

    return (nodes, edges, cptdata)


def _write_node_sections(f: Any, bn: Any) -> Dict[str, Any]:
    """Write a node section for every node of a BN.

    Args:
        f: Open file to write to.
        bn: Bayesian Network to write.

    Returns:
        Values of each node {node: [values]}.
    """
    values = {}
    for node in bn.dag.nodes:
        values[node] = (bn.cnds[node]).node_values()
        f.write(
            NODE_SECT.format(
                node, len(values[node]), '", "'.join(values[node])
            )
        )
    return values


def _write_cpt_pmf(
    f: Any,
    node: str,
    cpt: Any,
    values: Dict[str, Any],
    parental_values: Dict[str, str] = {},
) -> None:
    """Write the conditional probability entries of a node's CPT.

    Args:
        f: Open file to write to.
        node: Name of the node.
        cpt: Conditional distribution of the node.
        values: Values of each node {node: [values]}.
        parental_values: Parental values selected so far.
    """
    parent = cpt.parents()[len(parental_values)]
    for value in values[parent]:
        parental_values[parent] = value
        if len(cpt.parents()) > len(parental_values):
            _write_cpt_pmf(f, node, cpt, values, parental_values)
        else:
            value_idxs = [
                str(values[p].index(v)) for p, v in parental_values.items()
            ]
            probs = [str(cpt.cdist(parental_values)[v]) for v in values[node]]
            f.write(CPT_ENTRY.format(", ".join(value_idxs), ", ".join(probs)))
    del parental_values[parent]


def _write_prob_section(f: Any, cpt: Any, node: str, values: Any) -> None:
    """Write the probability section of one node.

    Args:
        f: Open file to write to.
        cpt: Conditional distribution of the node.
        node: Name of the node.
        values: Values of each node {node: [values]}.
    """
    parents = " | " + ", ".join(cpt.parents()) if cpt.has_parents else ""
    f.write(PROB_HDR.format(node, parents))
    if cpt.has_parents:
        _write_cpt_pmf(f, node, cpt, values)
    else:
        probs_str = ", ".join([str((cpt.cdist())[v]) for v in values[node]])
        f.write("   " + probs_str + ";\n")
    f.write(CLOSE_SECT.format())


def write(bn: Any, filename: str) -> None:
    """Writes Bayesian Network to disk file in DSC format.

    Args:
        bn: Bayesian Network to dump to file.
        filename: Name of file to write.

    Raises:
        FileNotFoundError: If file location nonexistent.
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(NETWORK_SECT.format("unknown"))

        values = _write_node_sections(f, bn)

        for node in bn.dag.nodes:
            _write_prob_section(f, bn.cnds[node], node, values)
