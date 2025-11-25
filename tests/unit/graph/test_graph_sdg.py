import example_sdgs as ex
import pytest

from causaliq_core.graph import EdgeType
from causaliq_core.graph.sdg import SDG


# bad argument types
def test_graph_sdg_type_error1():
    with pytest.raises(TypeError):
        SDG()
    with pytest.raises(TypeError):
        SDG(32)
    with pytest.raises(TypeError):
        SDG("not", "right")


# bad type within nodes
def test_graph_sdg_type_error2():
    with pytest.raises(TypeError):
        SDG([1], [])


# bad type within edges
def test_graph_sdg_type_error3():
    with pytest.raises(TypeError):
        SDG(["A", "B"], [3])
    with pytest.raises(TypeError):
        SDG(["A", "B"], ["S"])
    with pytest.raises(TypeError):
        SDG(["A", "B"], [("A", "->")])
    with pytest.raises(TypeError):
        SDG(["A", "B"], [("A", "->", True)])


# empty node name
def test_graph_sdg_value_error1():
    with pytest.raises(ValueError):
        SDG(["A", "B", ""], [])


# duplicate node name
def test_graph_sdg_value_error2():
    with pytest.raises(ValueError):
        SDG(["A", "B", "A"], [])


# cylic edge
def test_graph_sdg_value_error3():
    with pytest.raises(ValueError):
        SDG(["A", "B"], [("A", "->", "A")])


# invalid edge symbol
def test_graph_sdg_value_error4():
    with pytest.raises(TypeError):
        SDG(["A", "B"], [("A", "?", "B")])


# edge references unknown node
def test_graph_sdg_value_error5():
    with pytest.raises(ValueError):
        SDG(["A", "B"], [("A", "o-o", "C")])


# duplicate edges
def test_graph_sdg_value_error6():
    with pytest.raises(ValueError):
        SDG(["A", "B"], [("A", "o-o", "B"), ("A", "->", "B")])
    with pytest.raises(ValueError):
        SDG(["A", "B"], [("A", "o-o", "B"), ("B", "->", "A")])


# A - B graph validates OK
def test_graph_sdg_ab_undirected_ok():
    ex.ab_undirected(ex.ab_undirected())


# three node mixed graph validates OK
def test_graph_sdg_abc_mixed_ok():
    ex.abc_mixed(ex.abc_mixed())


# three node cycle validates OK
def test_graph_sdg_abc_cycle_ok():
    ex.abc_cycle(ex.abc_cycle())


# graph is equal to itself
def test_graph_sdg_abc_mixed_eq1():
    assert ex.abc_mixed() == ex.abc_mixed()
    assert (ex.abc_mixed() != ex.abc_mixed()) is False


# graph is equal to itself
def test_graph_sdg_abc_mixed_eq2():
    assert ex.abc_mixed_2() == ex.abc_mixed_2()
    assert (ex.abc_mixed_2() != ex.abc_mixed_2()) is False


# graph is equal to identical graph
def test_graph_sdg_abc_mixed_eq3():
    assert ex.abc_mixed() == ex.abc_mixed_2()
    assert (ex.abc_mixed() != ex.abc_mixed_2()) is False


# graph is equal to identical graph
def test_graph_sdg_ab_undirected_eq():
    assert ex.ab_undirected() == ex.ab_undirected()
    assert (ex.ab_undirected() != ex.ab_undirected()) is False


# graph is equal to itself
def test_graph_sdg_abc_cycle_eq():
    assert ex.abc_cycle() == ex.abc_cycle()
    assert (ex.abc_cycle() != ex.abc_cycle()) is False


# comparisons with non-graphs work OK
def test_graph_sdg_ne1():
    assert ex.ab_undirected() is not None
    assert (ex.ab_undirected() is None) is False
    assert ex.ab_undirected() != 1
    assert (ex.ab_undirected() == 1) is False


# comparisons with different graphs
def test_graph_sdg_ne2():
    assert ex.ab_undirected() != ex.abc_cycle()
    assert (ex.ab_undirected() == ex.abc_cycle()) is False
    assert ex.abc_mixed() != ex.abc_cycle()
    assert (ex.abc_mixed() == ex.abc_cycle()) is False
    assert ex.ab_undirected() != ex.abc_mixed()
    assert (ex.ab_undirected() == ex.abc_mixed()) is False


