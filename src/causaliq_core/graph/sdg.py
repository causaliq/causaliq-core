"""
Simple Dependency Graph (SDG)

This module supports Simple Dependency Graphs (SDGs) which are a general
form of graph that has at most one edge between any pair of nodes.

The two endpoints of each edge can be a head ">", tail "-" or circle "o"
(which means either head or tail).

This format can represent most dependency graph types including:
 - Markov Graphs
 - Directed Acyclic Graphs (DAGs)
 - Partially Directed Acyclic Graphs (PDAGs)
 - Maximal Ancestral Graphs (MAGs)
 - Partial Ancestral Graphs (PAGs)
"""

from typing import Dict, List, Optional, Set, Tuple, Union

from numpy import zeros
from pandas import DataFrame

from .enums import EdgeType
from .sdg_codec import decode_sdg, encode_sdg
from .sdg_traversal import (
    grow_component,
    grow_undirected_tree,
    layout_partial_order,
    undirected_edge_pairs,
)


class SDG:
    """Base class for simple dependency graphs (one edge between vertices).

    Simple Dependency Graphs (SDGs) are a general form of graph that has at
    most one edge between any pair of nodes. The two endpoints of each edge
    can be a     head ">", tail "-" or circle "o" (which means either
    head or tail).

    This format can represent most dependency graph types including:
    - Markov Graphs
    - Directed Acyclic Graphs (DAGs)
    - Partially Directed Acyclic Graphs (PDAGs)
    - Maximal Ancestral Graphs (MAGs)
    - Partial Ancestral Graphs (PAGs)

    Args:
        nodes: Nodes present in the graph.
        edges: Edges which define the graph connections as list of tuples:
            (node1, dependency symbol, node2).

    Attributes:
        nodes: Graph nodes in alphabetical order.
        edges: Graph edges {(node1, node2): EdgeType}.
        is_directed: Graph only has directed (causal) edges.
        is_partially_directed: Graph is partially directed.
        parents: Parents of node {node: [parents]}.
        has_directed_cycles: Contains any directed cycles.

    Raises:
        TypeError: If nodes and edges are not both lists.
        ValueError: If node or edge is invalid.
    """

    def __init__(
        self, nodes: List[str], edges: List[Tuple[str, str, str]]
    ) -> None:
        """Initialize a Simple Dependency Graph.

        Args:
            nodes: List of node names in the graph.
            edges: List of edge tuples in format
                (node1, edge_type_symbol, node2).
        """
        if type(nodes) is not list or type(edges) is not list:
            raise TypeError("graph edges and nodes not both lists")

        # Validate nodes specified

        self.nodes: List[str] = _validate_sdg_nodes(nodes)

        self.edges: Dict[Tuple[str, str], EdgeType] = {}
        edge_types = {e.value[3]: e for e in EdgeType}
        self.is_directed: bool = True
        self.is_partially_directed: bool = True
        self.parents: Dict[str, List[str]] = {}
        self.has_directed_cycles: bool = False

        for edge in edges:
            self._add_edge(edge, edge_types)

    def _add_edge(
        self, edge: Tuple[str, str, str], edge_types: Dict[str, EdgeType]
    ) -> None:
        """Validate and store one edge of the graph.

        Args:
            edge: Edge tuple (node1, edge_type_symbol, node2).
            edge_types: Mapping of edge type symbol to EdgeType.

        Raises:
            TypeError: If the edge or its parts have invalid types.
            ValueError: If the edge is cyclic, unknown or duplicated.
        """
        _validate_sdg_edge(edge, edge_types, self.nodes, self.edges)

        # Check if graph directed or partially directed
        edge_type = edge_types[edge[1]]
        if edge_type != EdgeType.DIRECTED:
            self.is_directed = False
            if edge_type != EdgeType.UNDIRECTED:
                self.is_partially_directed = False

        if edge_type == EdgeType.DIRECTED:
            # collect parents for directional links
            self._add_parent(edge[2], edge[0])
        elif _is_reversed_non_directed(edge_type, edge):
            # ensure nodes in alphabetical order for non-directional edges
            edge = (edge[2], edge[1], edge[0])

        # parents held in alphabetical order
        self.parents = {k: sorted(v) for k, v in self.parents.items()}

        # store the edge in dictionary {(node1, node2): edge_type}
        self.edges[(edge[0], edge[2])] = edge_type

        # see whether has directed cycles
        self.has_directed_cycles = (
            self.partial_order(self.parents, self.nodes) is None
        )

    def _add_parent(self, node: str, parent: str) -> None:
        """Record a parent for a node.

        Args:
            node: Node that gains a parent.
            parent: Name of the parent node.
        """
        if node in self.parents:
            self.parents[node].append(parent)
            return
        self.parents[node] = [parent]

    def rename(self, name_map: Dict[str, str]) -> None:
        """Rename nodes in place according to name map.

        Args:
            name_map: Name mapping {name: new name}. Must have mapping for
                every node.

        Raises:
            TypeError: With bad arg type.
            ValueError: With bad arg values e.g. unknown node names.
        """
        if not isinstance(name_map, dict) or not all(
            [
                isinstance(k, str) and isinstance(v, str)
                for k, v in name_map.items()
            ]
        ):
            raise TypeError("SDG.rename() bad arg types")

        if set(name_map.keys()) != set(self.nodes):
            raise ValueError("SDG.raname() bad arg values")

        # Change node names and node names in edges

        nodes = [name_map[n] if n in name_map else n for n in self.nodes]
        edges = [
            (
                (name_map[e[0]] if e[0] in name_map else e[0]),
                t.value[3],
                (name_map[e[1]] if e[1] in name_map else e[1]),
            )
            for e, t in self.edges.items()
        ]

        # Re-instantiate object with new names
        new_sdg = SDG(nodes, edges)
        self.nodes = new_sdg.nodes
        self.edges = new_sdg.edges
        self.is_directed = new_sdg.is_directed
        self.is_partially_directed = new_sdg.is_partially_directed
        self.parents = new_sdg.parents
        self.has_directed_cycles = new_sdg.has_directed_cycles

    @classmethod
    def partial_order(
        cls,
        parents: Dict[str, List[str]],
        nodes: Optional[Union[List[str], Set[str]]] = None,
        new_arc: Optional[Tuple[str, str]] = None,
    ) -> Optional[List[Set[str]]]:
        """Return partial topological ordering for the directed part of a
        graph.

        The graph is specified by list of parents for each node.

        Args:
            parents: Parents of each node {node: [parents]}.
            nodes: Optional complete list of nodes including parentless ones
                for use if parents argument doesn't include them already.
            new_arc: A new arc (n1, n2) to be added before order is evaluated.
                If the opposing arc is implied in parents then it is removed so
                that arc reversal is also supported. This argument facilitates
                seeing whether an arc addition or reversal would create a
                cycle.

        Returns:
            Nodes in a partial topological order as list of sets or None if
            there is no ordering which means the graph is cyclic.
        """
        return layout_partial_order(parents, nodes, new_arc)

    def is_DAG(self) -> bool:
        """Return whether graph is a Directed Acyclic Graph (DAG).

        Returns:
            True if graph is a DAG, False otherwise.
        """
        return self.is_directed and self.has_directed_cycles is False

    def is_PDAG(self) -> bool:
        """Return whether graph is a Partially Directed Acyclic Graph (PDAG).

        Returns:
            True if graph is a PDAG, False otherwise.
        """
        from causaliq_core.graph import EdgeType

        if self.is_directed:
            return self.is_DAG()

        if not self.is_partially_directed:
            return False

        # Check if there are any cycles in directed part of graph

        arcs = [
            (a[0], "->", a[1])
            for a, t in self.edges.items()
            if t == EdgeType.DIRECTED
        ]
        return not SDG(self.nodes, arcs).has_directed_cycles

    def undirected_trees(
        self,
    ) -> List[Set[Union[Tuple[str, str], Tuple[str, None]]]]:
        """Return undirected trees present in graph.

        Returns:
            List of trees, each tree a set of tuples representing edges in tree
            (n1, n2) or a single isolated node (n1, None).
        """
        trees = []
        edges = undirected_edge_pairs(self.edges.keys())
        isolated = set(self.nodes)
        while len(edges):
            # Start with the lexicographically smallest edge for determinism
            first_edge = min(edges)
            tree, t_nodes = grow_undirected_tree(first_edge, edges)

            # Remove only the actual edges (not isolated nodes) from edges set
            tree_edges = {edge for edge in tree if edge[1] is not None}
            edges = edges - tree_edges
            isolated = isolated - t_nodes
            trees.append(tree)

        # Sort for determinism
        trees.extend([{(n, None)} for n in sorted(isolated)])
        return sorted(trees, key=lambda t: min(t))

    def components(self) -> List[List[str]]:
        """Return components present in graph.

        Uses tree search algorithm to span the undirected graph to identify
        nodes in individual trees which are the spanning tree of each
        component.

        Returns:
            List of lists, each a list of sorted nodes in component.
        """
        components = []
        edges = undirected_edge_pairs(self.edges.keys())  # skeleton
        nodes = set(self.nodes)  # nodes yet to be included in components

        while len(nodes):
            # put 1st arbitrary node in component, then grow the component
            c_nodes = grow_component({list(nodes)[0]}, edges)

            # component identified, remove its nodes from consideration
            nodes = nodes - c_nodes
            components.append(sorted(c_nodes))

        return sorted(components)

    def number_components(self) -> int:
        """Return number of components (including unconnected nodes) in graph.

        Returns:
            Number of components.
        """
        return len(self.components())

    def to_adjmat(self) -> DataFrame:
        """Return an adjacency matrix representation of the graph.

        Returns:
            Adjacency matrix as a pandas DataFrame.
        """
        size = len(self.nodes)
        adjmat: DataFrame = DataFrame(
            zeros(shape=(size, size), dtype="int8"), columns=self.nodes
        )
        adjmat[""] = self.nodes
        adjmat = adjmat.set_index("")
        for nodes, type in self.edges.items():
            # print('{}: {}'.format(nodes, type.value[0]))
            adjmat.loc[nodes[0], nodes[1]] = type.value[0]

        return adjmat

    def __str__(self) -> str:
        """Return a human-readable description of the graph.

        Returns:
            String description of graph.
        """
        if not self.nodes:
            return "Empty graph"

        number_components = self.number_components()
        kind = (
            "DAG"
            if self.is_directed
            else ("PDAG" if self.is_partially_directed else "SDG")
        )
        desc = (
            "{} ({}), {} node".format(kind, type(self), len(self.nodes))
            + ("" if len(self.nodes) == 1 else "s")
            + ", {} edge".format(len(self.edges))
            + ("" if len(self.edges) == 1 else "s")
            + " and {} component".format(number_components)
            + ("" if number_components == 1 else "s")
        )

        for node in self.nodes:
            children = [
                t.value[3] + str(e[1])
                for e, t in self.edges.items()
                if e[0] == node
            ]
            desc += "\n{}: {}".format(node, " ".join(children))
        return desc

    def __eq__(self, other: object) -> bool:
        """Test if graph is identical to this one.

        Args:
            other: Graph to compare with self.

        Returns:
            True if other is identical to self.
        """
        return (
            isinstance(other, SDG)
            and self.nodes == other.nodes
            and self.edges == other.edges
        )

    def compress(self) -> bytes:
        """Compress graph to compact binary representation.

        Format:

        - 2 bytes: number of nodes (uint16, big-endian)
        - For each node: 2 bytes name length + UTF-8 encoded name
        - 2 bytes: number of edges (uint16, big-endian)
        - For each edge: 2 bytes source index + 2 bytes target index +
          1 byte edge type

        Returns:
            Compact binary representation of the graph.

        Raises:
            ValueError: If graph has more than 65535 nodes or edges.
        """
        return encode_sdg(self.nodes, self.edges)

    @classmethod
    def decompress(cls, data: bytes) -> "SDG":
        """Decompress graph from compact binary representation.

        Args:
            data: Binary data from SDG.compress().

        Returns:
            Reconstructed SDG instance.

        Raises:
            TypeError: If data is not bytes.
            ValueError: If data is invalid or corrupted.
        """
        nodes, edges = decode_sdg(data)
        return cls(nodes, edges)


