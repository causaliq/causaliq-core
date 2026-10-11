"""bnlearn graph utilities using Rscript subprocess."""

import os
from typing import Dict, List, Optional, Tuple

from causaliq_core.bn import BN, LinGauss
from causaliq_core.graph import DAG, PDAG, EdgeType
from causaliq_core.r.convert import r_arcs_to_edges
from causaliq_core.r.exceptions import (
    RNotAvailableError,
    RRuntimeError,
)
from causaliq_core.r.session import run_r_script


def _build_r_network_script(varname: str, pdag: PDAG) -> List[str]:
    """Return R code lines that create a bnlearn network variable.

    Args:
        varname: Name of the R variable to assign the network to.
        pdag: The PDAG to convert into bnlearn graph calls.

    Returns:
        List of R code lines (without trailing newlines).
    """
    nodes_str = ", ".join(f'"{n}"' for n in pdag.nodes)
    lines = [f"{varname} <- empty.graph(c({nodes_str}))"]
    for (tail, head), etype in pdag.edges.items():
        if etype == EdgeType.DIRECTED:
            lines.append(
                f"{varname} <- set.arc(" f'{varname}, "{tail}", "{head}")'
            )
        else:
            lines.append(
                f"{varname} <- set.edge(" f'{varname}, "{tail}", "{head}")'
            )
    return lines


def _parse_r_arc_output(output: str) -> List[Tuple[str, str]]:
    """Return the arcs listed in tab-delimited R output.

    Args:
        output: Standard output from an R script that wrote arcs as a table.

    Returns:
        List of (tail, head) node pairs.
    """
    arcs: List[Tuple[str, str]] = []
    if not output.strip():
        return arcs
    for row in output.strip().split("\n"):
        parts = row.strip().split("\t")
        if len(parts) == 2:
            arcs.append((parts[0], parts[1]))
    return arcs


def bnlearn_cpdag(pdag: PDAG) -> PDAG:
    """Return CPDAG corresponding to supplied PDAG via bnlearn.

    Args:
        pdag: PDAG to transform to CPDAG.

    Raises:
        TypeError: If pdag is not a PDAG instance.
        ValueError: If pdag is empty.
        RNotAvailableError: If Rscript is not available.
        RRuntimeError: If the R script exits with a non-zero status.

    Returns:
        CPDAG corresponding to the pdag argument.
    """
    if not isinstance(pdag, PDAG):
        raise TypeError("bnlearn_cpdag: pdag must be a PDAG instance")
    if not pdag.nodes:
        raise ValueError("bnlearn_cpdag: pdag must not be empty")
    script_lines = (
        ["library(bnlearn)"]
        + _build_r_network_script("net", pdag)
        + [
            "cpdag_net <- cpdag(net)",
            "a <- arcs(cpdag_net)",
            "if (nrow(a) > 0) {",
            "  write.table(",
            "    a, stdout(),",
            "    col.names=FALSE, row.names=FALSE,",
            '    quote=FALSE, sep="\\t"',
            "  )",
            "}",
        ]
    )
    try:
        output = run_r_script("\n".join(script_lines) + "\n")
        edges = r_arcs_to_edges(_parse_r_arc_output(output))
    except (RNotAvailableError, RRuntimeError):
        raise
    except Exception as exc:
        raise RRuntimeError(f"bnlearn_cpdag failed: {exc}") from exc
    return PDAG(pdag.nodes, edges)


def bnlearn_compare(pdag: PDAG, ref: PDAG) -> Dict[str, int]:
    """Compare a PDAG against a reference PDAG using bnlearn.

    Note: bnlearn converts graphs to CPDAGs before computing SHD.

    Args:
        pdag: PDAG to compare against the reference.
        ref: Reference PDAG.

    Raises:
        TypeError: If either argument is not a PDAG instance.
        ValueError: If node sets are empty or do not match.
        RNotAvailableError: If Rscript is not available.
        RRuntimeError: If the R script exits with a non-zero status.

    Returns:
        Dict with integer values for keys 'tp', 'fp', 'fn', 'shd'.
    """
    if not isinstance(pdag, PDAG) or not isinstance(ref, PDAG):
        raise TypeError("bnlearn_compare: pdag and ref must be PDAG instances")
    if not pdag.nodes or pdag.nodes != ref.nodes:
        raise ValueError(
            "bnlearn_compare: pdag and ref must have the same "
            "non-empty node set"
        )
    script_lines = (
        ["library(bnlearn)"]
        + _build_r_network_script("net", pdag)
        + _build_r_network_script("ref_net", ref)
        + [
            "comp <- compare(ref_net, net)",
            "shd_val <- shd(ref_net, net)",
            'cat(comp$tp, comp$fp, comp$fn, shd_val, sep="\\n")',
        ]
    )
    try:
        output = run_r_script("\n".join(script_lines) + "\n")
        values = [
            int(float(v)) for v in output.strip().split("\n") if v.strip()
        ]
        tp, fp, fn, shd = values[0], values[1], values[2], values[3]
    except (RNotAvailableError, RRuntimeError):
        raise
    except Exception as exc:
        raise RRuntimeError(f"bnlearn_compare failed: {exc}") from exc
    return {"tp": tp, "fp": fp, "fn": fn, "shd": shd}


