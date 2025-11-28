#
#   Partially Directed Acyclic Graph (PDAG) class
#

from typing import List, Tuple

from .sdg import SDG


class NotPDAGError(Exception):
    """Indicate graph is not a PDAG when one is expected."""

    pass


class PDAG(SDG):
    """Partially directed acyclic graph (PDAG).

    Args:
        nodes: Nodes present in the graph.
        edges: Edges which define the graph connections as list of tuples:
            (node1, dependency symbol, node2).

    Attributes:
        nodes: Graph nodes in alphabetical order.
        edges: Graph edges {(node1, node2): EdgeType}.
        is_directed: Graph only has directed (causal) edges.
        parents: Parents of node {node: [parents]}.

    Raises:
        TypeError: If nodes and edges not both lists.
        ValueError: If node or edge invalid.
        NotPDAGError: If graph is not a PDAG.
    """

    def __init__(
        self, nodes: List[str], edges: List[Tuple[str, str, str]]
    ) -> None:
        """Initialize PDAG.

        Args:
            nodes: Nodes present in the graph.
            edges: Edges which define the graph connections.

        Raises:
            NotPDAGError: If graph is not a PDAG.
        """
        SDG.__init__(self, nodes, edges)

        if not self.is_PDAG():
            raise NotPDAGError("graph is not a PDAG")

    def edge_reversible(self, edge: Tuple[str, str]) -> bool:
        """Return whether specified edge is in CPDAG and is reversible.

        Args:
            edge: Edge to examine, (node1, node2).

        Returns:
            Whether present and reversible, or not.

        Raises:
            TypeError: If edge argument has bad type.
        """
        from causaliq_core.graph import EdgeType

        if (
            not isinstance(edge, tuple)
            or not len(edge) == 2
            or not isinstance(edge[0], str)
            or not isinstance(edge[1], str)
        ):
            raise TypeError("PDAG.edge_reversible() bad arg type")

        e = (min(edge), max(edge))
        return e in self.edges and self.edges[e] == EdgeType.UNDIRECTED
