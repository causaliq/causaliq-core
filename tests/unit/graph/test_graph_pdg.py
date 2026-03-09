"""Unit tests for PDG (Probabilistic Dependency Graph) classes."""

import pytest

from causaliq_core.graph import PDG, EdgeProbabilities

# --- EdgeProbabilities tests ---


# Test EdgeProbabilities default construction gives no edge.
def test_edge_probabilities_default() -> None:
    """Default EdgeProbabilities represents no edge."""
    probs = EdgeProbabilities()
    assert probs.forward == 0.0
    assert probs.backward == 0.0
    assert probs.undirected == 0.0
    assert probs.none == 1.0


# Test EdgeProbabilities with valid probabilities.
def test_edge_probabilities_valid() -> None:
    """Valid probabilities summing to 1.0."""
    probs = EdgeProbabilities(
        forward=0.6, backward=0.2, undirected=0.1, none=0.1
    )
    assert probs.forward == 0.6
    assert probs.backward == 0.2
    assert probs.undirected == 0.1
    assert probs.none == 0.1


# Test EdgeProbabilities validation rejects non-summing probabilities.
def test_edge_probabilities_invalid_sum() -> None:
    """Probabilities must sum to 1.0."""
    with pytest.raises(ValueError, match="sum to 1.0"):
        EdgeProbabilities(forward=0.5, backward=0.5, undirected=0.5, none=0.0)


# Test EdgeProbabilities validation rejects negative forward probability.
def test_edge_probabilities_negative_forward() -> None:
    """Probabilities must be non-negative (forward)."""
    with pytest.raises(ValueError, match="non-negative"):
        EdgeProbabilities(forward=-0.1, backward=0.1, undirected=0.0, none=1.0)


# Test EdgeProbabilities validation rejects negative undirected probability.
def test_edge_probabilities_negative_undirected() -> None:
    """Probabilities must be non-negative (undirected)."""
    with pytest.raises(ValueError, match="non-negative"):
        EdgeProbabilities(forward=0.1, backward=0.0, undirected=-0.1, none=1.0)


# Test EdgeProbabilities p_exist property.
def test_edge_probabilities_p_exist() -> None:
    """p_exist returns sum of edge probabilities."""
    probs = EdgeProbabilities(
        forward=0.4, backward=0.3, undirected=0.2, none=0.1
    )
    assert abs(probs.p_exist - 0.9) < 1e-9


# Test EdgeProbabilities p_directed property.
def test_edge_probabilities_p_directed() -> None:
    """p_directed returns sum of forward and backward."""
    probs = EdgeProbabilities(
        forward=0.4, backward=0.3, undirected=0.2, none=0.1
    )
    assert abs(probs.p_directed - 0.7) < 1e-9


# Test EdgeProbabilities most_likely_state method.
def test_edge_probabilities_most_likely_state() -> None:
    """most_likely_state returns state with highest probability."""
    probs = EdgeProbabilities(
        forward=0.6, backward=0.2, undirected=0.1, none=0.1
    )
    assert probs.most_likely_state() == "forward"

    probs = EdgeProbabilities(
        forward=0.1, backward=0.1, undirected=0.1, none=0.7
    )
    assert probs.most_likely_state() == "none"


# Test EdgeProbabilities equality.
def test_edge_probabilities_equality() -> None:
    """EdgeProbabilities equality comparison."""
    p1 = EdgeProbabilities(forward=0.5, backward=0.3, none=0.2)
    p2 = EdgeProbabilities(forward=0.5, backward=0.3, none=0.2)
    p3 = EdgeProbabilities(forward=0.4, backward=0.4, none=0.2)
    assert p1 == p2
    assert p1 != p3


# --- PDG tests ---


# Test PDG construction with nodes only.
def test_pdg_nodes_only() -> None:
    """PDG with nodes but no edges."""
    pdg = PDG(["A", "B", "C"])
    assert pdg.nodes == ["A", "B", "C"]
    assert len(pdg.edges) == 0


# Test PDG construction with edges.
def test_pdg_with_edges() -> None:
    """PDG with nodes and edges."""
    edges = {
        ("A", "B"): EdgeProbabilities(forward=0.8, none=0.2),
        ("A", "C"): EdgeProbabilities(backward=0.6, none=0.4),
    }
    pdg = PDG(["A", "B", "C"], edges)
    assert pdg.nodes == ["A", "B", "C"]
    assert len(pdg.edges) == 2


