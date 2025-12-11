import pytest

from causaliq_core.graph import DAG, NotDAGError
from tests.functional.fixtures import example_dags as dag
from tests.functional.fixtures import example_pdags as ex_pdag
from tests.functional.fixtures import example_sdgs as ex_sdg


# bad argument types
def test_graph_dag_type_error1():
    with pytest.raises(TypeError):
        DAG()
    with pytest.raises(TypeError):
        DAG(32)
    with pytest.raises(TypeError):
        DAG("not", "right")


# bad type within nodes
def test_graph_dag_type_error2():
    with pytest.raises(TypeError):
        DAG([1], [])


# bad type within edges
def test_graph_dag_type_error3():
    with pytest.raises(TypeError):
        DAG(["A", "B"], [3])
    with pytest.raises(TypeError):
        DAG(["A", "B"], ["S"])
    with pytest.raises(TypeError):
        DAG(["A", "B"], [("A", "->")])
    with pytest.raises(TypeError):
        DAG(["A", "B"], [("A", "->", True)])


# empty node name
def test_graph_dag_value_error1():
    with pytest.raises(ValueError):
        DAG(["A", "B", ""], [])


# duplicate node name
def test_graph_dag_value_error2():
    with pytest.raises(ValueError):
        DAG(["A", "B", "A"], [])


# cylic edge
def test_graph_dag_value_error3():
    with pytest.raises(ValueError):
        DAG(["A", "B"], [("A", "->", "A")])


# invalid edge symbol
def test_graph_dag_value_error4():
    with pytest.raises(TypeError):
        DAG(["A", "B"], [("A", "?", "B")])


# edge references unknown node
def test_graph_dag_value_error5():
    with pytest.raises(ValueError):
        DAG(["A", "B"], [("A", "->", "C")])


# duplicate edges
def test_graph_dag_value_error6():
    with pytest.raises(ValueError):
        DAG(["A", "B"], [("A", "o-o", "B"), ("A", "->", "B")])
    with pytest.raises(ValueError):
        DAG(["A", "B"], [("A", "o-o", "B"), ("B", "->", "A")])


# undirected edges
def test_graph_dag_value_error7():
    with pytest.raises(NotDAGError):
        DAG(["A", "B"], [("A", "o-o", "B")])
    with pytest.raises(NotDAGError):
        DAG(["A", "B"], [("A", "o->", "B")])
    with pytest.raises(NotDAGError):
        DAG(["A", "B"], [("A", "-", "B")])
    with pytest.raises(NotDAGError):
        DAG(["A", "B"], [("A", "<->", "B")])


# cycles present
def test_graph_dag_value_error8():
    with pytest.raises(NotDAGError):
        DAG(
            ["A", "B", "C"],
            [("A", "->", "B"), ("B", "->", "C"), ("C", "->", "A")],
        )


# empty graph
def test_graph_dag_empty_ok():
    dag.empty(dag.empty())


# single node DAG
def test_graph_dag_a_ok():
    dag.a(dag.a())


# single node DAG
def test_graph_dag_x_ok():
    dag.x(dag.x())


# A -> B chain
def test_graph_dag_ab_ok():
    dag.ab(dag.ab())


# X -> Y chain
def test_graph_dag_xy_ok():
    dag.xy(dag.xy())


# X <- Y chain
def test_graph_dag_yx_ok():
    dag.yx(dag.yx())


# B -> A chain
def test_graph_dag_ba_ok():
    dag.ba(dag.ba())


# A, B unconnected
def test_graph_dag_a_b_ok():
    dag.a_b(dag.a_b())


# X, Y unconnected
def test_graph_dag_x_y_ok():
    dag.x_y(dag.x_y())


# A, B, C unconnected
def test_graph_dag_a_b_c_ok():
    dag.a_b_c(dag.a_b_c())


# A -> C, B
def test_graph_dag_ac_b_ok():
    dag.ac_b(dag.ac_b())


# C -> A, B
def test_graph_dag_ac_b2_ok():
    dag.ac_b2(dag.ac_b2())


# A -> B -> C
def test_graph_dag_abc_ok():
    dag.abc(dag.abc())


# X -> Y -> Z
def test_graph_dag_xyz_ok():
    dag.xyz(dag.xyz())


# A -> B -> C
def test_graph_dag_abc_2_ok():
    dag.abc_2(dag.abc_2())


# A <- B <- C
def test_graph_dag_abc3_ok():
    dag.abc3(dag.abc3())


# B <- A -> C - common cause
def test_graph_dag_ab_ac_ok():
    dag.ab_ac(dag.ab_ac())


# A <- B -> C - common cause
def test_graph_dag_ba_bc_ok():
    dag.ba_bc(dag.ba_bc())


# A -> C <- B - common effect
def test_graph_dag_ac_bc_ok():
    dag.ac_bc(dag.ac_bc())


# X -> Y <- Z - common effect
def test_graph_dag_xy_zy_ok():
    dag.xy_zy(dag.xy_zy())


# A -> B -> C <- A
def test_graph_dag_abc_acyclic_ok():
    dag.abc_acyclic(dag.abc_acyclic())


# C -> B -> A <- C
def test_graph_dag_abc_acyclic4_ok():
    dag.abc_acyclic4(dag.abc_acyclic4())


# 5-node CANCER DAG
def test_cancer_dag():
    dag.cancer(dag.cancer())


# 5-node CANCER DAG with Xray as root
def test_cancer3_dag():
    dag.cancer3(dag.cancer3())


# Correct 8-node ASIA DAG
def test_asia_dag():
    dag.asia(dag.asia())


# Wrong 8-node ASIA DAG produced by extending Asia PDAG
def test_asia2_dag():
    dag.asia2(dag.asia2())


