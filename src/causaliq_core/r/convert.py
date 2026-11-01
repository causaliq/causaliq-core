"""Data conversion utilities between CausalIQ and R types."""

from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

# Maps a CausalIQ node type string to its R read.csv colClasses value.
_R_COL_CLASSES: Dict[str, str] = {
    "CONTINUOUS": "numeric",
    "COUNT": "numeric",
    "DISCRETE": "factor",
    "BINARY": "factor",
    "ORDINAL": "factor",
}

# Column class assumed for node types absent from _R_COL_CLASSES.
_DEFAULT_COL_CLASS = "numeric"


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

    Note:
        Each value is emitted as an R literal, which the R parser
        turns into a separate one-element vector before ``c()``
        combines them.  Parsing cost therefore grows faster than the
        sample size, so this is suitable only for small samples.  For
        large samples write the data with :func:`write_r_datafile` and
        read it back with :func:`datafile_to_r_code`.

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


def _r_col_class(node_type: str) -> str:
    """Return the quoted R colClasses value for a CausalIQ node type.

    Args:
        node_type: Node type string, e.g. 'CONTINUOUS' or 'DISCRETE'.

    Returns:
        Quoted R colClasses value, e.g. '"numeric"' or '"factor"'.
    """
    return '"' + _R_COL_CLASSES.get(node_type, _DEFAULT_COL_CLASS) + '"'


def _r_col_classes(
    columns: Sequence[str],
    node_types: Dict[str, str],
) -> str:
    """Return an R colClasses vector expression for the given columns.

    Args:
        columns: Column names in file order.
        node_types: Mapping from column name to type string.  Columns
            without an entry are treated as continuous.

    Returns:
        R vector expression, e.g. ``c("factor", "numeric")``.
    """
    classes = [_r_col_class(node_types.get(c, "CONTINUOUS")) for c in columns]
    return "c(" + ", ".join(classes) + ")"


def _r_path_literal(path: str) -> str:
    """Return an R string literal for a filesystem path.

    R treats a backslash inside a string literal as an escape
    character, so Windows paths are converted to forward slashes.

    Args:
        path: Filesystem path.

    Returns:
        Double-quoted R string literal for the path.
    """
    escaped = path.replace("\\", "/").replace('"', '\\"')
    return f'"{escaped}"'


def write_r_datafile(
    sample: np.ndarray,
    columns: Sequence[str],
    path: str,
) -> None:
    """Write a sample matrix to a CSV datafile for R to read.

    R parses a CSV datafile with a linear C-level reader, whereas
    serialising values as R source code makes the R parser build a
    one-element vector for every value.  Reading a datafile is
    therefore orders of magnitude faster for large samples and keeps
    R memory use proportional to the data rather than to the number of
    parsed expressions.

    Args:
        sample: 2-D NumPy array, shape (n_samples, n_variables).
        columns: Column names corresponding to sample's second axis.
        path: Full path of the CSV file to create.

    Raises:
        ValueError: If columns and sample have different lengths.
    """
    if len(columns) != sample.shape[1]:
        raise ValueError("write_r_datafile() columns/sample mismatch")
    pd.DataFrame(sample, columns=list(columns)).to_csv(path, index=False)


def datafile_to_r_code(
    path: str,
    columns: Sequence[str],
    node_types: Dict[str, str],
    varname: str = "df",
) -> str:
    """Return R code that reads a CSV datafile into a data.frame.

    Categorical columns ('DISCRETE', 'BINARY', 'ORDINAL') become R
    factors and continuous columns ('CONTINUOUS', 'COUNT') become
    numeric vectors, matching :func:`data_to_r_dataframe`.  Column
    names are preserved verbatim (``check.names = FALSE``) so that
    node names returned by R match those supplied by the caller.

    Args:
        path: Full path of the CSV datafile written by
            :func:`write_r_datafile`.
        columns: Column names in file order.
        node_types: Mapping from column name to type string.  Columns
            without an entry are treated as continuous.
        varname: Name of the R variable to assign the data.frame to.

    Returns:
        R source line assigning the data.frame to varname.

    Examples:
        >>> code = datafile_to_r_code(
        ...     "C:/tmp/data.csv", ["A"], {"A": "DISCRETE"}
        ... )
        >>> 'read.csv' in code
        True
    """
    classes = _r_col_classes(columns, node_types)
    return (
        f"{varname} <- read.csv({_r_path_literal(path)}, "
        f"colClasses = {classes}, check.names = FALSE)"
    )