# Test PDG node sorting.
def test_pdg_nodes_sorted() -> None:
    """Nodes are stored in alphabetical order."""
    pdg = PDG(["C", "A", "B"])
    assert pdg.nodes == ["A", "B", "C"]


# Test PDG rejects non-list nodes.
def test_pdg_invalid_nodes_type() -> None:
    """Nodes must be a list."""
    with pytest.raises(TypeError, match="must be a list"):
        PDG("ABC")  # type: ignore[arg-type]


# Test PDG rejects non-string node names.
def test_pdg_invalid_node_name_type() -> None:
    """Node names must be strings."""
    with pytest.raises(TypeError, match="must be strings"):
        PDG([1, 2, 3])  # type: ignore[list-item]


# Test PDG rejects empty node names.
def test_pdg_empty_node_name() -> None:
    """Node names cannot be empty."""
    with pytest.raises(ValueError, match="cannot be empty"):
        PDG(["A", "", "C"])


# Test PDG rejects duplicate node names.
def test_pdg_duplicate_nodes() -> None:
    """Node names must be unique."""
    with pytest.raises(ValueError, match="duplicate"):
        PDG(["A", "B", "A"])


# Test PDG rejects non-dict edges parameter.
def test_pdg_invalid_edges_type() -> None:
    """Edges must be a dictionary."""
    with pytest.raises(TypeError, match="must be a dictionary"):
        PDG(["A", "B"], [("A", "B")])  # type: ignore[arg-type]


# Test PDG rejects edge value that is not EdgeProbabilities.
def test_pdg_invalid_edge_value_type() -> None:
    """Edge values must be EdgeProbabilities."""
    edges = {("A", "B"): 0.5}  # type: ignore[dict-item]
    with pytest.raises(TypeError, match="must be EdgeProbabilities"):
        PDG(["A", "B"], edges)


# Test PDG rejects edge with unknown source node.
def test_pdg_unknown_source_node() -> None:
    """Edge source must be a known node."""
    edges = {("X", "B"): EdgeProbabilities(forward=0.5, none=0.5)}
    with pytest.raises(ValueError, match="Unknown source"):
        PDG(["A", "B"], edges)


# Test PDG rejects edge with unknown target node.
def test_pdg_unknown_target_node() -> None:
    """Edge target must be a known node."""
    edges = {("A", "X"): EdgeProbabilities(forward=0.5, none=0.5)}
    with pytest.raises(ValueError, match="Unknown target"):
        PDG(["A", "B"], edges)


# Test PDG rejects self-loop edge.
def test_pdg_self_loop() -> None:
    """Self-loops not allowed."""
    edges = {("A", "A"): EdgeProbabilities(forward=0.5, none=0.5)}
    with pytest.raises(ValueError, match="Self-loop"):
        PDG(["A", "B"], edges)


# Test PDG rejects non-canonical edge order.
def test_pdg_non_canonical_order() -> None:
    """Edge keys must be in canonical order (source < target)."""
    edges = {("B", "A"): EdgeProbabilities(forward=0.5, none=0.5)}
    with pytest.raises(ValueError, match="canonical order"):
        PDG(["A", "B"], edges)


# Test PDG get_probabilities returns stored values.
def test_pdg_get_probabilities() -> None:
    """get_probabilities returns correct values."""
    probs = EdgeProbabilities(forward=0.7, backward=0.2, none=0.1)
    pdg = PDG(["A", "B"], {("A", "B"): probs})

    result = pdg.get_probabilities("A", "B")
    assert result.forward == 0.7
    assert result.backward == 0.2


# Test PDG get_probabilities handles reversed node order.
def test_pdg_get_probabilities_reversed() -> None:
    """get_probabilities swaps forward/backward for reversed nodes."""
    probs = EdgeProbabilities(forward=0.7, backward=0.2, none=0.1)
    pdg = PDG(["A", "B"], {("A", "B"): probs})

    result = pdg.get_probabilities("B", "A")
    assert result.forward == 0.2  # Was backward
    assert result.backward == 0.7  # Was forward


# Test PDG get_probabilities returns default for missing edge.
def test_pdg_get_probabilities_missing() -> None:
    """get_probabilities returns default for missing edge."""
    pdg = PDG(["A", "B", "C"])

    result = pdg.get_probabilities("A", "B")
    assert result.none == 1.0
    assert result.p_exist == 0.0


