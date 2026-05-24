"""bnlearn graph utilities ported from legacy call/bnlearn.py."""

import os
from typing import Any, Dict, List, Tuple

from causaliq_core.bn import BN, LinGauss
from causaliq_core.graph import DAG, PDAG, EdgeType
from causaliq_core.r.convert import r_arcs_to_edges
from causaliq_core.r.exceptions import (
    RNotAvailableError,
    RPackageNotAvailableError,
    RRuntimeError,
)
from causaliq_core.r.session import get_robjects, import_r_package


def _build_r_network(bnl: Any, pdag: PDAG) -> Any:
    """Build an rpy2 bnlearn network object from a CausalIQ PDAG.

    Args:
        bnl: The imported bnlearn R package object.
        pdag: The PDAG to convert.

    Returns:
        rpy2 bn object representing the same graph.
    """
    nodes_str = "".join(f"[{n}]" for n in pdag.nodes)
    net = bnl.model2network(nodes_str)
    for (tail, head), etype in pdag.edges.items():
        if etype == EdgeType.DIRECTED:
            net = bnl.set_arc(net, tail, head)
        else:
            net = bnl.set_edge(net, tail, head)
    return net


def bnlearn_cpdag(pdag: PDAG) -> PDAG:
    """Return CPDAG corresponding to supplied PDAG via bnlearn.

    Args:
        pdag: PDAG to transform to CPDAG.

    Raises:
        TypeError: If pdag is not a PDAG instance.
        ValueError: If pdag is empty.
        RNotAvailableError: If R or rpy2 is not available.
        RPackageNotAvailableError: If bnlearn is not installed.
        RRuntimeError: If bnlearn raises an R runtime error.

    Returns:
        CPDAG corresponding to the pdag argument.
    """
    if not isinstance(pdag, PDAG):
        raise TypeError("bnlearn_cpdag: pdag must be a PDAG instance")
    if not pdag.nodes:
        raise ValueError("bnlearn_cpdag: pdag must not be empty")
    try:
        bnl = import_r_package("bnlearn")
        net = _build_r_network(bnl, pdag)
        cpdag_r = bnl.cpdag(net)
        arcs_r = bnl.arcs(cpdag_r)
        edges = r_arcs_to_edges(arcs_r)
    except (
        TypeError,
        ValueError,
        RNotAvailableError,
        RPackageNotAvailableError,
    ):
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
        RNotAvailableError: If R or rpy2 is not available.
        RPackageNotAvailableError: If bnlearn is not installed.
        RRuntimeError: If bnlearn raises an R runtime error.

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
    try:
        bnl = import_r_package("bnlearn")
        net = _build_r_network(bnl, pdag)
        ref_net = _build_r_network(bnl, ref)
        metrics_r = bnl.compare(ref_net, net)
        shd_r = bnl.shd(ref_net, net)
        return {
            "tp": int(metrics_r.rx2("tp")[0]),
            "fp": int(metrics_r.rx2("fp")[0]),
            "fn": int(metrics_r.rx2("fn")[0]),
            "shd": int(shd_r[0]),
        }
    except (
        TypeError,
        ValueError,
        RNotAvailableError,
        RPackageNotAvailableError,
    ):
        raise
    except Exception as exc:
        raise RRuntimeError(f"bnlearn_compare failed: {exc}") from exc


def bnlearn_import(rda_path: str) -> BN:
    """Import a LinGauss BN from a bnlearn .rda file.

    Only supports continuous (LinGauss) Bayesian Networks. The .rda
    file must contain an R variable named 'bn' of type bn.fit.

    Args:
        rda_path: Absolute path to the .rda file.

    Raises:
        TypeError: If rda_path is not a string.
        FileNotFoundError: If the .rda file does not exist.
        ValueError: If the file cannot be parsed as a valid LinGauss BN.
        RNotAvailableError: If R or rpy2 is not available.
        RPackageNotAvailableError: If bnlearn is not installed.
        RRuntimeError: If bnlearn raises an R runtime error.

    Returns:
        BN object reconstructed from the .rda file.
    """
    if not isinstance(rda_path, str):
        raise TypeError("bnlearn_import: rda_path must be a string")
    if not os.path.isfile(rda_path):
        raise FileNotFoundError(f"bnlearn_import: file not found: {rda_path}")
    try:
        ro = get_robjects()
        import_r_package("bnlearn")
        ro.r["load"](rda_path)
        bn_r = ro.globalenv["bn"]
        node_names: List[str] = list(bn_r.names)
        arcs: List[Tuple[str, str, str]] = []
        cnd_specs: Dict = {}
        for node in node_names:
            node_data = bn_r.rx2(node)
            parents_r = node_data.rx2("parents")
            parents = [str(p) for p in parents_r] if len(parents_r) > 0 else []
            coeffs_r = node_data.rx2("coefficients")
            coeffs = {
                str(k): float(v)
                for k, v in zip(list(coeffs_r.names), list(coeffs_r))
            }
            sd = float(node_data.rx2("sd")[0])
            if set(coeffs) != {"(Intercept)"} | set(parents):
                raise ValueError("bnlearn_import: invalid RDA file")
            mean = float(coeffs.pop("(Intercept)"))
            cnd_specs[node] = (
                LinGauss,
                {"coeffs": coeffs, "mean": mean, "sd": sd},
            )
            arcs += [(p, "->", node) for p in coeffs]
        return BN(DAG(node_names, arcs), cnd_specs)
    except (
        TypeError,
        FileNotFoundError,
        ValueError,
        RNotAvailableError,
        RPackageNotAvailableError,
    ):
        raise
    except Exception as exc:
        raise RRuntimeError(f"bnlearn_import failed: {exc}") from exc
