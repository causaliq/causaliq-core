"""
Probabilistic Dependency Graph (PDG)

This module provides PDG (Probabilistic Dependency Graph) which represents
a probability distribution over edge states between node pairs. Unlike SDG
which stores a single deterministic edge type, PDG stores probabilities for
each possible edge state.

PDG is designed for:
- Graph averaging from multiple structure learning runs
- Fusing LLM-generated graphs with statistical structure learning
- Representing uncertainty in causal graph structure

The PDG class is independent of the SDG class hierarchy (not a subclass)
as it represents uncertainty over graphs rather than a single graph.
"""

from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple


@dataclass
class EdgeProbabilities:
    """Probability distribution over edge states between two nodes.

    Stores probabilities for each possible edge state. The edge is stored
    with source node alphabetically before target node (canonical form).

    Attributes:
        forward: P(source -> target) directed edge in stored direction.
        backward: P(target -> source) directed edge opposite to stored.
        undirected: P(source -- target) undirected edge.
        none: P(no edge between source and target).

    Raises:
        ValueError: If probabilities do not sum to 1.0 (within tolerance).

    Example:
        >>> probs = EdgeProbabilities(
        ...     forward=0.6, backward=0.2, undirected=0.1, none=0.1
        ... )
        >>> probs.p_exist
        0.9
        >>> probs.p_directed
        0.8
    """

    forward: float = 0.0
    backward: float = 0.0
    undirected: float = 0.0
    none: float = 1.0

    def __post_init__(self) -> None:
        """Validate probabilities sum to 1.0."""
        total = self.forward + self.backward + self.undirected + self.none
        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                f"Edge probabilities must sum to 1.0, got {total:.10f}"
            )
        # Validate all probabilities are non-negative
        if self.forward < 0 or self.backward < 0:
            raise ValueError("Edge probabilities must be non-negative")
        if self.undirected < 0 or self.none < 0:
            raise ValueError("Edge probabilities must be non-negative")

    @property
    def p_exist(self) -> float:
        """Probability that any edge exists between the nodes.

        Returns:
            Sum of forward, backward, and undirected probabilities.
        """
        return self.forward + self.backward + self.undirected

    @property
    def p_directed(self) -> float:
        """Probability of a directed edge (either direction).

        Returns:
            Sum of forward and backward probabilities.
        """
        return self.forward + self.backward

    def most_likely_state(self) -> str:
        """Return the most likely edge state.

        Returns:
            One of "forward", "backward", "undirected", or "none".
        """
        states = {
            "forward": self.forward,
            "backward": self.backward,
            "undirected": self.undirected,
            "none": self.none,
        }
        return max(states, key=lambda k: states[k])


