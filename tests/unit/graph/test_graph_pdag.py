import pytest

from causaliq_core.graph import PDAG, NotPDAGError
from tests.functional.fixtures import example_dags as dag
from tests.functional.fixtures import example_pdags as pdag
from tests.functional.fixtures import example_sdgs as sdg


# bad argument types
def test_graph_pdag_type_error1():
    with pytest.raises(TypeError):
        PDAG()
    with pytest.raises(TypeError):
        PDAG(32)
    with pytest.raises(TypeError):
        PDAG("not", "right")


# bad type within nodes
def test_graph_pdag_type_error2():
    with pytest.raises(TypeError):
        PDAG([1], [])


# bad type within edges
def test_graph_pdag_type_error3():
    with pytest.raises(TypeError):
        PDAG(["A", "B"], [3])
    with pytest.raises(TypeError):
        PDAG(["A", "B"], ["S"])
    with pytest.raises(TypeError):
        PDAG(["A", "B"], [("A", "->")])
    with pytest.raises(TypeError):
        PDAG(["A", "B"], [("A", "->", True)])


# empty node name
def test_graph_pdag_value_error1():
    with pytest.raises(ValueError):
        PDAG(["A", "B", ""], [])


# duplicate node name
def test_graph_pdag_value_error2():
    with pytest.raises(ValueError):
        PDAG(["A", "B", "A"], [])


# cylic edge
def test_graph_pdag_value_error3():
    with pytest.raises(ValueError):
        PDAG(["A", "B"], [("A", "->", "A")])


# invalid edge symbol
def test_graph_pdag_value_error4():
    with pytest.raises(TypeError):
        PDAG(["A", "B"], [("A", "?", "B")])


# edge references unknown node
def test_graph_pdag_value_error5():
    with pytest.raises(ValueError):
        PDAG(["A", "B"], [("A", "->", "C")])


# duplicate edges
def test_graph_pdag_value_error6():
    with pytest.raises(ValueError):
        PDAG(["A", "B"], [("A", "o-o", "B"), ("A", "->", "B")])
    with pytest.raises(ValueError):
        PDAG(["A", "B"], [("A", "o-o", "B"), ("B", "->", "A")])


# unsupported edge types for PDAG
def test_graph_pdag_value_error7():
    with pytest.raises(NotPDAGError):
        PDAG(["A", "B"], [("A", "o-o", "B")])
    with pytest.raises(NotPDAGError):
        PDAG(["A", "B"], [("A", "o->", "B")])
    with pytest.raises(NotPDAGError):
        PDAG(["A", "B"], [("A", "<->", "B")])


# cycles present
def test_graph_pdag_value_error8():
    with pytest.raises(NotPDAGError):  # directed & cyclic
        PDAG(
            ["A", "B", "C"],
            [("A", "->", "B"), ("B", "->", "C"), ("C", "->", "A")],
        )
    with pytest.raises(NotPDAGError):  # partially directed with cycle
        PDAG(
            ["A", "B", "C", "D"],
            [
                ("A", "->", "B"),
                ("B", "->", "C"),
                ("C", "->", "A"),
                ("A", "-", "D"),
            ],
        )


# empty graph
def test_graph_pdag_empty_ok():
    pdag.empty(pdag.empty())


# single node DAG
def test_graph_pdag_a_ok():
    pdag.a(pdag.a())


# A -> B chain
def test_graph_pdag_ab_ok():
    pdag.ab(pdag.ab())


# A -> B chain
def test_graph_pdag_ab_2_ok():
    pdag.ab_2(pdag.ab_2())


# B -> A chain
def test_graph_pdag_ba_ok():
    pdag.ba(pdag.ba())


# A, B unconnected
def test_graph_pdag_a_b_ok():
    pdag.a_b(pdag.a_b())


# A - B PDAG
def test_graph_pdag_ab3_ok():
    pdag.ab3(pdag.ab3())


# A, B, C unconnected
def test_graph_pdag_a_b_c_ok():
    pdag.a_b_c(pdag.a_b_c())


# A -> C, B
def test_graph_pdag_ac_b_ok():
    pdag.ac_b(pdag.ac_b())