# Test PDG get_probabilities returns default for missing edge in reverse.
def test_pdg_get_probabilities_missing_reversed() -> None:
    """get_probabilities returns default for missing edge."""
    pdg = PDG(["A", "B", "C"])

    # Request in non-canonical order (B, A) when edge doesn't exist
    result = pdg.get_probabilities("B", "A")
    assert result.none == 1.0
    assert result.p_exist == 0.0


# Test PDG get_probabilities rejects unknown node_a (first node).
def test_pdg_get_probabilities_unknown_node_a() -> None:
    """get_probabilities raises for unknown first node."""
    pdg = PDG(["A", "B"])
    with pytest.raises(ValueError, match="Unknown node"):
        pdg.get_probabilities("X", "A")


# Test PDG get_probabilities rejects unknown node_b (second node).
def test_pdg_get_probabilities_unknown_node_b() -> None:
    """get_probabilities raises for unknown second node."""
    pdg = PDG(["A", "B"])
    with pytest.raises(ValueError, match="Unknown node"):
        pdg.get_probabilities("A", "X")


# Test PDG get_probabilities rejects self-loop.
def test_pdg_get_probabilities_self_loop() -> None:
    """get_probabilities raises for self-loop."""
    pdg = PDG(["A", "B"])
    with pytest.raises(ValueError, match="self-loop"):
        pdg.get_probabilities("A", "A")


# Test PDG set_probabilities stores values.
def test_pdg_set_probabilities() -> None:
    """set_probabilities stores values correctly."""
    pdg = PDG(["A", "B"])
    probs = EdgeProbabilities(forward=0.8, none=0.2)
    pdg.set_probabilities("A", "B", probs)

    result = pdg.get_probabilities("A", "B")
    assert result.forward == 0.8


# Test PDG set_probabilities handles reversed node order.
def test_pdg_set_probabilities_reversed() -> None:
    """set_probabilities handles reversed node order."""
    pdg = PDG(["A", "B"])
    probs = EdgeProbabilities(forward=0.8, backward=0.1, none=0.1)
    pdg.set_probabilities("B", "A", probs)

    # Check canonical storage
    result = pdg.get_probabilities("A", "B")
    assert result.forward == 0.1  # Was backward in input
    assert result.backward == 0.8  # Was forward in input


# Test PDG set_probabilities validates node_a unknown.
def test_pdg_set_probabilities_unknown_node_a() -> None:
    """set_probabilities raises for unknown first node."""
    pdg = PDG(["A", "B"])
    probs = EdgeProbabilities(forward=0.5, none=0.5)
    with pytest.raises(ValueError, match="Unknown node"):
        pdg.set_probabilities("X", "A", probs)


# Test PDG set_probabilities validates node_b unknown.
def test_pdg_set_probabilities_unknown_node_b() -> None:
    """set_probabilities raises for unknown second node."""
    pdg = PDG(["A", "B"])
    probs = EdgeProbabilities(forward=0.5, none=0.5)
    with pytest.raises(ValueError, match="Unknown node"):
        pdg.set_probabilities("A", "X", probs)


# Test PDG set_probabilities rejects self-loop.
def test_pdg_set_probabilities_self_loop() -> None:
    """set_probabilities raises for self-loop."""
    pdg = PDG(["A", "B"])
    probs = EdgeProbabilities(forward=0.5, none=0.5)
    with pytest.raises(ValueError, match="self-loop"):
        pdg.set_probabilities("A", "A", probs)


# Test PDG set_probabilities validates type.
def test_pdg_set_probabilities_invalid_type() -> None:
    """set_probabilities raises for non-EdgeProbabilities."""
    pdg = PDG(["A", "B"])
    with pytest.raises(TypeError, match="EdgeProbabilities"):
        pdg.set_probabilities("A", "B", 0.5)  # type: ignore[arg-type]


# Test PDG node_pairs iteration.
def test_pdg_node_pairs() -> None:
    """node_pairs iterates over all pairs in canonical order."""
    pdg = PDG(["A", "B", "C"])
    pairs = list(pdg.node_pairs())
    assert pairs == [("A", "B"), ("A", "C"), ("B", "C")]


