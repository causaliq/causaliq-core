"""Integration tests for bnlearn_compare via live R/bnlearn.

These tests require a working R installation with bnlearn
installed. Auto-skipped when R is unavailable (conftest.py).
Run explicitly with: pytest -m r_integration
"""

import pytest

from causaliq_core.graph import PDAG
from causaliq_core.r.bnlearn import bnlearn_compare


# Test identical v-structure PDAGs give perfect comparison metrics.
@pytest.mark.r_integration
def test_bnlearn_compare_identical_graph_gives_perfect_metrics():
    # A->C<-B is a v-structure: unique MEC, so CPDAG == DAG.
    # Comparing a graph against itself must yield tp=edges, rest 0.
    pdag = PDAG(
        ["A", "B", "C"],
        [("A", "->", "C"), ("B", "->", "C")],
    )
    result = bnlearn_compare(pdag, pdag)
    assert result == {"tp": 2, "fp": 0, "fn": 0, "shd": 0}


# Test empty learned graph gives fn equal to reference edge count.
@pytest.mark.r_integration
def test_bnlearn_compare_empty_learned_gives_fn_equal_to_ref_edges():
    # pdag is the "learned" graph; ref is the ground truth.
    # With no learned edges, all reference edges are false negatives.
    pdag = PDAG(["A", "B", "C"], [])
    ref = PDAG(
        ["A", "B", "C"],
        [("A", "->", "C"), ("B", "->", "C")],
    )
    result = bnlearn_compare(pdag, ref)
    assert result["tp"] == 0
    assert result["fp"] == 0
    assert result["fn"] == 2
    assert result["shd"] == 2


# Test extra edge in learned graph appears as a false positive.
@pytest.mark.r_integration
def test_bnlearn_compare_extra_edge_gives_false_positive():
    # pdag has one edge not in ref, so fp >= 1 and fn = 0.
    pdag = PDAG(["A", "B"], [("A", "->", "B")])
    ref = PDAG(["A", "B"], [])
    result = bnlearn_compare(pdag, ref)
    assert result["tp"] == 0
    assert result["fp"] >= 1
    assert result["fn"] == 0
    for key in ("tp", "fp", "fn", "shd"):
        assert isinstance(result[key], int)
        assert result[key] >= 0
