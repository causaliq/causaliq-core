"""Data conversion utilities between CausalIQ and R types."""

from typing import Dict, List, Tuple

import numpy as np


def r_arcs_to_edges(
    arcs: List[Tuple[str, str]],
) -> List[Tuple[str, str, str]]:
    """Convert a list of (from, to) arc pairs to CausalIQ edge tuples.

    Opposing arc pairs — where both (A, B) and (B, A) are present —
    are collapsed into a single undirected edge. The alphabetically
    earlier node is used as the tail.

    Args:
        arcs: List of (from_node, to_node) string pairs, as parsed
              from bnlearn's write.table(arcs(...)) output.

    Returns:
        List of (tail, edge_type, head) tuples where edge_type is
        '->' for directed arcs or '-' for undirected edges.

    Examples:
        >>> r_arcs_to_edges([])
        []
    """
    arc_set = set(arcs)
    if not arc_set:
        return []
    return [
        (f, "-" if (t, f) in arc_set else "->", t)
        for f, t in arc_set
        if (t, f) not in arc_set or f < t
    ]


def data_to_r_dataframe(
    sample: np.ndarray,
    columns: List[str],
    node_types: Dict[str, str],
    varname: str = "df",
) -> str:
    """Generate R code that creates a data.frame from a NumPy array.

    Categorical columns (node_types value 'DISCRETE') become R
    factors; continuous columns become numeric vectors.

    Args:
        sample: 2-D NumPy array, shape (n_samples, n_variables).
        columns: Column names corresponding to sample's second axis.
        node_types: Mapping from column name to type string,
                    'CONTINUOUS' or 'DISCRETE'.
        varname: Name of the R variable to assign the data.frame to.

    Returns:
        R code string that assigns the data.frame to varname.

    Examples:
        >>> import numpy as np
        >>> code = data_to_r_dataframe(
        ...     np.array([[1.0, 2.0], [3.0, 4.0]]),
        ...     ['A', 'B'],
        ...     {'A': 'CONTINUOUS', 'B': 'CONTINUOUS'},
        ... )
        >>> 'data.frame' in code
        True
    """
    col_exprs = []
    for i, col in enumerate(columns):
        values = sample[:, i]
        vals_str = ", ".join(str(v) for v in values)
        if node_types.get(col, "CONTINUOUS") == "DISCRETE":
            col_exprs.append(f"  `{col}` = as.factor(c({vals_str}))")
        else:
            col_exprs.append(f"  `{col}` = c({vals_str})")
    body = ",\n".join(col_exprs)
    return f"{varname} <- data.frame(\n{body}\n)"