# A - C, B
def test_graph_pdag_ac_b2_ok():
    pdag.ac_b2(pdag.ac_b2())


# A -> B -> C
def test_graph_pdag_abc_ok():
    pdag.abc(pdag.abc())


# A -> B -> C
def test_graph_pdag_abc2_ok():
    pdag.abc2(pdag.abc2())


# A - B -> C
def test_graph_pdag_abc3_ok():
    pdag.abc3(pdag.abc3())


# A - B - C
def test_graph_pdag_abc4_ok():
    pdag.abc4(pdag.abc4())


# A -> B - C
def test_graph_pdag_abc5_ok():
    pdag.abc5(pdag.abc5())


# C - A - B
def test_graph_pdag_abc6_ok():
    pdag.abc6(pdag.abc6())


# B <- A -> C - common cause
def test_graph_pdag_ab_ac_ok():
    pdag.ab_ac(pdag.ab_ac())


# A <- B -> C - common cause
def test_graph_pdag_ba_bc_ok():
    pdag.ba_bc(pdag.ba_bc())


# A -> C <- B - common effect
def test_graph_pdag_ac_bc_ok():
    pdag.ac_bc(pdag.ac_bc())


# A -> B <- C - common effect
def test_graph_pdag_ab_cb_ok():
    pdag.ab_cb(pdag.ab_cb())


# A -> B -> C <- A
def test_graph_pdag_abc_acyclic_ok():
    pdag.abc_acyclic(pdag.abc_acyclic())


# A -> B -> C - A
def test_graph_pdag_abc_acyclic2_ok():
    pdag.abc_acyclic2(pdag.abc_acyclic2())


# A -- B -- C, A --> C
def test_graph_pdag_abc_acyclic3_ok():
    pdag.abc_acyclic3(pdag.abc_acyclic3())


# A -- B -- C -- A
def test_graph_pdag_abc_acyclic4_ok():
    pdag.abc_acyclic4(pdag.abc_acyclic4())


# 5-node CANCER DAG as a PDAG
def test_graph_pdag_cancer1_OK():
    pdag.cancer1(pdag.cancer1())


# 5-node CANCER PDAG with 2 undirected edges
def test_graph_pdag_cancer2_OK():
    pdag.cancer2(pdag.cancer2())


# 5-node CANCER skeleton PDAG
def test_graph_pdag_cancer3_OK():
    pdag.cancer3(pdag.cancer3())


# Fully-orientated Asia PDAG
def test_graph_pdag_asia_OK():
    pdag.asia(pdag.asia())


# Exemplar 4 node PDAGs from Andersson et al., 1995


# 1  2  3  4 PDAG
def test_graph_pdag_and4_1_OK():
    pdag.and4_1(pdag.and4_1())


# 1 - 2  3  4 PDAG
def test_graph_pdag_and4_2_OK():
    pdag.and4_2(pdag.and4_2())


# 1 - 2  3 - 4 PDAG
def test_graph_pdag_and4_3_OK():
    pdag.and4_3(pdag.and4_3())


# 1 - 2 - 3  4 PDAG
def test_graph_pdag_and4_4_OK():
    pdag.and4_4(pdag.and4_4())


# 1 -> 2 <- 3  4 PDAG
def test_graph_pdag_and4_5_OK():
    pdag.and4_5(pdag.and4_5())


# 1 - 2 - 3 - 1  4 PDAG
def test_graph_pdag_and4_6_OK():
    pdag.and4_6(pdag.and4_6())


# 1 - 2 - 3 - 4 PDAG
def test_graph_pdag_and4_7_OK():
    pdag.and4_7(pdag.and4_7())


# 1 -> 2 <- 3 - 4 PDAG
def test_graph_pdag_and4_8_OK():
    pdag.and4_8(pdag.and4_8())


# 3 - 2 - 1, 2 - 4 (undirected star) PDAG
def test_graph_pdag_and4_9_OK():
    pdag.and4_9(pdag.and4_9())


# 1 -> 2 -> 4, 3 -> 2
def test_graph_pdag_and4_10_OK():
    pdag.and4_10(pdag.and4_10())


# 1 -> 2 <- 4, 3 -> 2 (star collider)
def test_graph_pdag_and4_11_OK():
    pdag.and4_11(pdag.and4_11())


