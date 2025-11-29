"""
Graph-related enums and utilities for CausalIQ Core.
"""

from typing import Dict, List, Optional

from pandas import DataFrame

# Import conversion functions
from .convert import dag_to_pdag, extend_pdag, is_cpdag, pdag_to_cpdag
from .dag import DAG, NotDAGError

# Import enums
from .enums import EdgeMark, EdgeType
from .pdag import PDAG, NotPDAGError

# Import graph classes - moved to top to fix E402
from .sdg import SDG

# Supported BayeSys versions for graph comparison semantics
BAYESYS_VERSIONS = ["v1.3", "v1.5+"]


def adjmat(columns: Optional[Dict[str, List[int]]] = None) -> DataFrame:
    """
    Create an adjacency matrix with specified entries.

    :param dict columns: data for matrix specified by column

    :raises TypeError: if arg types incorrect
    :raises ValueError: if values specified are invalid

    :returns DataFrame: the adjacency matrix
    """
    if (
        columns is None
        or not isinstance(columns, dict)
        or not all([isinstance(c, list) for c in columns.values()])
        or not all([isinstance(e, int) for c in columns.values() for e in c])
    ):
        raise TypeError("adjmat called with bad arg type")

    if not all([len(c) == len(columns) for c in columns.values()]):
        raise ValueError("some columns wrong length for adjmat")

    valid = [e.value[0] for e in EdgeType]  # valid edge integer codes
    if not all([e in valid for c in columns.values() for e in c]):
        raise ValueError("invalid integer values for adjmat")

    adjmat_df = DataFrame(columns, dtype="int8")
    adjmat_df[""] = list(adjmat_df.columns)
    return adjmat_df.set_index("")


# Export public interface
__all__ = [
    "EdgeType",
    "EdgeMark",
    "adjmat",
    "SDG",
    "PDAG",
    "NotPDAGError",
    "DAG",
    "NotDAGError",
    "dag_to_pdag",
    "pdag_to_cpdag",
    "extend_pdag",
    "is_cpdag",
    "BAYESYS_VERSIONS",
]