def _validate_sdg_nodes(nodes: List[str]) -> List[str]:
    """Return the validated, alphabetically sorted node names.

    Args:
        nodes: Node names supplied to the graph.

    Returns:
        Sorted node names.

    Raises:
        TypeError: If a node name is not a string.
        ValueError: If a node name is empty or duplicated.
    """
    validated: List[str] = []
    for node in nodes:
        if type(node) is not str:
            raise TypeError("graph has non-string node name")
        if not node:
            raise ValueError("graph has empty node name")
        if node in validated:
            raise ValueError("graph has duplicate node names")
        validated.append(node)
    validated.sort()
    return validated


def _validate_sdg_edge(
    edge: Tuple[str, str, str],
    edge_types: Dict[str, EdgeType],
    nodes: List[str],
    edges: Dict[Tuple[str, str], EdgeType],
) -> None:
    """Validate one edge of a simple dependency graph.

    Args:
        edge: Edge tuple (node1, edge_type_symbol, node2).
        edge_types: Mapping of edge type symbol to EdgeType.
        nodes: Nodes already accepted into the graph.
        edges: Edges already accepted into the graph.

    Raises:
        TypeError: If the edge or its parts have invalid types.
        ValueError: If the edge is cyclic, unknown or duplicated.
    """
    if type(edge) is not tuple or len(edge) != 3:
        raise TypeError("graph has non-triple edge")
    for part in edge:
        if type(part) is not str:
            raise TypeError("graph has non-string edge triple")
    if edge[0] == edge[2]:
        raise ValueError("graph has cyclic edge")
    if edge[1] not in edge_types:
        raise TypeError(
            'graph edge has unknown type symbol: "{}"'.format(edge[1])
        )
    if edge[0] not in nodes or edge[2] not in nodes:
        raise ValueError("graph edge has unknown node")
    if (edge[0], edge[2]) in edges or (edge[2], edge[0]) in edges:
        raise ValueError("graph has duplicate edges")


def _is_reversed_non_directed(
    edge_type: EdgeType, edge: Tuple[str, str, str]
) -> bool:
    """Return whether a non-directed edge needs its nodes reordering.

    Args:
        edge_type: Type of the edge.
        edge: Edge tuple (node1, edge_type_symbol, node2).

    Returns:
        bool: Whether the edge nodes are not in alphabetical order.
    """
    if edge_type not in (
        EdgeType.UNDIRECTED,
        EdgeType.BIDIRECTED,
        EdgeType.NONDIRECTED,
    ):
        return False
    return edge[0] > edge[2]
