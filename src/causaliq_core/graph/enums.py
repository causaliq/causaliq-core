"""
Graph-related enumerations for CausalIQ Core.
"""

from enum import Enum


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
