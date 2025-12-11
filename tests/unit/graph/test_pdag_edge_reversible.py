#   Check edge_reversible method of PDAG class.
#   Note that analysis/test/test_bn_analysis.py also tests this method.

import pytest

from tests.functional.fixtures import example_pdags as ex_pdag


# no args specified
def test_pdag_edge_reversible_type_error_1():
    pdag = ex_pdag.a()
    with pytest.raises(TypeError):
        pdag.edge_reversible()


# argument not a tuple
def test_pdag_edge_reversible_type_error_2():
    pdag = ex_pdag.a()
    with pytest.raises(TypeError):
        pdag.edge_reversible(27)
    with pytest.raises(TypeError):
        pdag.edge_reversible(["A", "B"])
    with pytest.raises(TypeError):
        pdag.edge_reversible(-1.9)
    with pytest.raises(TypeError):
        pdag.edge_reversible(True)


# tuple doesn't have two elems
def test_pdag_edge_reversible_type_error_3():
    pdag = ex_pdag.a()
    with pytest.raises(TypeError):
        pdag.edge_reversible(tuple(["A"]))
    with pytest.raises(TypeError):
        pdag.edge_reversible(("1",))
    with pytest.raises(TypeError):
        pdag.edge_reversible(("1", "2", "3"))


# tuple elements not strings
def test_pdag_edge_reversible_type_error_4():
    pdag = ex_pdag.a()
    with pytest.raises(TypeError):
        pdag.edge_reversible((1, 2))
    with pytest.raises(TypeError):
        pdag.edge_reversible(("1", 3))


# PDAG A, edge not present
def test_pdag_edge_reversible_value_a_ok():
    pdag = ex_pdag.a()
    assert not pdag.edge_reversible(("A", "A"))


# PDAG A->B
def test_pdag_edge_reversible_ab_ok():
    pdag = ex_pdag.ab()
    assert not pdag.edge_reversible(("A", "B"))
    assert not pdag.edge_reversible(("B", "A"))
    assert not pdag.edge_reversible(("A", "C"))


# PDAG A-B
def test_pdag_edge_reversible_ab3_ok():
    pdag = ex_pdag.ab3()
    assert pdag.edge_reversible(("A", "B"))
    assert pdag.edge_reversible(("B", "A"))
    assert not pdag.edge_reversible(("A", "A"))
    assert not pdag.edge_reversible(("A", "C"))


# PDAG A-B-C
def test_pdag_edge_reversible_abc4_ok():
    pdag = ex_pdag.abc4()
    assert pdag.edge_reversible(("A", "B"))
    assert pdag.edge_reversible(("B", "A"))
    assert pdag.edge_reversible(("B", "C"))
    assert pdag.edge_reversible(("C", "B"))
    assert not pdag.edge_reversible(("A", "C"))
    assert not pdag.edge_reversible(("C", "A"))


# PDAG A->B<-C
def test_pdag_edge_reversible_ab_cb_ok():
    pdag = ex_pdag.ab_cb()
    assert not pdag.edge_reversible(("A", "B"))
    assert not pdag.edge_reversible(("B", "A"))
    assert not pdag.edge_reversible(("B", "C"))
    assert not pdag.edge_reversible(("C", "B"))
    assert not pdag.edge_reversible(("A", "C"))
    assert not pdag.edge_reversible(("C", "A"))
