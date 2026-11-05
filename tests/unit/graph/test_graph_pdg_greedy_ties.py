"""Greedy DAG extraction: tolerance-based ties and deterministic ranking."""

from typing import Dict, List, Tuple

from causaliq_core.graph import PDG, EdgeProbabilities

PairMap = Dict[Tuple[str, str], Tuple[float, float]]


# Return the extracted DAG edges for a forward/backward probability map.
def _dag_edges(pairs: PairMap) -> List[Tuple[str, str]]:
    """Extract DAG edges from forward/backward probability pairs."""
    edges = {
        pair: EdgeProbabilities(
            forward=forward, backward=backward, none=1.0 - forward - backward
        )
        for pair, (forward, backward) in pairs.items()
    }
    return list(PDG(["A", "B", "C"], edges).to_dag_greedy().dag.edges)


# Test that an orientation difference within the tolerance is a tie.
def test_orientation_noise_uses_alphabetical_tie_break() -> None:
    """A 1e-15 orientation difference counts as a tie."""
    probs = EdgeProbabilities(
        forward=0.4, backward=0.4 + 1e-15, none=0.2 - 1e-15
    )
    result = PDG(["A", "B"], {("A", "B"): probs}).to_dag_greedy()
    assert list(result.dag.edges) == [("A", "B")]
    assert result.tie_breaks_applied == 1


# Test that an orientation difference beyond the tolerance picks backward.
def test_orientation_beyond_tolerance_uses_backward() -> None:
    """A 1e-6 orientation difference is a real preference."""
    probs = EdgeProbabilities(
        forward=0.4, backward=0.4 + 1e-6, none=0.2 - 1e-6
    )
    result = PDG(["A", "B"], {("A", "B"): probs}).to_dag_greedy()
    assert list(result.dag.edges) == [("B", "A")]
    assert result.tie_breaks_applied == 0


# Test that an edge hovering at the threshold is kept.
def test_threshold_noise_keeps_edge() -> None:
    """A p_exist 1e-15 below the threshold is still included."""
    probs = EdgeProbabilities(forward=0.3 - 1e-15, none=0.7 + 1e-15)
    result = PDG(["A", "B"], {("A", "B"): probs}).to_dag_greedy(threshold=0.3)
    assert list(result.dag.edges) == [("A", "B")]
    assert result.edges_skipped_threshold == 0


# Test that an edge clearly below the threshold is excluded.
def test_threshold_below_tolerance_is_skipped() -> None:
    """A p_exist 1e-6 below the threshold is skipped."""
    probs = EdgeProbabilities(forward=0.3 - 1e-6, none=0.7 + 1e-6)
    result = PDG(["A", "B"], {("A", "B"): probs}).to_dag_greedy(threshold=0.3)
    assert list(result.dag.edges) == []
    assert result.edges_skipped_threshold == 1


# Test that 1e-16 probability noise cannot change the extracted DAG.
def test_perturbed_probabilities_extract_same_dag() -> None:
    """Two PDGs differing by 2e-16 yield the same DAG."""
    base: PairMap = {
        ("A", "B"): (0.5, 0.5),
        ("A", "C"): (0.5, 0.5),
        ("B", "C"): (0.5, 0.5),
    }
    perturbed: PairMap = {
        pair: (forward - 1e-16, backward + 1e-16)
        for pair, (forward, backward) in base.items()
    }
    assert _dag_edges(base) == _dag_edges(perturbed)


# Test that edge insertion order cannot change the extracted DAG.
def test_edge_order_does_not_change_extracted_dag() -> None:
    """Reversed insertion order yields the same DAG."""
    pairs = [("A", "B"), ("A", "C"), ("B", "C")]
    forward = {
        pair: EdgeProbabilities(forward=0.6, none=0.4) for pair in pairs
    }
    reversed_pairs = {
        pair: EdgeProbabilities(forward=0.6, none=0.4)
        for pair in reversed(pairs)
    }
    first = list(PDG(["A", "B", "C"], forward).to_dag_greedy().dag.edges)
    second = list(
        PDG(["A", "B", "C"], reversed_pairs).to_dag_greedy().dag.edges
    )
    assert first == second