# 2 - 3 - 1 - 2 - 4
def test_graph_pdag_and4_12_OK():
    pdag.and4_12(pdag.and4_12())


# 2 <- 1 - 3 -> 2 <- 4
def test_graph_pdag_and4_13_OK():
    pdag.and4_13(pdag.and4_13())


# 2 <- 1 -> 3 <- 2 <- 4
def test_graph_pdag_and4_14_OK():
    pdag.and4_14(pdag.and4_14())


# 2->4<-3, 2-1-3 (square, 1 collider)
def test_graph_pdag_and4_15_OK():
    pdag.and4_15(pdag.and4_15())


# 2->4<-3, 2->1<-3 (square colliders)
def test_graph_pdag_and4_16_OK():
    pdag.and4_16(pdag.and4_16())


# 4 - 3 - 1 - 2 - 4 - 1 (undirected square)
def test_graph_pdag_and4_17_OK():
    pdag.and4_17(pdag.and4_17())


# complete skeleton
def test_graph_pdag_complete4_OK():
    pdag.complete4(pdag.complete4())


# 1 -2 -3 -4 -1 (unextendable square)
def test_graph_pdag_and4_inv1_OK():
    pdag.and4_inv1(pdag.and4_inv1())


# Equality and non-equality tests


# compare identical empty PDAGs
def test_graph_pdag_empty_eq():
    assert pdag.empty() == pdag.empty()
    assert (pdag.empty() != pdag.empty()) is False


# compare identical single node PDAGs
def test_graph_pdag_a_eq():
    assert pdag.a() == pdag.a()
    assert (pdag.a() != pdag.a()) is False


# compare identical DAGs
def test_graph_pdag_ab_eq():
    assert dag.ab() == dag.ab()
    assert (dag.ab() != dag.ab()) is False


# identical, differently specified PDAGs
def test_graph_pdag_ab_2_eq():
    assert pdag.ab_2() == pdag.ab()
    assert (pdag.ab_2() != pdag.ab()) is False


# compare identical three node PDAGs (1)
def test_graph_pdag_abc_eq():
    assert pdag.abc() == pdag.abc()
    assert (pdag.abc() != pdag.abc()) is False


# compare identical three node PDAGs (2)
def test_graph_pdag_abc3_eq():
    assert pdag.abc3() == pdag.abc3()
    assert (pdag.abc3() != pdag.abc3()) is False


# compare identical three node PDAGs (3)
def test_graph_pdag_abc4_eq():
    assert pdag.abc4() == pdag.abc4()
    assert (pdag.abc4() != pdag.abc4()) is False


# compare identical SDG and PDAG
def test_graph_pdag_sdg_ab_eq():
    assert pdag.ab() == sdg.ab()
    assert (pdag.ab() != sdg.ab()) is False


# compare identical DAG and PDAG
def test_graph_pdag_dag_ab_eq():
    assert pdag.ab() == dag.ab()
    assert (pdag.ab() != dag.ab()) is False


# compare PDAG with non DAGs
def test_graph_pdag_ne1():
    assert (pdag.ab() is None) is False
    assert pdag.ab() is not None
    assert (pdag.ab() == 1) is False
    assert pdag.ab() != 1
    assert (pdag.ab() == 4.7) is False
    assert pdag.ab() != 4.7
    assert (pdag.ab() == "string") is False
    assert pdag.ab() != "string"


# compare different DAGs
def test_graph_pdag_ne2():
    assert (pdag.a() == pdag.empty()) is False
    assert pdag.a() != pdag.empty()
    assert (pdag.ab() == pdag.empty()) is False
    assert pdag.ab() != pdag.empty()
    assert (pdag.ab() == pdag.ba()) is False
    assert pdag.ab() != pdag.ba()
    assert (pdag.ab() == pdag.a_b()) is False
    assert pdag.ab() != pdag.a_b()
    assert (pdag.ab() == pdag.abc()) is False
    assert pdag.ab() != pdag.abc()
    assert (pdag.ab_ac() == pdag.ac_bc()) is False
    assert pdag.ab_ac() != pdag.ac_bc()
