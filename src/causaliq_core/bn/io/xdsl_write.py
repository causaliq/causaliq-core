#
#   Writes Bayesian Networks to XDSL format BN definition files
#

from re import sub
from typing import Any, Dict

from ..dist import CPT, NodeValueCombinations
from .xdsl_common import (
    GENIE_END,
    GENIE_HDR,
    GENIE_NODE,
    NODES_END,
    STARTS_WITH_LETTER,
    XDSL_END,
    XDSL_HDR,
)


def genie_str(string: Any, prefix: Any) -> Any:
    """Cleanses string so that it conforms to Genie requirements.

    Cleanses string so that it conforms to Genie requirements for a
    node name or value.

    Args:
        string: Node name or value to cleanse.
        prefix: Prefix to use if doesn't start with letter.

    Returns:
        Cleansed string that meets Genie requirements.
    """
    cleansed = string if STARTS_WITH_LETTER.match(string) else prefix + string

    return sub("[^0-9a-zA-Z]+", "_", cleansed)


def write_genie_extension(f: Any, partial_order: Any) -> Any:
    """Writes the XDSL Genie extension XML.

    Writes the XDSL Genie extension XML which defines node placement
    on the visual drawing of the network.

    Args:
        f: Handle to write text.
        partial_order: Of (list of) nodes in each partial order
                       group of nodes.
    """
    f.write(GENIE_HDR)
    top = 0
    for group in partial_order:
        top += 100
        left = 20
        for node in group:
            f.write(
                GENIE_NODE.format(
                    genie_str(node, "N"), 8, left, top, left + 80, top + 40
                )
            )
            left += 100
    f.write(GENIE_END)


def _write_cpt(
    f: Any, node: Any, cpt: Any, node_values: Any, genie: Any
) -> Any:
    """Write a <cpt> element.

    Args:
        f: Handle for writing to file.
        node: Node that CPT relates to.
        cpt: CPT to represent in XDSL.
        node_values: Node values for categorical nodes.
        genie: Whether to be in Genie format.
    """

    # <cpt> opening element

    f.write('        <cpt id="{}">\n'.format(node))

    # node values (states)

    for value in node_values[node]:
        f.write(
            '            <state id="{}" />\n'.format(
                genie_str(value, "S") if genie is True else value
            )
        )

    # process CPT to get parents name if any, and then probabilities
    # associated with each parent value combo and node value.
    # Take care that values always processed in alphabetical order.

    probs = []
    if cpt.has_parents:
        parents = " ".join([p for p in cpt.parents()])
        f.write("            <parents>" + parents + "</parents>\n")
        pvs = {p: node_values[p] for p in cpt.parents()}
        for pvc in NodeValueCombinations(pvs):
            probs.extend([cpt.cdist(pvc)[v] for v in node_values[node]])
    else:
        probs.extend([cpt.cdist()[v] for v in node_values[node]])
    f.write(
        "            <probabilities>{}</probabilities>\n".format(
            " ".join(["{}".format(p) for p in probs])
        )
    )

    f.write("        </cpt>\n")


def _write_equation(f: Any, node: Any, lingauss: Any, genie: Any) -> Any:
    """Write <equation> element representing linear gaussian.

    Args:
        f: Handle for writing to file.
        node: Node that CPT relates to.
        lingauss: Linear Gaussian to represent in XDSL.
        genie: Whether to be in Genie format.
    """
    f.write(
        '        <equation id="{}">\n'.format(
            genie_str(node, "N") if genie is True else node
        )
    )

    if lingauss.coeffs != {}:
        parents = " ".join([p for p in lingauss.coeffs])
        f.write("            <parents>" + parents + "</parents>\n")

    f.write(
        "            <definition>{}={}</definition>\n".format(node, lingauss)
    )

    f.write("        </equation>\n")


def write(bn: Any, filename: Any, genie: Any = False) -> Any:
    """Write Bayesian Network to disk file in XDSL format.

    Ensure everything written out with node name and values ordered
    alphabetically.

    Args:
        bn: Bayesian Network to dump to file.
        filename: Name of file to write.
        genie: Whether files needs to be read by Genie - if so,
               will ensure all node and state names start with
               a letter.

    Raises:
        TypeError: Bad argument types.
        FileNotFoundError: If file location nonexistent.
    """
    if bn.__class__.__name__ != "BN" or not isinstance(filename, str):
        raise TypeError("xdsl.write() bad arg type")

    # Ensure all node names are Genie-friendly if required

    if genie is True:
        bn = _genie_renamed_bn(bn)

    # node_values has each node's allowed values ordered alphabetically.

    node_values = _categorical_node_values(bn)
    parents = _node_parents(bn)
    partial_order = bn.dag.partial_order(parents)
    order = [n for g in partial_order for n in g]

    with open(filename, "w", encoding="utf-8") as f:

        f.write(XDSL_HDR)

        _write_nodes(f, order, bn, node_values, genie)

        f.write(NODES_END)

        if genie is True:
            write_genie_extension(f, partial_order)

        f.write(XDSL_END)


def _genie_renamed_bn(bn: Any) -> Any:
    """Return a copy of a BN with Genie-friendly node names.

    Args:
        bn: Bayesian Network to rename.

    Returns:
        Copy of the network with cleansed node names.
    """
    from copy import deepcopy

    name_map = {n: genie_str(n, "N") for n in bn.dag.nodes}
    renamed = deepcopy(bn)  # Work on a copy to avoid modifying the original
    renamed.rename(name_map)
    return renamed


def _categorical_node_values(bn: Any) -> Dict[Any, Any]:
    """Return the allowed values of each categorical node of a BN.

    Args:
        bn: Bayesian Network to write.

    Returns:
        Values of each categorical node {node: [values]}, ordered
        alphabetically.
    """
    return {
        n: bn.cnds[n].node_values()
        for n in bn.dag.nodes
        if isinstance(bn.cnds[n], CPT)
    }


def _node_parents(bn: Any) -> Dict[Any, Any]:
    """Return the parents of each node of a BN.

    Args:
        bn: Bayesian Network to write.

    Returns:
        Parents of each node {node: [parents]}.
    """
    return {
        n: bn.dag.parents[n] if n in bn.dag.parents else []
        for n in bn.dag.nodes
    }


def _write_nodes(
    f: Any, order: Any, bn: Any, node_values: Any, genie: Any
) -> None:
    """Write the <cpt> or <equation> element of every node.

    Args:
        f: Handle for writing to file.
        order: Nodes in topological order.
        bn: Bayesian Network to write.
        node_values: Node values for categorical nodes.
        genie: Whether to be in Genie format.
    """
    for node in order:
        if isinstance(bn.cnds[node], CPT):
            _write_cpt(f, node, bn.cnds[node], node_values, genie)
        else:
            _write_equation(f, node, bn.cnds[node], genie)