class PDG:
    """Probabilistic Dependency Graph - distribution over SDG structures.

    Represents uncertainty over causal graph structure by storing probability
    distributions for each possible edge between node pairs. Unlike SDG,
    PDAG, and DAG which represent single deterministic graphs, PDG captures
    structural uncertainty.

    PDG is not a subclass of SDG because it represents a fundamentally
    different concept: a distribution over graphs rather than a single graph.

    Args:
        nodes: List of node names in the graph.
        edges: Dictionary mapping (source, target) pairs to EdgeProbabilities.
            Node pairs should be in canonical order (source < target
            alphabetically).

    Attributes:
        nodes: Graph nodes in alphabetical order.
        edges: Edge probabilities {(source, target): EdgeProbabilities}.

    Raises:
        TypeError: If nodes or edges have invalid types.
        ValueError: If edge keys are not in canonical order or reference
            unknown nodes.

    Example:
        >>> from causaliq_core.graph.pdg import PDG, EdgeProbabilities
        >>> nodes = ["A", "B", "C"]
        >>> edges = {
        ...     ("A", "B"): EdgeProbabilities(forward=0.8, none=0.2),
        ...     ("A", "C"): EdgeProbabilities(forward=0.6, backward=0.3,
        ...                                   none=0.1),
        ... }
        >>> pdg = PDG(nodes, edges)
        >>> pdg.get_probabilities("A", "B").forward
        0.8
    """

    def __init__(
        self,
        nodes: List[str],
        edges: Optional[Dict[Tuple[str, str], EdgeProbabilities]] = None,
    ) -> None:
        """Initialise a Probabilistic Dependency Graph.

        Args:
            nodes: List of node names.
            edges: Optional dictionary of edge probabilities. Keys must be
                tuples (source, target) where source < target alphabetically.
        """
        if not isinstance(nodes, list):
            raise TypeError("PDG nodes must be a list")
        for node in nodes:
            if not isinstance(node, str):
                raise TypeError("PDG node names must be strings")
            if not node:
                raise ValueError("PDG node names cannot be empty")

        # Store nodes in alphabetical order
        self.nodes: List[str] = sorted(set(nodes))

        if len(self.nodes) != len(nodes):
            raise ValueError("PDG has duplicate node names")

        # Validate and store edges
        self.edges: Dict[Tuple[str, str], EdgeProbabilities] = {}

        if edges is not None:
            if not isinstance(edges, dict):
                raise TypeError("PDG edges must be a dictionary")

            node_set = set(self.nodes)
            for (source, target), probs in edges.items():
                # Validate node pair
                if source not in node_set:
                    raise ValueError(f"Unknown source node: {source}")
                if target not in node_set:
                    raise ValueError(f"Unknown target node: {target}")
                if source == target:
                    raise ValueError(f"Self-loop not allowed: {source}")

                # Validate canonical order
                if source > target:
                    raise ValueError(
                        f"Edge ({source}, {target}) not in canonical order. "
                        f"Use ({target}, {source}) instead."
                    )

                if not isinstance(probs, EdgeProbabilities):
                    raise TypeError(
                        f"Edge ({source}, {target}) value must be "
                        "EdgeProbabilities"
                    )

                self.edges[(source, target)] = probs

    def get_probabilities(self, node_a: str, node_b: str) -> EdgeProbabilities:
        """Get edge probabilities between two nodes.

        Handles node ordering automatically - returns probabilities with
        forward/backward relative to alphabetical ordering.

        Args:
            node_a: First node name.
            node_b: Second node name.

        Returns:
            EdgeProbabilities for the node pair. If no explicit probabilities
            stored, returns EdgeProbabilities(none=1.0).

        Raises:
            ValueError: If either node is not in the graph.
        """
        if node_a not in self.nodes:
            raise ValueError(f"Unknown node: {node_a}")
        if node_b not in self.nodes:
            raise ValueError(f"Unknown node: {node_b}")
        if node_a == node_b:
            raise ValueError("Cannot get probabilities for self-loop")

        # Canonicalise order
        if node_a < node_b:
            key = (node_a, node_b)
            probs = self.edges.get(key)
            if probs is None:
                return EdgeProbabilities()  # Default: no edge
            return probs
        else:
            key = (node_b, node_a)
            probs = self.edges.get(key)
            if probs is None:
                return EdgeProbabilities()  # Default: no edge
            # Swap forward/backward for reversed order
            return EdgeProbabilities(
                forward=probs.backward,
                backward=probs.forward,
                undirected=probs.undirected,
                none=probs.none,
            )

    def set_probabilities(
        self, node_a: str, node_b: str, probs: EdgeProbabilities
    ) -> None:
        """Set edge probabilities between two nodes.

        Handles node ordering automatically.

        Args:
            node_a: First node name.
            node_b: Second node name.
            probs: Edge probabilities to set.

        Raises:
            ValueError: If either node is not in the graph.
            TypeError: If probs is not EdgeProbabilities.
        """
        if node_a not in self.nodes:
            raise ValueError(f"Unknown node: {node_a}")
        if node_b not in self.nodes:
            raise ValueError(f"Unknown node: {node_b}")
        if node_a == node_b:
            raise ValueError("Cannot set probabilities for self-loop")
        if not isinstance(probs, EdgeProbabilities):
            raise TypeError("probs must be EdgeProbabilities")

        # Canonicalise order
        if node_a < node_b:
            self.edges[(node_a, node_b)] = probs
        else:
            # Swap forward/backward for reversed order
            self.edges[(node_b, node_a)] = EdgeProbabilities(
                forward=probs.backward,
                backward=probs.forward,
                undirected=probs.undirected,
                none=probs.none,
            )

    def node_pairs(self) -> Iterator[Tuple[str, str]]:
        """Iterate over all possible node pairs in canonical order.

        Yields:
            Tuples (source, target) where source < target alphabetically.
        """
        for i, source in enumerate(self.nodes):
            for target in self.nodes[i + 1 :]:
                yield (source, target)

    def existing_edges(self) -> Iterator[Tuple[str, str, EdgeProbabilities]]:
        """Iterate over node pairs with non-zero edge probability.

        Yields:
            Tuples (source, target, probs) where p_exist > 0.
        """
        for (source, target), probs in self.edges.items():
            if probs.p_exist > 0:
                yield (source, target, probs)

    def __len__(self) -> int:
        """Return number of node pairs with explicit probabilities."""
        return len(self.edges)

    def __eq__(self, other: object) -> bool:
        """Check equality with another PDG."""
        if not isinstance(other, PDG):
            return False
        return self.nodes == other.nodes and self.edges == other.edges

    def __str__(self) -> str:
        """Return human-readable description of the PDG."""
        n_nodes = len(self.nodes)
        n_exist = sum(1 for _, _, p in self.existing_edges())
        return (
            f"PDG ({n_nodes} node{'s' if n_nodes != 1 else ''}, "
            f"{n_exist} edge{'s' if n_exist != 1 else ''} with p_exist > 0)"
        )

    def __repr__(self) -> str:
        """Return detailed representation of the PDG."""
        return f"PDG(nodes={self.nodes}, edges={self.edges})"