# bad argument types
def test_graph_rename_type_error_1():
    graph = ex.ab_undirected()
    with pytest.raises(TypeError):
        graph.rename()


# name_map not a dictionary
def test_graph_rename_type_error_2():
    graph = ex.ab_undirected()
    with pytest.raises(TypeError):
        graph.rename(name_map=None)
    with pytest.raises(TypeError):
        graph.rename(name_map=True)
    with pytest.raises(TypeError):
        graph.rename(name_map=37)
    with pytest.raises(TypeError):
        graph.rename(name_map=[{"A": "B"}])


# name_map has non-string keys
def test_graph_rename_type_error_3():
    graph = ex.ab_undirected()
    with pytest.raises(TypeError):
        graph.rename(name_map={1: "B"})
    with pytest.raises(TypeError):
        graph.rename(name_map={("A",): "B"})


# name_map has non-string values
def test_graph_rename_type_error_4():
    graph = ex.ab_undirected()
    with pytest.raises(TypeError):
        graph.rename(name_map={"A": 1})
    with pytest.raises(TypeError):
        graph.rename(name_map={"A": ["B"]})


# keys that are not current node name
def test_graph_rename_value_error_1():
    graph = ex.ab_undirected()
    with pytest.raises(ValueError):
        graph.rename(name_map={"C": "Q"})


# Renames on undirected graph


# change first node name, keeping order
def test_graph_rename_sdg_ab_1_ok():
    graph = ex.ab_undirected()
    graph.rename(name_map={"A": "AA", "B": "B"})

    assert isinstance(graph, SDG)
    assert graph.nodes == ["AA", "B"]
    assert graph.edges == {("AA", "B"): EdgeType.UNDIRECTED}
    assert graph.parents == {}
    assert graph.is_directed is False
    assert graph.is_partially_directed is True
    assert graph.has_directed_cycles is False


# change first node name, changing order
def test_graph_rename_sdg_ab_2_ok():
    graph = ex.ab_undirected()
    graph.rename(name_map={"A": "C", "B": "B"})

    assert isinstance(graph, SDG)
    assert graph.nodes == ["B", "C"]
    assert graph.edges == {("B", "C"): EdgeType.UNDIRECTED}
    assert graph.parents == {}
    assert graph.is_directed is False
    assert graph.is_partially_directed is True
    assert graph.has_directed_cycles is False


# change second node name, keeping order
def test_graph_rename_sdg_ab_3_ok():
    graph = ex.ab_undirected()
    graph.rename(name_map={"B": "BB", "A": "A"})

    assert isinstance(graph, SDG)
    assert graph.nodes == ["A", "BB"]
    assert graph.edges == {("A", "BB"): EdgeType.UNDIRECTED}
    assert graph.parents == {}
    assert graph.is_directed is False
    assert graph.is_partially_directed is True
    assert graph.has_directed_cycles is False


# change both names, changing order
def test_graph_rename_sdg_ab_4_ok():
    graph = ex.ab_undirected()
    graph.rename(name_map={"A": "X001A", "B": "X000B"})

    assert isinstance(graph, SDG)
    assert graph.nodes == ["X000B", "X001A"]
    assert graph.edges == {("X000B", "X001A"): EdgeType.UNDIRECTED}
    assert graph.parents == {}
    assert graph.is_directed is False
    assert graph.is_partially_directed is True
    assert graph.has_directed_cycles is False


# change names and order
def test_graph_rename_sdg_abc_1_ok():
    graph = ex.abc_mixed()
    graph.rename(name_map={"A": "X002A", "B": "X001B", "C": "X000C"})

    assert isinstance(graph, SDG)
    assert graph.nodes == ["X000C", "X001B", "X002A"]
    assert graph.edges == {
        ("X001B", "X002A"): EdgeType.UNDIRECTED,
        ("X001B", "X000C"): EdgeType.SEMIDIRECTED,
    }
    assert graph.parents == {}
    assert graph.is_directed is False
    assert graph.is_partially_directed is False
    assert graph.has_directed_cycles is False


# Additional tests for 100% coverage


