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

from .pdg_codec import (  # noqa: F401
    _decode_probability,
    _encode_probability,
    decode_pdg,
    encode_pdg,
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
        self.nodes = _validate_pdg_nodes(nodes)
        self.edges = _validate_pdg_edges(self.nodes, edges)

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
        _check_get_probability_nodes(self.nodes, node_a, node_b)

        # Canonicalise order
        probs = self.edges.get(_canonical_pair(node_a, node_b))
        if probs is None:
            return EdgeProbabilities()  # Default: no edge
        if node_a < node_b:
            return probs
        # Swap forward/backward for reversed order
        return _reversed_probabilities(probs)

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

        candidates, edges_skipped_threshold = _candidate_edges(
            self.edges, threshold
        )
        dag_edges, included, skipped_cycle, tie_breaks = _build_greedy_dag(
            self.nodes, candidates
        )

        # Create DAG
        dag = DAG(self.nodes, dag_edges)

        return GreedyDAGResult(
            dag=dag,
            edges_included=included,
            edges_skipped_cycle=skipped_cycle,
            edges_skipped_threshold=edges_skipped_threshold,
            tie_breaks_applied=tie_breaks,
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
        probabilities = {
            pair: (p.forward, p.backward, p.undirected, p.none)
            for pair, p in self.edges.items()
        }
        return encode_pdg(self.nodes, probabilities)

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
        nodes, probabilities = decode_pdg(data)
        edges = {
            pair: EdgeProbabilities(
                forward=probs[0],
                backward=probs[1],
                undirected=probs[2],
                none=probs[3],
            )
            for pair, probs in probabilities.items()
        }
        return cls(nodes, edges)


def _validate_pdg_nodes(nodes: List[str]) -> List[str]:
    """Return the node names of a PDG in alphabetical order.

    Args:
        nodes: Node names supplied to the PDG constructor.

    Returns:
        Sorted unique node names.

    Raises:
        TypeError: If nodes is not a list or holds a non-string name.
        ValueError: If a name is empty or names are duplicated.
    """
    if not isinstance(nodes, list):
        raise TypeError("PDG nodes must be a list")
    for node in nodes:
        if not isinstance(node, str):
            raise TypeError("PDG node names must be strings")
        if not node:
            raise ValueError("PDG node names cannot be empty")

    # Store nodes in alphabetical order
    ordered = sorted(set(nodes))

    if len(ordered) != len(nodes):
        raise ValueError("PDG has duplicate node names")
    return ordered


def _validate_pdg_edges(
    nodes: List[str],
    edges: Optional[Dict[Tuple[str, str], EdgeProbabilities]],
) -> Dict[Tuple[str, str], EdgeProbabilities]:
    """Return the validated edge probabilities of a PDG.

    Args:
        nodes: Validated node names of the graph.
        edges: Edge probabilities supplied to the PDG constructor.

    Returns:
        Validated edge probabilities keyed by node pair.

    Raises:
        TypeError: If edges is not a dictionary or a value is not
            EdgeProbabilities.
        ValueError: If a pair names an unknown node, is a self-loop or is
            not in canonical order.
    """
    validated: Dict[Tuple[str, str], EdgeProbabilities] = {}
    if edges is None:
        return validated
    if not isinstance(edges, dict):
        raise TypeError("PDG edges must be a dictionary")

    node_set = set(nodes)
    for (source, target), probs in edges.items():
        _validate_pdg_edge_pair(node_set, source, target, probs)
        validated[(source, target)] = probs
    return validated


def _validate_pdg_edge_pair(
    node_set: set, source: str, target: str, probs: EdgeProbabilities
) -> None:
    """Validate one node pair of a PDG's edge probabilities.

    Args:
        node_set: Nodes known to the graph.
        source: Source node name.
        target: Target node name.
        probs: Value supplied for the pair.

    Raises:
        TypeError: If probs is not EdgeProbabilities.
        ValueError: If the pair names an unknown node, is a self-loop or is
            not in canonical order.
    """
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
            f"Edge ({source}, {target}) value must be " "EdgeProbabilities"
        )


def _check_get_probability_nodes(
    nodes: List[str], node_a: str, node_b: str
) -> None:
    """Validate the node pair requested from a PDG.

    Args:
        nodes: Nodes known to the graph.
        node_a: First node name.
        node_b: Second node name.

    Raises:
        ValueError: If a node is unknown or the pair is a self-loop.
    """
    if node_a not in nodes:
        raise ValueError(f"Unknown node: {node_a}")
    if node_b not in nodes:
        raise ValueError(f"Unknown node: {node_b}")
    if node_a == node_b:
        raise ValueError("Cannot get probabilities for self-loop")


def _canonical_pair(node_a: str, node_b: str) -> Tuple[str, str]:
    """Return a node pair in alphabetical (canonical) order.

    Args:
        node_a: First node name.
        node_b: Second node name.

    Returns:
        The pair with the alphabetically smaller name first.
    """
    return (node_a, node_b) if node_a < node_b else (node_b, node_a)


def _reversed_probabilities(
    probs: EdgeProbabilities,
) -> EdgeProbabilities:
    """Return edge probabilities with forward and backward swapped.

    Args:
        probs: Probabilities stored in canonical order.

    Returns:
        Probabilities relative to the reversed node order.
    """
    return EdgeProbabilities(
        forward=probs.backward,
        backward=probs.forward,
        undirected=probs.undirected,
        none=probs.none,
    )


# Candidate edge: (probability, source, target, direction, is tie break)
Candidate = Tuple[float, str, str, str, bool]


def _candidate_for(
    source: str, target: str, probs: EdgeProbabilities
) -> Candidate:
    """Return the ranked candidate edge for one node pair.

    The undirected probability is split equally between the two possible
    directions and ties are broken in favour of the canonical forward
    direction.

    Args:
        source: Canonical source node.
        target: Canonical target node.
        probs: Edge probabilities for the pair.

    Returns:
        Candidate edge tuple.
    """
    eff_forward = probs.forward + probs.undirected / 2
    eff_backward = probs.backward + probs.undirected / 2
    if eff_backward > eff_forward:
        return (eff_backward, source, target, "backward", False)
    is_tie = eff_forward == eff_backward
    return (eff_forward, source, target, "forward", is_tie)


def _candidate_edges(
    edges: Dict[Tuple[str, str], EdgeProbabilities], threshold: float
) -> Tuple[List[Candidate], int]:
    """Return ranked candidate edges and those below the threshold.

    Args:
        edges: Edge probabilities of the graph.
        threshold: Minimum p_exist for an edge to be considered.

    Returns:
        Tuple of (candidates ordered by descending probability, number of
        edges skipped because they fall below the threshold).
    """
    candidates = []
    skipped = 0
    for (source, target), probs in edges.items():
        if probs.p_exist < threshold:
            skipped += 1
            continue
        candidates.append(_candidate_for(source, target, probs))

    # Sort by probability descending (stable sort preserves order for ties)
    candidates.sort(key=lambda x: -x[0])
    return candidates, skipped


def _edge_ends(source: str, target: str, direction: str) -> Tuple[str, str]:
    """Return the (from, to) nodes for a candidate edge direction.

    Args:
        source: Canonical source node.
        target: Canonical target node.
        direction: "forward" or "backward".

    Returns:
        Tuple of (from node, to node).
    """
    if direction == "forward":
        return source, target
    return target, source


def _pass_ancestors_to_children(
    ancestors: Dict[str, set],
    dag_edges: List[Tuple[str, str, str]],
    current: str,
    new_ancestors: set,
    to_visit: List[str],
) -> None:
    """Add new ancestors to a node and queue its children for updating.

    Args:
        ancestors: Ancestors of each node, updated in place.
        dag_edges: Edge triples added so far.
        current: Node to update.
        new_ancestors: Ancestors to add to the node and its descendants.
        to_visit: Queue of nodes still to update.
    """
    ancestors[current] = ancestors[current] | new_ancestors
    for edge in dag_edges:
        if edge[0] == current:
            child = edge[2]
            ancestors[child] = ancestors[child] | new_ancestors
            to_visit.append(child)


def _propagate_ancestors(
    ancestors: Dict[str, set],
    dag_edges: List[Tuple[str, str, str]],
    from_node: str,
    to_node: str,
) -> None:
    """Add from_node and its ancestors to to_node and its descendants.

    Args:
        ancestors: Ancestors of each node, updated in place.
        dag_edges: Edge triples added so far.
        from_node: Node the new edge starts from.
        to_node: Node the new edge points to.
    """
    new_ancestors = ancestors[from_node] | {from_node}
    to_visit = [to_node]
    visited: set = set()
    while to_visit:
        current = to_visit.pop()
        if current in visited:
            continue
        visited.add(current)
        _pass_ancestors_to_children(
            ancestors, dag_edges, current, new_ancestors, to_visit
        )


def _add_candidate_edge(
    dag_edges: List[Tuple[str, str, str]],
    ancestors: Dict[str, set],
    source: str,
    target: str,
    direction: str,
) -> Tuple[int, int]:
    """Add one candidate edge when it does not create a cycle.

    A cycle would arise when the target is already an ancestor of the
    source, i.e. there is already a path from the target to the source.

    Args:
        dag_edges: Edge triples added so far, extended in place.
        ancestors: Ancestors of each node, updated in place.
        source: Canonical source node of the candidate.
        target: Canonical target node of the candidate.
        direction: "forward" or "backward".

    Returns:
        Tuple of (1 if the edge was added else 0, 1 if it was skipped to
        avoid a cycle else 0).
    """
    from_node, to_node = _edge_ends(source, target, direction)
    if to_node in ancestors[from_node] or from_node == to_node:
        return 0, 1
    dag_edges.append((from_node, "->", to_node))
    _propagate_ancestors(ancestors, dag_edges, from_node, to_node)
    return 1, 0


def _build_greedy_dag(
    nodes: List[str], candidates: List[Candidate]
) -> Tuple[List[Tuple[str, str, str]], int, int, int]:
    """Return the DAG built greedily from ranked candidate edges.

    Args:
        nodes: Nodes of the graph.
        candidates: Candidate edges ordered by descending probability.

    Returns:
        Tuple of (dag edge triples, edges included, edges skipped to avoid
        a cycle, tie breaks applied).
    """
    dag_edges: List[Tuple[str, str, str]] = []
    ancestors: Dict[str, set] = {node: set() for node in nodes}
    included = 0
    skipped_cycle = 0
    tie_breaks = 0

    for _, source, target, direction, is_tie in candidates:
        added, skipped = _add_candidate_edge(
            dag_edges, ancestors, source, target, direction
        )
        included += added
        skipped_cycle += skipped
        tie_breaks += 1 if is_tie and added else 0

    return dag_edges, included, skipped_cycle, tie_breaks