# Test PDG existing_edges iteration.
def test_pdg_existing_edges() -> None:
    """existing_edges yields only edges with p_exist > 0."""
    pdg = PDG(
        ["A", "B", "C"],
        {
            ("A", "B"): EdgeProbabilities(forward=0.5, none=0.5),
            ("A", "C"): EdgeProbabilities(none=1.0),  # No edge
            ("B", "C"): EdgeProbabilities(undirected=1.0, none=0.0),
        },
    )
    edges = list(pdg.existing_edges())
    assert len(edges) == 2
    assert edges[0][0:2] == ("A", "B")
    assert edges[1][0:2] == ("B", "C")


# Test PDG __len__ returns number of stored edges.
def test_pdg_len() -> None:
    """__len__ returns number of stored edge probabilities."""
    pdg = PDG(
        ["A", "B", "C"],
        {("A", "B"): EdgeProbabilities(forward=0.5, none=0.5)},
    )
    assert len(pdg) == 1


# Test PDG equality.
def test_pdg_equality() -> None:
    """PDG equality comparison."""
    edges = {("A", "B"): EdgeProbabilities(forward=0.5, none=0.5)}
    pdg1 = PDG(["A", "B"], edges)
    pdg2 = PDG(["A", "B"], edges)
    pdg3 = PDG(["A", "B", "C"], edges)

    assert pdg1 == pdg2
    assert pdg1 != pdg3
    assert pdg1 != "not a PDG"


# Test PDG __str__ representation.
def test_pdg_str() -> None:
    """__str__ returns human-readable description."""
    pdg = PDG(
        ["A", "B", "C"],
        {("A", "B"): EdgeProbabilities(forward=0.5, none=0.5)},
    )
    s = str(pdg)
    assert "3 nodes" in s
    assert "1 edge" in s


# Test PDG __repr__ representation.
def test_pdg_repr() -> None:
    """__repr__ returns detailed representation."""
    pdg = PDG(["A", "B"])
    r = repr(pdg)
    assert "PDG" in r
    assert "nodes" in r


# --- to_dag_greedy tests ---


# Test to_dag_greedy with simple directed edges.
def test_to_dag_greedy_simple_directed() -> None:
    """Greedy DAG extraction with clear directed edges."""
    pdg = PDG(
        ["A", "B", "C"],
        {
            ("A", "B"): EdgeProbabilities(forward=0.8, none=0.2),
            ("A", "C"): EdgeProbabilities(forward=0.6, none=0.4),
        },
    )
    result = pdg.to_dag_greedy()

    assert result.edges_included == 2
    assert result.edges_skipped_cycle == 0
    assert result.edges_skipped_threshold == 0
    assert result.tie_breaks_applied == 0

    # Check DAG has the expected edges
    dag = result.dag
    assert ("A", "B") in dag.edges
    assert ("A", "C") in dag.edges


# Test to_dag_greedy with backward direction.
def test_to_dag_greedy_backward_edge() -> None:
    """Greedy DAG extraction chooses backward when probability higher."""
    pdg = PDG(
        ["A", "B"],
        {
            ("A", "B"): EdgeProbabilities(backward=0.9, none=0.1),
        },
    )
    result = pdg.to_dag_greedy()

    assert result.edges_included == 1
    dag = result.dag
    # backward means B -> A (since A < B alphabetically)
    assert ("B", "A") in dag.edges


# Test to_dag_greedy avoids cycles.
def test_to_dag_greedy_avoids_cycles() -> None:
    """Greedy DAG extraction skips edges that would create cycles."""
    pdg = PDG(
        ["A", "B", "C"],
        {
            # High probability: A -> B
            ("A", "B"): EdgeProbabilities(forward=0.9, none=0.1),
            # Medium probability: B -> C
            ("B", "C"): EdgeProbabilities(forward=0.8, none=0.2),
            # Lower probability: C -> A (would create cycle)
            ("A", "C"): EdgeProbabilities(backward=0.7, none=0.3),
        },
    )
    result = pdg.to_dag_greedy()

    assert result.edges_included == 2
    assert result.edges_skipped_cycle == 1  # C -> A skipped

    dag = result.dag
    assert ("A", "B") in dag.edges
    assert ("B", "C") in dag.edges
    # C -> A not present (would create cycle)


