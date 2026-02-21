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
