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
from typing import (
    TYPE_CHECKING,
    Dict,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Tuple,
)

if TYPE_CHECKING:  # pragma: no cover
    from .dag import DAG


class GreedyDAGResult(NamedTuple):
    """Result from PDG.to_dag_greedy().

    Attributes:
        dag: The extracted DAG.
        edges_included: Number of edges added to the DAG.
        edges_skipped_cycle: Edges skipped to avoid cycles.
        edges_skipped_threshold: Edges below threshold.
        tie_breaks_applied: Edges where alphabetical tie-break was used.
    """

    dag: "DAG"
    edges_included: int
    edges_skipped_cycle: int
    edges_skipped_threshold: int
    tie_breaks_applied: int


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
        # Use 1e-6 tolerance to account for GraphML text serialisation
        # round-trips (8 sig figs per float, 4 floats = ~1e-7 worst case)
        if abs(total - 1.0) > 1e-6:
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

    def to_dag_greedy(self, threshold: float = 0.0) -> GreedyDAGResult:
        """Extract a DAG from PDG using greedy algorithm.

        Greedily adds edges in order of probability, choosing directions
        based on effective probability (splitting undirected probability
        equally between forward and backward). Edges that would create
        cycles are skipped.

        For ties where effective forward equals effective backward,
        alphabetical ordering is used (source < target).

        Args:
            threshold: Minimum p_exist to consider an edge (default 0.0).

        Returns:
            GreedyDAGResult containing the DAG and extraction statistics.

        Example:
            >>> pdg = PDG(["A", "B", "C"], {
            ...     ("A", "B"): EdgeProbabilities(forward=0.7, none=0.3),
            ...     ("A", "C"): EdgeProbabilities(forward=0.5, none=0.5),
            ... })
            >>> result = pdg.to_dag_greedy()
            >>> result.edges_included
            2
        """
        # Import here to avoid circular import
        from .dag import DAG

        # Collect candidate edges with effective probabilities
        candidates = []
        edges_skipped_threshold = 0

        for (source, target), probs in self.edges.items():
            p_exist = probs.p_exist
            if p_exist < threshold:
                edges_skipped_threshold += 1
                continue

            # Split undirected probability equally between directions
            eff_forward = probs.forward + probs.undirected / 2
            eff_backward = probs.backward + probs.undirected / 2

            # Determine direction and whether tie-break was needed
            if eff_forward > eff_backward:
                direction = "forward"
                max_prob = eff_forward
                is_tie = False
            elif eff_backward > eff_forward:
                direction = "backward"
                max_prob = eff_backward
                is_tie = False
            else:
                # Tie - use alphabetical (forward means source -> target)
                direction = "forward"
                max_prob = eff_forward
                is_tie = True

            candidates.append((max_prob, source, target, direction, is_tie))

        # Sort by probability descending (stable sort preserves order for ties)
        candidates.sort(key=lambda x: -x[0])

        # Greedily build DAG
        dag_edges: List[Tuple[str, str, str]] = []
        ancestors: Dict[str, set] = {node: set() for node in self.nodes}
        edges_included = 0
        edges_skipped_cycle = 0
        tie_breaks_applied = 0

        for _, source, target, direction, is_tie in candidates:
            # Determine actual edge direction
            if direction == "forward":
                from_node, to_node = source, target
            else:
                from_node, to_node = target, source

            # Check if adding this edge would create a cycle
            # A cycle occurs if to_node is already an ancestor of from_node
            # (i.e., there's already a path from to_node to from_node)
            if to_node in ancestors[from_node] or from_node == to_node:
                edges_skipped_cycle += 1
                continue

            # Add edge
            dag_edges.append((from_node, "->", to_node))
            edges_included += 1
            if is_tie:
                tie_breaks_applied += 1

            # Update ancestors: to_node gains from_node and all its ancestors
            new_ancestors = ancestors[from_node] | {from_node}
            ancestors[to_node] = ancestors[to_node] | new_ancestors

            # Propagate to all descendants of to_node
            to_visit = [to_node]
            visited = set()
            while to_visit:
                current = to_visit.pop()
                if current in visited:
                    continue
                visited.add(current)
                # Find children of current
                for edge in dag_edges:
                    if edge[0] == current:
                        child = edge[2]
                        ancestors[child] = ancestors[child] | new_ancestors
                        to_visit.append(child)

        # Create DAG
        dag = DAG(self.nodes, dag_edges)

        return GreedyDAGResult(
            dag=dag,
            edges_included=edges_included,
            edges_skipped_cycle=edges_skipped_cycle,
            edges_skipped_threshold=edges_skipped_threshold,
            tie_breaks_applied=tie_breaks_applied,
        )

    def compress(self) -> bytes:
        """Compress PDG to compact binary representation.

        Format:
        - 2 bytes: number of nodes (uint16, big-endian)
        - For each node: 2 bytes name length + UTF-8 encoded name
        - 2 bytes: number of edge pairs with probabilities (uint16)
        - For each edge pair:
            - 2 bytes: source node index (uint16)
            - 2 bytes: target node index (uint16)
            - 3 bytes: p_forward (4 s.f. mantissa + exponent)
            - 3 bytes: p_backward (4 s.f. mantissa + exponent)
            - 3 bytes: p_undirected (4 s.f. mantissa + exponent)

        Probabilities are encoded with 4 significant figures using a
        mantissa (0-9999) and exponent format: value = mantissa × 10^exp.
        The p_none value is derived as 1.0 - (forward + backward + undirected).

        Returns:
            Compact binary representation of the PDG.

        Raises:
            ValueError: If graph has more than 65535 nodes or edge pairs.
        """
        if len(self.nodes) > 65535:
            raise ValueError("PDG.compress() graph has too many nodes")
        if len(self.edges) > 65535:
            raise ValueError("PDG.compress() graph has too many edge pairs")

        # Build node index for edge compression
        node_index = {node: i for i, node in enumerate(self.nodes)}

        # Compress number of nodes
        data = len(self.nodes).to_bytes(2, "big")

        # Compress each node name
        for node in self.nodes:
            name_bytes = node.encode("utf-8")
            if len(name_bytes) > 65535:
                raise ValueError("PDG.compress() node name too long")
            data += len(name_bytes).to_bytes(2, "big")
            data += name_bytes

        # Compress number of edge pairs
        data += len(self.edges).to_bytes(2, "big")

        # Compress each edge pair (source idx, target idx, 3 probabilities)
        for (source, target), probs in self.edges.items():
            data += node_index[source].to_bytes(2, "big")
            data += node_index[target].to_bytes(2, "big")
            data += _encode_probability(probs.forward)
            data += _encode_probability(probs.backward)
            data += _encode_probability(probs.undirected)

        return data

    @classmethod
    def decompress(cls, data: bytes) -> "PDG":
        """Decompress PDG from compact binary representation.

        Args:
            data: Binary data from PDG.compress().

        Returns:
            Reconstructed PDG instance.

        Raises:
            TypeError: If data is not bytes.
            ValueError: If data is invalid or corrupted.
        """
        if not isinstance(data, bytes):
            raise TypeError("PDG.decompress() data must be bytes")

        if len(data) < 2:
            raise ValueError("PDG.decompress() data too short")

        pos = 0

        # Decompress number of nodes
        num_nodes = int.from_bytes(data[pos : pos + 2], "big")
        pos += 2

        # Decompress node names
        nodes = []
        for _ in range(num_nodes):
            if pos + 2 > len(data):
                raise ValueError("PDG.decompress() data truncated")
            name_len = int.from_bytes(data[pos : pos + 2], "big")
            pos += 2
            if pos + name_len > len(data):
                raise ValueError("PDG.decompress() data truncated")
            node = data[pos : pos + name_len].decode("utf-8")
            pos += name_len
            nodes.append(node)

        # Decompress number of edge pairs
        if pos + 2 > len(data):
            raise ValueError("PDG.decompress() data truncated")
        num_edges = int.from_bytes(data[pos : pos + 2], "big")
        pos += 2

        # Decompress edge pairs
        edges: Dict[Tuple[str, str], EdgeProbabilities] = {}
        for _ in range(num_edges):
            if pos + 13 > len(data):  # 2+2+3+3+3 = 13 bytes per edge
                raise ValueError("PDG.decompress() data truncated")

            source_idx = int.from_bytes(data[pos : pos + 2], "big")
            pos += 2
            target_idx = int.from_bytes(data[pos : pos + 2], "big")
            pos += 2

            if source_idx >= len(nodes) or target_idx >= len(nodes):
                raise ValueError("PDG.decompress() invalid node index")

            p_forward = _decode_probability(data[pos : pos + 3])
            pos += 3
            p_backward = _decode_probability(data[pos : pos + 3])
            pos += 3
            p_undirected = _decode_probability(data[pos : pos + 3])
            pos += 3

            # Derive p_none from the constraint that probabilities sum to 1.0
            p_none = 1.0 - (p_forward + p_backward + p_undirected)

            # Handle floating point precision issues
            if p_none < 0:
                if p_none > -1e-9:  # pragma: no cover
                    p_none = 0.0
                else:
                    raise ValueError(
                        "PDG.decompress() probabilities sum to more than 1.0"
                    )

            source = nodes[source_idx]
            target = nodes[target_idx]
            edges[(source, target)] = EdgeProbabilities(
                forward=p_forward,
                backward=p_backward,
                undirected=p_undirected,
                none=p_none,
            )

        return cls(nodes, edges)