def bnlearn_import(rda_path: str) -> BN:
    """Import a LinGauss BN from a bnlearn .rda file.

    Only supports continuous (LinGauss) Bayesian Networks. The .rda
    file must contain an R variable named 'bn' of type bn.fit.

    Args:
        rda_path: Absolute path to the .rda file.

    Raises:
        TypeError: If rda_path is not a string.
        FileNotFoundError: If the .rda file does not exist.
        ValueError: If the file cannot be parsed as a LinGauss BN.
        RNotAvailableError: If Rscript is not available.
        RRuntimeError: If the R script exits with a non-zero status.

    Returns:
        BN object reconstructed from the .rda file.
    """
    if not isinstance(rda_path, str):
        raise TypeError("bnlearn_import: rda_path must be a string")
    if not os.path.isfile(rda_path):
        raise FileNotFoundError(f"bnlearn_import: file not found: {rda_path}")
    r_path = rda_path.replace("\\", "/")
    script_lines = [
        "library(bnlearn)",
        f'load("{r_path}")',
        "for (node in nodes(bn)) {",
        "  nd <- bn[[node]]",
        "  parents_str <- paste(nd$parents, collapse=',')",
        '  cat("NODE\\t", node, "\\n", sep="")',
        '  cat("PARENTS\\t", parents_str, "\\n", sep="")',
        "  coef_names <- names(nd$coefficients)",
        "  coef_vals <- as.numeric(nd$coefficients)",
        "  for (i in seq_along(coef_names)) {",
        '    cat("COEF\\t", coef_names[i],',
        '        "\\t", coef_vals[i], "\\n", sep="")',
        "  }",
        '  cat("SD\\t", nd$sd, "\\n", sep="")',
        "}",
    ]
    try:
        output = run_r_script("\n".join(script_lines) + "\n")
        nodes_list, node_data = _parse_bn_output(output)
        return _build_imported_bn(nodes_list, node_data)
    except (
        TypeError,
        FileNotFoundError,
        ValueError,
        RNotAvailableError,
        RRuntimeError,
    ):
        raise
    except Exception as exc:
        raise RRuntimeError(f"bnlearn_import failed: {exc}") from exc


def _build_imported_bn(nodes_list: List[str], node_data: Dict) -> BN:
    """Return a LinGauss BN from parsed bnlearn serialisation data.

    Args:
        nodes_list: Ordered node names.
        node_data: Per-node serialisation data.

    Returns:
        The reconstructed Bayesian Network.

    Raises:
        ValueError: If the data does not describe a LinGauss network.
    """
    arcs: List[Tuple[str, str, str]] = []
    cnd_specs: Dict = {}
    for node in nodes_list:
        info = node_data[node]
        coefs = dict(info["coefs"])
        parents = info["parents"]
        if set(coefs) != {"(Intercept)"} | set(parents):
            raise ValueError("bnlearn_import: invalid RDA file")
        mean = float(coefs.pop("(Intercept)"))
        cnd_specs[node] = (
            LinGauss,
            {"coeffs": coefs, "mean": mean, "sd": info["sd"]},
        )
        arcs += [(p, "->", node) for p in coefs]
    return BN(DAG(nodes_list, arcs), cnd_specs)


def _parse_bn_output(
    output: str,
) -> Tuple[List[str], Dict]:
    """Parse the tab-delimited BN serialisation output from R.

    Args:
        output: Stdout from the bnlearn_import R script.

    Returns:
        Tuple of (ordered node list, dict mapping node name to
        dict with keys 'coefs', 'parents', 'sd').
    """
    nodes_list: List[str] = []
    node_data: Dict = {}
    current_node: Optional[str] = None
    for raw_line in output.strip().split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("\t")
        current_node = _apply_bn_line(
            parts, nodes_list, node_data, current_node
        )
    return nodes_list, node_data


def _apply_bn_line(
    parts: List[str],
    nodes_list: List[str],
    node_data: Dict,
    current: Optional[str],
) -> Optional[str]:
    """Apply one tab-delimited BN line to the accumulated parse state.

    Args:
        parts: Tab-delimited fields of the line.
        nodes_list: Ordered node list, extended in place.
        node_data: Per-node serialisation data, updated in place.
        current: Node currently being described.

    Returns:
        The node being described once this line has been applied.
    """
    tag = parts[0]
    if tag == "NODE":
        nodes_list.append(parts[1])
        node_data[parts[1]] = {"coefs": {}, "parents": [], "sd": 0.0}
        return parts[1]
    if current is None:
        return current
    _apply_bn_node_line(node_data[current], parts)
    return current


def _apply_bn_node_line(node: Dict, parts: List[str]) -> None:
    """Apply one PARENTS, COEF or SD line to a node's serialisation data.

    Args:
        node: Serialisation data of the node being described.
        parts: Tab-delimited fields of the line.
    """
    tag = parts[0]
    if tag == "PARENTS":
        _set_bn_parents(node, parts)
        return
    if tag == "COEF":
        node["coefs"][parts[1]] = float(parts[2])
        return
    if tag == "SD":
        node["sd"] = float(parts[1])


def _set_bn_parents(node: Dict, parts: List[str]) -> None:
    """Record the parent list of a node from a PARENTS line.

    Args:
        node: Serialisation data of the node being described.
        parts: Tab-delimited fields of the line.
    """
    parent_str = parts[1] if len(parts) > 1 else ""
    if parent_str:
        node["parents"] = parent_str.split(",")
