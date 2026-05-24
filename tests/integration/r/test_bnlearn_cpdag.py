"""Integration tests for bnlearn_cpdag using a live R/bnlearn session.

These tests require a working R installation with bnlearn and rpy2.
They are auto-skipped when R is not available (see tests/conftest.py).
Run explicitly with: pytest -m r_integration
"""

import pytest

from causaliq_core.graph import PDAG
from causaliq_core.graph.enums import EdgeType
from causaliq_core.r.bnlearn import bnlearn_cpdag


# Test CPDAG of a single-node PDAG has no edges.
@pytest.mark.r_integration
def test_bnlearn_cpdag_single_node():
    pdag = PDAG(["A"], [])
    result = bnlearn_cpdag(pdag)
    assert isinstance(result, PDAG)
    assert result.nodes == ["A"]
    assert result.edges == {}


# Test CPDAG of a two-node DAG gives an undirected edge.
@pytest.mark.r_integration
def test_bnlearn_cpdag_two_node_dag_gives_undirected_edge():
    # A->B: MEC also contains B->A (same skeleton, no v-structures)
    # so bnlearn returns undirected A-B
    pdag = PDAG(["A", "B"], [("A", "->", "B")])
    result = bnlearn_cpdag(pdag)
    assert isinstance(result, PDAG)
    assert sorted(result.nodes) == ["A", "B"]
    edge_types = set(result.edges.values())
    assert edge_types == {EdgeType.UNDIRECTED}


# Test CPDAG of a chain A->B->C has all undirected edges.
@pytest.mark.r_integration
def test_bnlearn_cpdag_chain_gives_all_undirected_edges():
    # Chain A->B->C is Markov equivalent to A<-B->C and A<-B<-C,
    # so bnlearn returns A-B-C with all undirected edges.
    pdag = PDAG(
        ["A", "B", "C"],
        [("A", "->", "B"), ("B", "->", "C")],
    )
    result = bnlearn_cpdag(pdag)
    assert isinstance(result, PDAG)
    assert sorted(result.nodes) == ["A", "B", "C"]
    edge_types = set(result.edges.values())
    assert edge_types == {EdgeType.UNDIRECTED}
    assert len(result.edges) == 2


# Test CPDAG of a v-structure preserves all directed edges.
@pytest.mark.r_integration
def test_bnlearn_cpdag_v_structure_preserves_directed_edges():
    # A->C<-B is a v-structure: unique in its MEC, so CPDAG = A->C<-B
    pdag = PDAG(
        ["A", "B", "C"],
        [("A", "->", "C"), ("B", "->", "C")],
    )
    result = bnlearn_cpdag(pdag)
    assert isinstance(result, PDAG)
    assert sorted(result.nodes) == ["A", "B", "C"]
    edge_types = set(result.edges.values())
    assert edge_types == {EdgeType.DIRECTED}
    assert len(result.edges) == 2


# Test CPDAG of a disconnected graph handles each component independently.
@pytest.mark.r_integration
def test_bnlearn_cpdag_disconnected_graph():
    # A->B (one component), C isolated: CPDAG has A-B undirected, no C edges
    pdag = PDAG(["A", "B", "C"], [("A", "->", "B")])
    result = bnlearn_cpdag(pdag)
    assert isinstance(result, PDAG)
    assert sorted(result.nodes) == ["A", "B", "C"]
    assert len(result.edges) == 1
    edge_types = set(result.edges.values())
    assert edge_types == {EdgeType.UNDIRECTED}