# test the classmethod version
def test_sdg_partial_order_classmethod():
    parents = {"B": ["A"]}  # Simple valid ordering
    nodes = ["A", "B"]  # Need to provide nodes list
    order = SDG.partial_order(parents, nodes)
    assert order == [{"A"}, {"B"}]

    # Test with cycle
    parents = {"A": ["B"], "B": ["A"]}
    order = SDG.partial_order(parents)
    assert order is None

    # Test with nodes parameter
    parents = {"B": ["A"]}
    order = SDG.partial_order(parents, nodes=["A", "B", "C"])
    assert order == [{"A", "C"}, {"B"}]

    # Test with new_arc parameter - both nodes must exist in parents
    parents = {"B": ["A"], "A": [], "C": []}
    order = SDG.partial_order(parents, new_arc=("C", "A"))
    assert order == [
        {"C"},
        {"A"},
        {"B"},
    ]  # C->A: C removes A from parents (none), A adds C


# test type checking in partial_order
def test_sdg_partial_order_type_errors():
    with pytest.raises(TypeError):
        SDG.partial_order("not a dict")

    with pytest.raises(TypeError):
        SDG.partial_order({"B": ["A"]}, nodes="not a list or set")


# test undirected_trees method
def test_sdg_undirected_trees():
    # Test with undirected edges
    graph = SDG(["A", "B", "C", "D"], [("A", "-", "B"), ("C", "-", "D")])
    trees = graph.undirected_trees()
    assert len(trees) == 2
    assert {("A", "B")} in trees
    assert {("C", "D")} in trees

    # Test with isolated node
    graph = SDG(["A", "B", "C"], [("A", "-", "B")])
    trees = graph.undirected_trees()
    assert len(trees) == 2
    assert {("A", "B")} in trees
    assert {("C", None)} in trees

    # Test empty graph
    graph = SDG([], [])
    trees = graph.undirected_trees()
    assert trees == []


# test components method
def test_sdg_components():
    # Test single component
    graph = SDG(["A", "B", "C"], [("A", "-", "B"), ("B", "-", "C")])
    components = graph.components()
    assert components == [["A", "B", "C"]]

    # Test multiple components
    graph = SDG(["A", "B", "C", "D"], [("A", "-", "B"), ("C", "-", "D")])
    components = graph.components()
    assert components == [["A", "B"], ["C", "D"]]

    # Test with isolated nodes
    graph = SDG(["A", "B", "C"], [("A", "-", "B")])
    components = graph.components()
    assert components == [["A", "B"], ["C"]]


# test number_components method
def test_sdg_number_components():
    # Test single component
    graph = SDG(["A", "B", "C"], [("A", "-", "B"), ("B", "-", "C")])
    assert graph.number_components() == 1

    # Test multiple components
    graph = SDG(["A", "B", "C", "D"], [("A", "-", "B"), ("C", "-", "D")])
    assert graph.number_components() == 2

    # Test isolated nodes
    graph = SDG(["A", "B", "C"], [])
    assert graph.number_components() == 3


# test adjacency matrix conversion
def test_sdg_to_adjmat():
    # Test directed graph
    graph = SDG(["A", "B"], [("A", "->", "B")])
    adj = graph.to_adjmat()
    assert adj.loc["A", "B"] == 1
    assert adj.loc["B", "A"] == 0

    # Test undirected graph
    graph = SDG(["A", "B"], [("A", "-", "B")])
    adj = graph.to_adjmat()
    assert adj.loc["A", "B"] == 2  # EdgeType.UNDIRECTED has value 2


# test __str__ method
def test_sdg_str_method():
    # Test empty graph
    graph = SDG([], [])
    assert str(graph) == "Empty graph"

    # Test single node
    graph = SDG(["A"], [])
    s = str(graph)
    assert "DAG" in s
    assert "1 node" in s
    assert "0 edge" in s
    assert "1 component" in s

    # Test graph with edges
    graph = SDG(["A", "B"], [("A", "->", "B")])
    s = str(graph)
    assert "DAG" in s
    assert "2 nodes" in s
    assert "1 edge" in s
    assert "A: ->B" in s


# test is_PDAG for various cases
def test_sdg_is_pdag_cases():
    # Test mixed graph that is PDAG
    graph = SDG(["A", "B", "C"], [("A", "->", "B"), ("B", "-", "C")])
    assert graph.is_PDAG() is True

    # Test purely undirected graph (is partially directed, so is PDAG)
    graph = SDG(["A", "B"], [("A", "-", "B")])
    assert graph.is_PDAG() is True  # undirected graphs are PDAGs