# Test to_dag_greedy with undirected probability.
def test_to_dag_greedy_undirected_probability() -> None:
    """Undirected probability split equally between directions."""
    pdg = PDG(
        ["A", "B"],
        {
            # p_undirected = 0.8, p_forward = 0.1, p_backward = 0.05
            # effective_forward = 0.1 + 0.4 = 0.5
            # effective_backward = 0.05 + 0.4 = 0.45
            # Should choose forward (A -> B)
            ("A", "B"): EdgeProbabilities(
                forward=0.1, backward=0.05, undirected=0.8, none=0.05
            ),
        },
    )
    result = pdg.to_dag_greedy()

    assert result.edges_included == 1
    dag = result.dag
    assert ("A", "B") in dag.edges


# Test to_dag_greedy tie-break uses alphabetical order.
def test_to_dag_greedy_tie_break_alphabetical() -> None:
    """Equal probabilities use alphabetical tie-break."""
    pdg = PDG(
        ["A", "B"],
        {
            # Equal forward and backward after splitting undirected
            # eff_forward = 0.0 + 0.5 = 0.5, eff_backward = 0.0 + 0.5 = 0.5
            ("A", "B"): EdgeProbabilities(undirected=1.0, none=0.0),
        },
    )
    result = pdg.to_dag_greedy()

    assert result.edges_included == 1
    assert result.tie_breaks_applied == 1

    dag = result.dag
    # Alphabetical: A -> B (forward)
    assert ("A", "B") in dag.edges


# Test to_dag_greedy with threshold.
def test_to_dag_greedy_threshold() -> None:
    """Edges below threshold are skipped."""
    pdg = PDG(
        ["A", "B", "C"],
        {
            ("A", "B"): EdgeProbabilities(
                forward=0.8, none=0.2
            ),  # p_exist=0.8
            ("A", "C"): EdgeProbabilities(
                forward=0.3, none=0.7
            ),  # p_exist=0.3
        },
    )
    result = pdg.to_dag_greedy(threshold=0.5)

    assert result.edges_included == 1
    assert result.edges_skipped_threshold == 1

    dag = result.dag
    assert ("A", "B") in dag.edges
    assert ("A", "C") not in dag.edges


# Test to_dag_greedy with empty PDG.
def test_to_dag_greedy_empty() -> None:
    """Empty PDG produces empty DAG."""
    pdg = PDG(["A", "B", "C"])
    result = pdg.to_dag_greedy()

    assert result.edges_included == 0
    assert result.edges_skipped_cycle == 0
    assert result.edges_skipped_threshold == 0
    assert result.tie_breaks_applied == 0

    dag = result.dag
    assert len(dag.edges) == 0


# Test to_dag_greedy result is valid DAG.
def test_to_dag_greedy_result_is_dag() -> None:
    """Result is a valid DAG (no cycles)."""
    from causaliq_core.graph import DAG

    pdg = PDG(
        ["A", "B", "C", "D"],
        {
            ("A", "B"): EdgeProbabilities(forward=0.9, none=0.1),
            ("A", "C"): EdgeProbabilities(forward=0.85, none=0.15),
            ("B", "C"): EdgeProbabilities(forward=0.8, none=0.2),
            ("B", "D"): EdgeProbabilities(forward=0.7, none=0.3),
            ("C", "D"): EdgeProbabilities(forward=0.6, none=0.4),
        },
    )
    result = pdg.to_dag_greedy()

    assert isinstance(result.dag, DAG)
    # DAG construction would fail if there were cycles


# Test to_dag_greedy with complex cycle avoidance.
def test_to_dag_greedy_complex_cycle_avoidance() -> None:
    """Complex graph where multiple edges would create cycles."""
    pdg = PDG(
        ["A", "B", "C", "D"],
        {
            # Create chain A -> B -> C -> D
            ("A", "B"): EdgeProbabilities(forward=0.95, none=0.05),
            ("B", "C"): EdgeProbabilities(forward=0.90, none=0.10),
            ("C", "D"): EdgeProbabilities(forward=0.85, none=0.15),
            # These would create cycles:
            ("A", "D"): EdgeProbabilities(backward=0.80, none=0.20),  # D -> A
            ("A", "C"): EdgeProbabilities(backward=0.75, none=0.25),  # C -> A
            ("B", "D"): EdgeProbabilities(backward=0.70, none=0.30),  # D -> B
        },
    )
    result = pdg.to_dag_greedy()

    # First 3 edges form chain, last 3 would all create cycles
    assert result.edges_included == 3
    assert result.edges_skipped_cycle == 3

    dag = result.dag
    assert ("A", "B") in dag.edges
    assert ("B", "C") in dag.edges
    assert ("C", "D") in dag.edges


