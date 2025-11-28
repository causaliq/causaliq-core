import example_dags as ex_dag
import example_pdags as ex_pdag
import pytest

from causaliq_core.graph import fromDAG


# bad argument types
def test_graph_fromDAG_type_error():
    with pytest.raises(TypeError):
        fromDAG()
    with pytest.raises(TypeError):
        fromDAG(32)
    with pytest.raises(TypeError):
        fromDAG("not", "right")


# empty DAG
def test_graph_dag_to_pdag_empty_ok():
    dag = ex_dag.empty()
    print("\nEmpty DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.empty(pdag)


# A (single node) DAG
def test_graph_dag_to_pdag_a_ok():
    dag = ex_dag.a()
    print("\nA (single-node) DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.a(pdag)


# 2 Node DAGs


# A  B  DAG
def test_graph_dag_to_pdag_a_b_ok():
    dag = ex_dag.a_b()
    print("\nA  B  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.a_b(pdag)  # A  B  PDAG


# A -> B DAG
def test_graph_dag_to_pdag_ab_ok():
    dag = ex_dag.ab()
    print("\nA -> B DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.ab3(pdag)  # A - B  PDAG


# B -> A DAG
def test_graph_dag_to_pdag_ba_ok():
    dag = ex_dag.ba()
    print("\nB -> A DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.ab3(pdag)  # A - B  PDAG


# 3 Node DAGs


# A  B  C  DAG
def test_graph_dag_to_pdag_a_b_c_ok():
    dag = ex_dag.a_b_c()
    print("\nA  B  C  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.a_b_c(pdag)  # A  B  C  PDAG


# A -> C   B  DAG
def test_graph_dag_to_pdag_ac_b_ok():
    dag = ex_dag.ac_b()
    print("\nA -> C  B  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.ac_b2(pdag)  # A - C  B  PDAG


# C -> A   B  DAG
def test_graph_dag_to_pdag_ac_b2_ok():
    dag = ex_dag.ac_b2()
    print("\nC -> A  B  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.ac_b2(pdag)  # A - C  B  PDAG


# A -> B -> C  DAG
def test_graph_dag_to_pdag_abc_ok():
    dag = ex_dag.abc()
    print("\nA -> B -> C  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.abc4(pdag)  # A - B - C  PDAG


# A <- B <- C  DAG
def test_graph_dag_to_pdag_abc3_ok():
    dag = ex_dag.abc3()
    print("\nA <- B <- C  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.abc4(pdag)  # A - B - C  PDAG


# C <- A -> B  DAG
def test_graph_dag_to_pdag_ab_ac_ok():
    dag = ex_dag.ab_ac()
    print("\nA -> B -> C  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.abc6(pdag)  # C - A - B  PDAG


# A -> C <- B (collider)  DAG
def test_graph_dag_to_pdag_ac_bc_ok():
    dag = ex_dag.ac_bc()
    print("\nA -> C <- B  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.ac_bc(pdag)  # A -> C <- B  PDAG


# C <- A -> B -> C (complete) DAG
def test_graph_dag_to_pdag_abc_acyclic_ok():
    dag = ex_dag.abc_acyclic()
    print("\nC <- A -> B -> C  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.abc_acyclic4(pdag)  # C - A - B - C  PDAG


# Exemplar 4 node PDAGs from Andersson et al., 1995


# 1  2  3  4  DAG
def test_graph_dag_to_pdag_and4_1_ok():
    dag = ex_dag.and4_1()
    print("\n1  2  3  4  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_1(pdag)  # 1  2  3  4  PDAG


# 1 <- 2  3  4  DAG
def test_graph_dag_to_pdag_and4_2_ok():
    dag = ex_dag.and4_2()
    print("\n1 <- 2  3  4  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_2(pdag)  # 1 - 2  3  4  PDAG


# 1 <- 2  3 <- 4  DAG
def test_graph_dag_to_pdag_and4_3_ok():
    dag = ex_dag.and4_3()
    print("\n1 <- 2  3 <- 4  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_3(pdag)  # 1 - 2  3 - 4  PDAG


# 1 <- 2 <- 3  4  DAG
def test_graph_dag_to_pdag_and4_4_ok():
    dag = ex_dag.and4_4()
    print("\n1 <- 2 <- 3  4  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_4(pdag)  # 1 - 2 - 3  4  PDAG


# 1 -> 2 <- 3  4  DAG
def test_graph_dag_to_pdag_and4_5_ok():
    dag = ex_dag.and4_5()
    print("\n1 -> 2 <- 3  4  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_5(pdag)  # 1 -> 2 <- 3  4  PDAG


# 1 <- 3 -> 2 -> 1  4  DAG
def test_graph_dag_to_pdag_and4_6_ok():
    dag = ex_dag.and4_6()
    print("\n1 <- 3 -> 2 -> 1  4  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_6(pdag)  # 1 - 2 - 3 - 1  4  PDAG


# 1 <- 2 <- 3 <- 4  DAG
def test_graph_dag_to_pdag_and4_7_ok():
    dag = ex_dag.and4_7()
    print("\n1 <- 2 <- 3 <- 4  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_7(pdag)  # 1 - 2 - 3 - 4  PDAG


# 1 -> 2 <- 3 <- 4  DAG
def test_graph_dag_to_pdag_and4_8_ok():
    dag = ex_dag.and4_8()
    print("\n1 -> 2 <- 3 <- 4  DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_8(pdag)  # 1 -> 2 <- 3 - 4  PDAG


# 3 -> 2 -> 1, 2 -> 4  DAG
def test_graph_dag_to_pdag_and4_9_ok():
    dag = ex_dag.and4_9()
    print("\n1 -> 2 -> 4, 3 -> 2 DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_9(pdag)  # 3 - 2 - 1, 2 - 4 (undirected star) PDAG


# 1 -> 2 -> 4, 3 -> 2
def test_graph_dag_to_pdag_and4_10_ok():
    dag = ex_dag.and4_10()
    print("\n1 -> 2 -> 4, 3 -> 2 DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_10(pdag)  # 1 -> 2 -> 4, 3 -> 2  PDAG


# 1 -> 2 <- 4, 3 -> 2 (star collider)
def test_graph_dag_to_pdag_and4_11_ok():
    dag = ex_dag.and4_11()
    print("\n1 -> 2 <- 4, 3 -> 2 (star collider) DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_11(pdag)  # 1 -> 2 <- 4, 3 -> 2 (star collider) PDAG


# 2 -> 1 <- 3 <- 2 <- 4
def test_graph_dag_to_pdag_and4_12_ok():
    dag = ex_dag.and4_12()
    print("\n1 -> 2 <- 4, 3 -> 2 (star collider) DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_12(pdag)  # 2 - 3 - 1 - 2 - 4 PDAG


# 2 <- 1 <- 3 -> 2 <- 4
def test_graph_dag_to_pdag_and4_13_ok():
    dag = ex_dag.and4_13()
    print("\n2 <- 1 <- 3 -> 2 <- 4 DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_13(pdag)  # 2 <- 1 - 3 -> 2 <- 4 PDAG


# 2 <- 1 -> 3 <- 2 <- 4
def test_graph_dag_to_pdag_and4_14_ok():
    dag = ex_dag.and4_14()
    print("\n2 <- 1 -> 3 <- 2 <- 4 DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_14(pdag)  # 2 <- 1 -> 3 <- 2 <- 4 PDAG


# 1->2->4<-3->1 (square, 1 collider)
def test_graph_dag_to_pdag_and4_15_ok():
    dag = ex_dag.and4_15()
    print("\n1->2->4<-3->1 (square, 1 collider) DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_15(pdag)  # 2->4<-3, 2-1-3 (square, 1 collider) PDAG


# 2->4<-3, 2->1<-3 (square colliders)
def test_graph_dag_to_pdag_and4_16_ok():
    dag = ex_dag.and4_16()
    print("\n2->4<-3, 2->1<-3 (square colliders) DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_16(pdag)  # 2->4<-3, 2->1<-3 (square colliders) PDAG


# 4->3->1->2, 4->1, 4->2
def test_graph_dag_to_pdag_and4_17_ok():
    dag = ex_dag.and4_17()
    print("\n4->3->1->2, 4->1, 4->2 DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.and4_17(pdag)  # 4 - 3 - 1 - 2 - 4 - 1 (undirected square)


# 4 nodes, 6 edges
def test_graph_dag_to_pdag_complete4_ok():
    dag = ex_dag.complete4()
    print("\n4 nodes, 6 edges DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.complete4(pdag)  # complete skeleton


#   Standard BNs


# Cancer DAG
def test_graph_dag_to_pdag_cancer_ok():
    dag = ex_dag.cancer()
    print("\nCancer DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.cancer1(pdag)  # fully orientated Cancer PDAG


# Asia DAG
def test_graph_dag_to_pdag_asia_ok():
    dag = ex_dag.asia()
    print("\nAsia DAG:\n{}".format(dag))
    pdag = fromDAG(dag)
    print("\nextends PDAG:\n{}".format(pdag))
    ex_pdag.asia(pdag)  # fully orientated Cancer PDAG