def _encode_probability(value: float) -> bytes:
    """Encode probability to 3 bytes with 4 significant figures.

    Format: 2 bytes mantissa (uint16) + 1 byte exponent (int8).
    Value = mantissa × 10^exponent.

    Args:
        value: Probability value in range [0.0, 1.0].

    Returns:
        3-byte encoding.

    Example:
        >>> _encode_probability(0.9876)  # mantissa=9876, exp=-4
        >>> _encode_probability(0.001234)  # mantissa=1234, exp=-6
        >>> _encode_probability(0.0)  # mantissa=0, exp=0
    """
    if value == 0.0:
        return b"\x00\x00\x00"

    if value < 0 or value > 1.0:
        raise ValueError(f"Probability must be in [0, 1], got {value}")

    # Special case for exactly 1.0
    if value == 1.0:
        # 1.0 = 1000 × 10^-3
        mantissa = 1000
        exponent = -3
        return mantissa.to_bytes(2, "big") + exponent.to_bytes(
            1, "big", signed=True
        )

    # Find exponent: we want mantissa in range [1000, 9999] for 4 s.f.
    import math

    log_val = math.log10(value)
    # Exponent to get mantissa in [1000, 9999]
    exponent = int(math.floor(log_val)) - 3

    # Calculate mantissa
    mantissa = round(value / (10**exponent))

    # Ensure mantissa is in valid range
    if mantissa >= 10000:
        mantissa = mantissa // 10
        exponent += 1
    elif mantissa < 1000 and mantissa > 0:  # pragma: no cover
        mantissa = mantissa * 10
        exponent -= 1

    # Clamp mantissa to uint16 range
    mantissa = max(0, min(9999, mantissa))

    # Clamp exponent to int8 range
    exponent = max(-128, min(127, exponent))

    return bytes(
        mantissa.to_bytes(2, "big") + exponent.to_bytes(1, "big", signed=True)
    )


def _decode_probability(data: bytes) -> float:
    """Decode probability from 3-byte format.

    Args:
        data: 3 bytes (mantissa uint16 + exponent int8).

    Returns:
        Decoded probability value.
    """
    if len(data) != 3:
        raise ValueError("Probability encoding must be 3 bytes")

    mantissa = int.from_bytes(data[0:2], "big")
    exponent = int.from_bytes(data[2:3], "big", signed=True)

    if mantissa == 0:
        return 0.0

    return float(mantissa * (10**exponent))
