# Test PDAG.is_cpdag() method

import pytest

from causaliq_core.graph import is_cpdag
from tests.functional.fixtures import example_dags as dag
from tests.functional.fixtures import example_pdags as pdag


# Test empty graph
def test_pdag_is_cpdag_empty_ok():
    assert is_cpdag(pdag.empty()) is True


# Test single node DAG
def test_pdag_is_cpdag_a_ok():
    assert is_cpdag(pdag.a()) is True


# Test A -> B chain
def test_pdag_is_cpdag_ab_ok():
    assert is_cpdag(pdag.ab()) is False


# Test A -> B chain
def test_pdag_is_cpdag_ab_2_ok():
    assert is_cpdag(pdag.ab_2()) is False


# Test B -> A chain
def test_pdag_is_cpdag_ba_ok():
    assert is_cpdag(pdag.ba()) is False


# Test A, B unconnected
def test_pdag_is_cpdag_a_b_ok():
    assert is_cpdag(pdag.a_b()) is True


# Test A - B PDAG
def test_pdag_is_cpdag_ab3_ok():
    assert is_cpdag(pdag.ab3()) is True


# Test A, B, C unconnected
def test_pdag_is_cpdag_a_b_c_ok():
    assert is_cpdag(pdag.a_b_c()) is True


# Test A -> C, B
def test_pdag_is_cpdag_ac_b_ok():
    assert is_cpdag(pdag.ac_b()) is False


# Test A - C, B
def test_pdag_is_cpdag_ac_b2_ok():
    assert is_cpdag(pdag.ac_b2()) is True


# Test A -> B -> C
def test_pdag_is_cpdag_abc_ok():
    assert is_cpdag(pdag.abc()) is False


# Test A -> B -> C
def test_pdag_is_cpdag_abc2_ok():
    assert is_cpdag(pdag.abc2()) is False


# Test A - B -> C
def test_pdag_is_cpdag_abc3_ok():
    assert is_cpdag(pdag.abc3()) is False


# Test A - B - C
def test_pdag_is_cpdag_abc4_ok():
    assert is_cpdag(pdag.abc4()) is True


# Test A -> B - C
def test_pdag_is_cpdag_abc5_ok():
    assert is_cpdag(pdag.abc5()) is False


# Test C - A - B
def test_pdag_is_cpdag_abc6_ok():
    assert is_cpdag(pdag.abc6()) is True


# Test B <- A -> C - common cause
def test_pdag_is_cpdag_ab_ac_ok():
    assert is_cpdag(pdag.ab_ac()) is False


# Test A <- B -> C - common cause
def test_pdag_is_cpdag_ba_bc_ok():
    assert is_cpdag(pdag.ba_bc()) is False


# Test A -> C <- B - common effect
def test_pdag_is_cpdag_ac_bc_ok():
    assert is_cpdag(pdag.ac_bc()) is True


# Test A -> B <- C - common effect
def test_pdag_is_cpdag_ab_cb_ok():
    assert is_cpdag(pdag.ab_cb()) is True


# Test A -> B -> C <- A
def test_pdag_is_cpdag_abc_acyclic_ok():
    assert is_cpdag(pdag.abc_acyclic()) is False


# Test A -> B -> C - A
def test_pdag_is_cpdag_abc_acyclic2_ok():
    assert is_cpdag(pdag.abc_acyclic2()) is False


# Test A -- B -- C, A --> C
def test_pdag_is_cpdag_abc_acyclic3_ok():
    assert is_cpdag(pdag.abc_acyclic3()) is False


# Test A -- B -- C -- A
def test_pdag_is_cpdag_abc_acyclic4_ok():
    assert is_cpdag(pdag.abc_acyclic4()) is True


# Test 5-node CANCER DAG as a PDAG
def test_pdag_is_cpdag_cancer1_OK():
    assert is_cpdag(pdag.cancer1()) is True


# Test 5-node CANCER PDAG with 2 undir. edges
def test_pdag_is_cpdag_cancer2_OK():
    assert is_cpdag(pdag.cancer2()) is False


# Test 5-node CANCER skeleton PDAG
def test_pdag_is_cpdag_cancer3_OK():
    assert is_cpdag(pdag.cancer3()) is True


# Test Asia PDAG
def test_pdag_is_cpdag_asia1_OK():
    assert is_cpdag(pdag.asia()) is True


# Test Asia DAG
def test_pdag_is_cpdag_asia2_OK():
    assert is_cpdag(dag.asia()) is False


# Exemplar 4 node PDAGs from Andersson et al., 1995


# Test 1  2  3  4 DAG
def test_pdag_is_cpdag_and4_1a_OK():
    assert is_cpdag(dag.and4_1()) is True


# Test 1  2  3  4 PDAG
def test_pdag_is_cpdag_and4_1b_OK():
    assert is_cpdag(pdag.and4_1()) is True


# Test 1 -> 2  3  4 DAG
def test_pdag_is_cpdag_and4_2a_OK():
    assert is_cpdag(dag.and4_2()) is False


# Test 1 - 2  3  4 PDAG
def test_pdag_is_cpdag_and4_2b_OK():
    assert is_cpdag(pdag.and4_2()) is True


# Test 1 -> 2  3 -> 4 DAG
def test_pdag_is_cpdag_and4_3a_OK():
    assert is_cpdag(dag.and4_3()) is False


# Test 1 - 2  3 - 4 PDAG
def test_pdag_is_cpdag_and4_3b_OK():
    assert is_cpdag(pdag.and4_3()) is True


# Test 1 <- 2 <- 3  4 PDAG
def test_pdag_is_cpdag_and4_4a_OK():
    assert is_cpdag(dag.and4_4()) is False