# test edge reordering behavior
def test_sdg_edge_reordering():
    # Test that non-directional edges get reordered alphabetically
    graph = SDG(["A", "B"], [("B", "-", "A")])  # B comes before A in edge
    assert ("A", "B") in graph.edges  # Should be reordered to A, B
    assert ("B", "A") not in graph.edges

    # Test bidirectional edge reordering
    graph = SDG(["C", "A"], [("C", "<->", "A")])
    assert ("A", "C") in graph.edges  # Should be reordered to A, C
    assert graph.edges[("A", "C")] == EdgeType.BIDIRECTED


# test parent collection for directed edges
def test_sdg_parent_collection():
    # Test multiple parents
    graph = SDG(["A", "B", "C"], [("A", "->", "C"), ("B", "->", "C")])
    assert graph.parents == {"C": ["A", "B"]}

    # Test that parents are sorted
    graph = SDG(["Z", "A", "B"], [("Z", "->", "A"), ("B", "->", "A")])
    assert graph.parents == {
        "A": ["B", "Z"]
    }  # Should be sorted alphabetically


# test complex tree structures
def test_sdg_complex_undirected_trees():
    # Test connected tree - undirected_trees() returns one component
    # for connected graph
    graph = SDG(
        ["A", "B", "C", "D"],
        [("A", "-", "B"), ("B", "-", "C"), ("C", "-", "D")],
    )
    trees = graph.undirected_trees()
    # Connected undirected graph returns single component
    assert len(trees) == 1
    assert len(trees[0]) == 3  # Should contain all three edges


# test new_arc parameter edge cases
def test_sdg_partial_order_new_arc():
    # Test with existing nodes to ensure all paths are covered
    parents = {"B": ["A"], "A": []}  # Both nodes must exist in parents
    nodes = ["A", "B"]
    # Test adding edge A->B: A removes B from parents (none),
    # B adds A (already has A)
    order = SDG.partial_order(parents, nodes=nodes, new_arc=("A", "B"))
    assert order == [
        {"A"},
        {"B"},
    ]  # Same order since B already has A as parent

    # Test with different new arc
    parents = {"B": ["A"], "A": [], "C": []}
    order = SDG.partial_order(parents, new_arc=("C", "A"))
    assert order == [{"C"}, {"A"}, {"B"}]  # C->A creates new ordering

    # Test case to create actual cycle
    parents = {"A": ["B"], "B": []}
    nodes = ["A", "B"]
    order = SDG.partial_order(parents, nodes=nodes, new_arc=("B", "A"))
    assert order == [{"B"}, {"A"}]  # Valid ordering exists


# test to hit the missing lines
def test_sdg_is_pdag_with_cycle_to_hit_line_242():
    # Create a mixed graph that will call is_PDAG and hit line 242-251
    # This creates a graph with directed edges only in mixed context
    graph = SDG(["A", "B", "C"], [("A", "->", "B"), ("B", "-", "C")])
    # Call is_PDAG which creates arcs list and calls SDG constructor
    # (lines 246-251)
    result = graph.is_PDAG()
    assert result is True  # Should be a valid PDAG


# test line 239
def test_sdg_is_pdag_not_partially_directed():
    # Create graph that is not partially directed to hit line 239
    graph = SDG(
        ["A", "B"], [("A", "<->", "B")]
    )  # bidirected makes is_partially_directed=False
    result = graph.is_PDAG()
    assert result is False  # Should return False at line 239


# test to cover line 239 (directed graph case)
def test_sdg_is_pdag_directed_graph():
    # Test directed graph - should call self.is_DAG() at line 239
    graph = SDG(["A", "B", "C"], [("A", "->", "B"), ("B", "->", "C")])
    assert graph.is_directed  # Should be True for all directed edges
    assert graph.is_PDAG()  # Should return result of is_DAG() from line 239


# Additional test for line 239
def test_sdg_coverage_line_239():
    # Create bidirected graph (not partially directed)
    graph = SDG(["A", "B"], [("A", "<->", "B")])
    assert (
        not graph.is_partially_directed
    )  # Verify it's not partially directed
    result = graph.is_PDAG()
    assert result is False  # This should hit line 239
