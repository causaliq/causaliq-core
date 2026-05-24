"""Data conversion utilities between CausalIQ and R types."""

from typing import Any, Dict, List, Tuple

import numpy as np

from causaliq_core.r.session import get_robjects


def r_arcs_to_edges(arcs_r: Any) -> List[Tuple[str, str, str]]:
    """Convert a bnlearn arcs R matrix to CausalIQ edge tuples.

    The input is the column-major character matrix returned by
    bnlearn::arcs(). The first half of elements are 'from' nodes;
    the second half are 'to' nodes. Undirected edges appear as two
    opposing arcs in bnlearn and are collapsed to a single '-' tuple.

    Args:
        arcs_r: R character matrix from bnlearn.arcs(), or any
                sequence supporting len() and integer indexing with
                column-major layout.

    Returns:
        List of (tail, edge_type, head) tuples where edge_type is
        '->' for directed arcs or '-' for undirected edges.

    Examples:
        >>> r_arcs_to_edges([])
        []
    """
    n = len(arcs_r) // 2
    if n == 0:
        return []
    froms = [str(arcs_r[i]) for i in range(n)]
    tos = [str(arcs_r[n + i]) for i in range(n)]
    arc_set = set(zip(froms, tos))
    return [
        (f, "-" if (t, f) in arc_set else "->", t)
        for f, t in arc_set
        if (t, f) not in arc_set or f < t
    ]


def data_to_r_dataframe(
    sample: np.ndarray,
    columns: List[str],
    node_types: Dict[str, str],
) -> Any:
    """Convert a NumPy sample array to an R data.frame.

    Categorical columns (node_types value 'DISCRETE') become R
    factors; continuous columns become numeric vectors.

    Args:
        sample: 2-D NumPy array, shape (n_samples, n_variables).
        columns: Column names corresponding to sample's second axis.
        node_types: Mapping from column name to type string,
                    'CONTINUOUS' or 'DISCRETE'.

    Raises:
        RNotAvailableError: If R or rpy2 is not available.

    Returns:
        An rpy2 DataFrame representing the data.

    Examples:
        >>> import numpy as np
        >>> data_to_r_dataframe(
        ...     np.array([[1.0, 2.0], [3.0, 4.0]]),
        ...     ['A', 'B'],
        ...     {'A': 'CONTINUOUS', 'B': 'CONTINUOUS'},
        ... )  # doctest: +SKIP
    """
    ro = get_robjects()
    r_cols: Dict[str, object] = {}
    for i, col in enumerate(columns):
        values = sample[:, i]
        if node_types.get(col, "CONTINUOUS") == "DISCRETE":
            r_cols[col] = ro.FactorVector(
                ro.StrVector([str(int(v)) for v in values])
            )
        else:
            r_cols[col] = ro.FloatVector(values.tolist())
    return ro.DataFrame(r_cols)