# Test 1 - 2 - 3  4 PDAG
def test_pdag_is_cpdag_and4_4b_OK():
    assert is_cpdag(pdag.and4_4()) is True


# Test 1 -> 2 <- 3  4 DAG
def test_pdag_is_cpdag_and4_5a_OK():
    assert is_cpdag(dag.and4_5()) is True


# Test 1 -> 2 <- 3  4 PDAG
def test_pdag_is_cpdag_and4_5b_OK():
    assert is_cpdag(pdag.and4_5()) is True


# Test 1 <- 2 <- 3 -> 1  4 DAG
def test_pdag_is_cpdag_and4_6a_OK():
    assert is_cpdag(dag.and4_6()) is False


# Test 1 - 2 - 3 - 1  4 PDAG
def test_pdag_is_cpdag_and4_6b_OK():
    assert is_cpdag(pdag.and4_6()) is True


# Test 1 <- 2 <- 3 <- 4 DAG
def test_pdag_is_cpdag_and4_7a_OK():
    assert is_cpdag(dag.and4_7()) is False


# Test 1 - 2 - 3 - 4 PDAG
def test_pdag_is_cpdag_and4_7b_OK():
    assert is_cpdag(pdag.and4_7()) is True


# Test 1 -> 2 <- 3 <- 4 DAG
def test_pdag_is_cpdag_and4_8a_OK():
    assert is_cpdag(dag.and4_8()) is False


# Test 1 -> 2 <- 3 - 4 PDAG
def test_pdag_is_cpdag_and4_8b_OK():
    assert is_cpdag(pdag.and4_8()) is True


# Test 3 <- 2 -> 1, 2 <- 4 DAG
def test_pdag_is_cpdag_and4_9a_OK():
    assert is_cpdag(dag.and4_9()) is False


# Test 3 - 2 - 1, 2 - 4 (undir. star) PDAG
def test_pdag_is_cpdag_and4_9b_OK():
    assert is_cpdag(pdag.and4_9()) is True


# Test 1 -> 2 -> 4, 3 -> 2 DAG
def test_pdag_is_cpdag_and4_10a_OK():
    assert is_cpdag(dag.and4_10()) is True


# Test 1 -> 2 -> 4, 3 -> 2 PDAG
def test_pdag_is_cpdag_and4_10b_OK():
    assert is_cpdag(pdag.and4_10()) is True


# Test 1 -> 2 <- 4, 3 -> 2 (star coll) DAG
def test_pdag_is_cpdag_and4_11a_OK():
    assert is_cpdag(dag.and4_11()) is True


# Test 1 -> 2 <- 4, 3 -> 2 (star coll) PDAG
def test_pdag_is_cpdag_and4_11b_OK():
    assert is_cpdag(pdag.and4_11()) is True


# Test 2 -> 3 -> 1 <- 2 <- 4 DAG
def test_pdag_is_cpdag_and4_12a_OK():
    assert is_cpdag(dag.and4_12()) is False


# Test 2 - 3 - 1 - 2 - 4 PDAG
def test_pdag_is_cpdag_and4_12b_OK():
    assert is_cpdag(pdag.and4_12()) is True


# Test 2 <- 1 <- 3 -> 2 <- 4 DAG
def test_pdag_is_cpdag_and4_13a_OK():
    assert is_cpdag(dag.and4_13()) is False


# Test 2 <- 1 - 3 -> 2 <- 4 PDAG
def test_pdag_is_cpdag_and4_13b_OK():
    assert is_cpdag(pdag.and4_13()) is True


# Test 2 <- 1 -> 3 <- 2 <- 4 DAG
def test_pdag_is_cpdag_and4_14a_OK():
    assert is_cpdag(dag.and4_14()) is True


# Test 2 <- 1 -> 3 <- 2 <- 4 PDAG
def test_pdag_is_cpdag_and4_14b_OK():
    assert is_cpdag(pdag.and4_14()) is True


# Test 2->4<-3, 2<-1->3 (square, 1 coll) DAG
def test_pdag_is_cpdag_and4_15a_OK():
    assert is_cpdag(dag.and4_15()) is False


# Test 2->4<-3, 2-1-3 (square, 1 coll) PDAG
def test_pdag_is_cpdag_and4_15b_OK():
    assert is_cpdag(pdag.and4_15()) is True


# Test 2->4<-3, 2->1<-3 (square colls) DAG
def test_pdag_is_cpdag_and4_16a_OK():
    assert is_cpdag(dag.and4_16()) is True


# Test 2->4<-3, 2->1<-3 (square colls) PDAG
def test_pdag_is_cpdag_and4_16b_OK():
    assert is_cpdag(pdag.and4_16()) is True


# Test 1<-4->2<-1<-3<-1 (0 col sq + diag) DAG
def test_pdag_is_cpdag_and4_17a_OK():
    assert is_cpdag(dag.and4_17()) is False


# Test 1-4-2-1-3<-1 (sq + diag undir) PDAG
def test_pdag_is_cpdag_and4_17b_OK():
    assert is_cpdag(pdag.and4_17()) is True


# Test complete DAG
def test_pdag_is_cpdag_complete4a_OK():
    assert is_cpdag(dag.complete4()) is False


# Test complete undir PDAG
def test_pdag_is_cpdag_complete4b_OK():
    assert is_cpdag(pdag.complete4()) is True


# Test 1-2-3-4-1 (unextendable square)
def test_pdag_is_cpdag_value_error_1():
    with pytest.raises(ValueError):
        is_cpdag(pdag.and4_inv1())
