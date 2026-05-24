"""R integration smoke tests.

These tests require a working R installation with bnlearn and rpy2.
They are auto-skipped when R is not available (see tests/conftest.py).
Run explicitly with: pytest -m r_integration
"""

import pytest

from causaliq_core.graph import PDAG
from causaliq_core.r.availability import (
    is_r_available,
    is_r_package_available,
)
from causaliq_core.r.bnlearn import bnlearn_compare, bnlearn_cpdag
from causaliq_core.r.session import get_robjects, import_r_package


# Test R is reachable via rpy2 in this environment.
@pytest.mark.r_integration
def test_r_is_available():
    assert is_r_available()


# Test bnlearn R package is installed and loadable.
@pytest.mark.r_integration
def test_bnlearn_is_available():
    assert is_r_package_available("bnlearn")


# Test get_robjects returns the rpy2 robjects module.
@pytest.mark.r_integration
def test_get_robjects_returns_module():
    ro = get_robjects()
    assert ro is not None


# Test import_r_package returns the bnlearn package object.
@pytest.mark.r_integration
def test_import_bnlearn_returns_package():
    bnl = import_r_package("bnlearn")
    assert bnl is not None


# Test bnlearn can construct a simple network in R.
@pytest.mark.r_integration
def test_bnlearn_creates_network():
    bnl = import_r_package("bnlearn")
    net = bnl.model2network("[A][B|A][C|B]")
    assert net is not None


# Test bnlearn_cpdag returns a PDAG for a simple DAG.
@pytest.mark.r_integration
def test_bnlearn_cpdag_returns_pdag():
    pdag = PDAG(["A", "B", "C"], [("A", "->", "B"), ("B", "->", "C")])
    result = bnlearn_cpdag(pdag)
    assert isinstance(result, PDAG)
    assert sorted(result.nodes) == ["A", "B", "C"]


# Test bnlearn_compare returns expected metric keys.
@pytest.mark.r_integration
def test_bnlearn_compare_returns_metrics():
    pdag = PDAG(["A", "B"], [("A", "->", "B")])
    ref = PDAG(["A", "B"], [("A", "->", "B")])
    metrics = bnlearn_compare(pdag, ref)
    assert set(metrics.keys()) == {"tp", "fp", "fn", "shd"}