# Exemplar 4 node PDAGs from Andersson et al., 1995


# 1  2  3  4 DAG
def test_and4_1_dag():
    dag.and4_1(dag.and4_1())


# 1 <- 2  3  4 DAG
def test_and4_2_dag():
    dag.and4_2(dag.and4_2())


# 1 <- 2  3 <- 4 DAG
def test_and4_3_dag():
    dag.and4_3(dag.and4_3())


# 1 <- 2 <- 3  4  DAG
def test_and4_4_dag():
    dag.and4_4(dag.and4_4())


# 1 -> 2 <- 3  4  DAG
def test_and4_5_dag():
    dag.and4_5(dag.and4_5())


# 1 <- 3 -> 2 -> 1  4  DAG
def test_and4_6_dag():
    dag.and4_6(dag.and4_6())


# 1 <- 2 <- 3 <- 4  DAG
def test_and4_7_dag():
    dag.and4_7(dag.and4_7())


# 1 -> 2 <- 3 <- 4  DAG
def test_and4_8_dag():
    dag.and4_8(dag.and4_8())


# 4 -> 2 -> 1, 2 -> 3
def test_and4_9_dag():
    dag.and4_9(dag.and4_9())


# 1 -> 2 -> 4, 3 -> 2
def test_and4_10_dag():
    dag.and4_10(dag.and4_10())


# 1 -> 2 <- 4, 3 -> 2 (star collider)
def test_and4_11_dag():
    dag.and4_11(dag.and4_11())


# 2 -> 1 <- 3 <- 2 <- 4
def test_and4_12_dag():
    dag.and4_12(dag.and4_12())


# 2 <- 1 <- 3 -> 2 <- 4
def test_and4_13_dag():
    dag.and4_13(dag.and4_13())


# 2 <- 1 -> 3 <- 2 <- 4
def test_and4_14_dag():
    dag.and4_14(dag.and4_14())


# 1->2->4<-3->1 (square, 1 collider)
def test_and4_15_dag():
    dag.and4_15(dag.and4_15())


# 4->3->1->2, 4->1, 4->2
def test_and4_16_dag():
    dag.and4_16(dag.and4_16())


# 4->3->1->2, 4->1, 4->2
def test_and4_17_dag():
    dag.and4_17(dag.and4_17())


# 4->3->1->2, 4->1, 4->2
def test_complete4_dag():
    dag.complete4(dag.complete4())


# BNLearn 7-node example Gaussian DAG
def test_gauss_dag():
    dag.gauss(dag.gauss())


# Equality and inequality tests


# compare identical DAGs
def test_graph_dag_empty_eq():
    assert dag.empty() == dag.empty()
    assert (dag.empty() != dag.empty()) is False


# compare identical DAGs
def test_graph_dag_a_eq():
    assert dag.a() == dag.a()
    assert (dag.a() != dag.a()) is False


# compare identical DAGs
def test_graph_dag_ab_eq():
    assert dag.ab() == dag.ab()
    assert (dag.ab() != dag.ab()) is False


# compare identical, differently specified DAGs
def test_graph_dag_ab_2_eq():
    assert dag.ab_2() == dag.ab()
    assert (dag.ab_2() != dag.ab()) is False


# compare identical DAGs
def test_graph_dag_abc_eq():
    assert dag.abc() == dag.abc()
    assert (dag.abc() != dag.abc()) is False


# compare identical, differently specified DAGs
def test_graph_dag_abc_2_eq():
    assert dag.abc_2() == dag.abc()
    assert (dag.abc_2() != dag.abc()) is False


# compare identical SDG and DAG
def test_graph_dag_graph_ab_eq():
    assert dag.ab() == ex_sdg.ab()
    assert (dag.ab() != ex_sdg.ab()) is False


# compare identical PDAG and DAG
def test_graph_dag_graph_ab2_eq():
    assert dag.ab() == ex_pdag.ab()
    assert (dag.ab() != ex_pdag.ab()) is False


# compare DAG with non DAGs
def test_graph_dag_ne1():
    assert (dag.ab() is None) is False
    assert dag.ab() is not None
    assert (dag.ab() == 1) is False
    assert dag.ab() != 1
    assert (dag.ab() == 4.7) is False
    assert dag.ab() != 4.7
    assert (dag.ab() == "string") is False
    assert dag.ab() != "string"


# compare different DAGs
def test_graph_dag_ne2():
    assert (dag.a() == dag.empty()) is False
    assert dag.a() != dag.empty()
    assert (dag.ab() == dag.empty()) is False
    assert dag.ab() != dag.empty()
    assert (dag.ab() == dag.ba()) is False
    assert dag.ab() != dag.ba()
    assert (dag.ab() == dag.a_b()) is False
    assert dag.ab() != dag.a_b()
    assert (dag.ab() == dag.abc()) is False
    assert dag.ab() != dag.abc()
    assert (dag.ab_ac() == dag.ac_bc()) is False
    assert dag.ab_ac() != dag.ac_bc()


# Test for defensive RuntimeError in ordered_nodes method (line 67)
def test_graph_dag_ordered_nodes_runtime_error(monkeypatch):
    """Test RuntimeError when partial_order returns None (cycles detected)."""
    # Create a valid DAG first
    test_dag = DAG(["A", "B"], [("A", "->", "B")])

    # Mock partial_order to return None (simulating cycles)
    def mock_partial_order(parents, nodes):
        return None

    # Patch the partial_order method to return None
    monkeypatch.setattr(test_dag, "partial_order", mock_partial_order)

    # Now calling ordered_nodes should trigger the RuntimeError on line 67
    with pytest.raises(
        RuntimeError, match="DAG has cycles - this should not happen"
    ):
        list(test_dag.ordered_nodes())
