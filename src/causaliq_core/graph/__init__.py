"""
Graph-related enums and utilities for CausalIQ Core.
"""

from enum import Enum
from typing import Dict, List, Optional

from pandas import DataFrame

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


class EdgeMark(Enum):
    """Supported 'ends' of an edge in a graph."""

    NONE = 0
    LINE = 1
    ARROW = 2
    CIRCLE = 3


class EdgeType(Enum):
    """Supported edge types and their symbols."""

    NONE = (0, EdgeMark.NONE, EdgeMark.NONE, "")
    DIRECTED = (1, EdgeMark.LINE, EdgeMark.ARROW, "->")
    UNDIRECTED = (2, EdgeMark.LINE, EdgeMark.LINE, "-")
    BIDIRECTED = (3, EdgeMark.ARROW, EdgeMark.ARROW, "<->")
    SEMIDIRECTED = (4, EdgeMark.CIRCLE, EdgeMark.ARROW, "o->")
    NONDIRECTED = (5, EdgeMark.CIRCLE, EdgeMark.CIRCLE, "o-o")
    SEMIUNDIRECTED = (6, EdgeMark.CIRCLE, EdgeMark.LINE, "o-")


# Export public interface
__all__ = ["EdgeType", "EdgeMark", "adjmat", "SDG", "BAYESYS_VERSIONS"]