# Test to_dag_greedy ancestor propagation to descendants.
def test_to_dag_greedy_ancestor_propagation() -> None:
    """Ancestors are propagated to existing descendants when edge added."""
    pdg = PDG(
        ["A", "B", "C", "D", "E"],
        {
            # First build chain B -> C -> D -> E
            ("B", "C"): EdgeProbabilities(forward=0.95, none=0.05),
            ("C", "D"): EdgeProbabilities(forward=0.90, none=0.10),
            ("D", "E"): EdgeProbabilities(forward=0.85, none=0.15),
            # Then add A -> B - ancestors must propagate to C, D, E
            ("A", "B"): EdgeProbabilities(forward=0.80, none=0.20),
            # This would create cycle (E -> A) since A is ancestor of E
            ("A", "E"): EdgeProbabilities(backward=0.70, none=0.30),
        },
    )
    result = pdg.to_dag_greedy()

    # Chain of 4 edges built, E -> A skipped due to cycle
    assert result.edges_included == 4
    assert result.edges_skipped_cycle == 1

    dag = result.dag
    # Verify the chain exists
    assert ("A", "B") in dag.edges
    assert ("B", "C") in dag.edges
    assert ("C", "D") in dag.edges
    assert ("D", "E") in dag.edges


# Test to_dag_greedy with diamond pattern visits nodes once.
def test_to_dag_greedy_diamond_pattern() -> None:
    """Diamond pattern doesn't revisit nodes during propagation."""
    pdg = PDG(
        ["A", "B", "C", "D"],
        {
            # Create diamond: A -> B -> D and A -> C -> D
            ("A", "B"): EdgeProbabilities(forward=0.95, none=0.05),
            ("A", "C"): EdgeProbabilities(forward=0.90, none=0.10),
            ("B", "D"): EdgeProbabilities(forward=0.85, none=0.15),
            ("C", "D"): EdgeProbabilities(forward=0.80, none=0.20),
        },
    )
    result = pdg.to_dag_greedy()

    # All 4 edges should be included (no cycles)
    assert result.edges_included == 4
    assert result.edges_skipped_cycle == 0

    dag = result.dag
    assert ("A", "B") in dag.edges
    assert ("A", "C") in dag.edges
    assert ("B", "D") in dag.edges
    assert ("C", "D") in dag.edges


# Test to_dag_greedy propagates through diamond descendants.
def test_to_dag_greedy_diamond_descendant_propagation() -> None:
    """BFS visits descendant only once even with multiple paths."""
    pdg = PDG(
        ["A", "B", "C", "D", "E", "F"],
        {
            # Build lower diamond first: D -> F, E -> F
            ("D", "F"): EdgeProbabilities(forward=0.99, none=0.01),
            ("E", "F"): EdgeProbabilities(forward=0.98, none=0.02),
            # Then B -> D, B -> E (B has two children)
            ("B", "D"): EdgeProbabilities(forward=0.97, none=0.03),
            ("B", "E"): EdgeProbabilities(forward=0.96, none=0.04),
            # Finally A -> B triggers propagation through D,E to F (twice)
            ("A", "B"): EdgeProbabilities(forward=0.95, none=0.05),
            # Add C -> F to verify cycle detection works after propagation
            ("C", "F"): EdgeProbabilities(forward=0.94, none=0.06),
        },
    )
    result = pdg.to_dag_greedy()

    # All 6 edges included (no cycles in this structure)
    assert result.edges_included == 6
    assert result.edges_skipped_cycle == 0


# Test GreedyDAGResult is a proper NamedTuple.
def test_greedy_dag_result_namedtuple() -> None:
    """GreedyDAGResult has expected attributes."""
    from causaliq_core.graph import GreedyDAGResult

    pdg = PDG(
        ["A", "B"], {("A", "B"): EdgeProbabilities(forward=0.8, none=0.2)}
    )
    result = pdg.to_dag_greedy()

    assert isinstance(result, GreedyDAGResult)

    # Access by attribute
    assert result.dag is not None
    assert result.edges_included == 1
    assert result.edges_skipped_cycle == 0
    assert result.edges_skipped_threshold == 0
    assert result.tie_breaks_applied == 0

    # Access by index (NamedTuple behaviour)
    assert result[0] == result.dag
    assert result[1] == 1
