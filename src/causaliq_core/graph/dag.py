#
#   Directed Acyclic Graph (DAG) class
#

from typing import Generator, List, Tuple

from .pdag import PDAG, NotPDAGError


class NotDAGError(Exception):
    """Indicate graph is not a DAG when one is expected."""

    pass


class DAG(PDAG):
    """Directed Acyclic Graph (DAG).

    Args:
        nodes: Nodes present in the graph.
        edges: Edges which define the graph connections as list of tuples:
            (node1, dependency symbol, node2).

    Attributes:
        nodes: Graph nodes in alphabetical order.
        edges: Graph edges {(node1, node2): EdgeType}.
        is_directed: Always True for DAGs.
        parents: Parents of node {node: [parents]}.

    Raises:
        TypeError: If nodes and edges not both lists.
        ValueError: If node or edge invalid.
        NotDAGError: If graph is not a DAG.
    """

    def __init__(
        self, nodes: List[str], edges: List[Tuple[str, str, str]]
    ) -> None:
        """Initialize DAG.

        Args:
            nodes: Nodes present in the graph.
            edges: Edges which define the graph connections.

        Raises:
            NotDAGError: If graph is not a DAG.
        """
        try:
            PDAG.__init__(self, nodes, edges)
        except NotPDAGError:
            raise NotDAGError("graph is not a DAG")

        if not self.is_DAG():
            raise NotDAGError("graph is not a DAG")

    def ordered_nodes(self) -> Generator[str, None, None]:
        """Generator which returns nodes in a topological order.

        Yields:
            Next node in topological order.

        Raises:
            RuntimeError: If the graph has cycles (shouldn't happen for a DAG).
        """
        partial_ordering = self.partial_order(self.parents, self.nodes)
        if partial_ordering is None:
            raise RuntimeError("DAG has cycles - this should not happen")

        for group in partial_ordering:
            for node in sorted(list(group)):
                yield node

    def to_string(self) -> str:
        """Compact (bnlearn) string representation of DAG e.g. [A][B][C|A:B].

        Returns:
            Description of graph.
        """
        if not self.nodes:
            return ""

        result = ""
        for node in self.nodes:
            result += "[{}".format(node)
            result += (
                "|" + ":".join(self.parents[node])
                if node in self.parents
                else ""
            )
            result += "]"
        return result

    def __str__(self) -> str:
        """Return a human-readable description of the DAG.

        Returns:
            Description of DAG.
        """
        graph_desc = super().__str__()
        graph_desc = graph_desc.replace("SDG", "DAG", 1)
        return graph_desc
