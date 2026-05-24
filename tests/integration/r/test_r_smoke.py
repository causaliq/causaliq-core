"""R integration smoke tests.

These tests require a working R installation with bnlearn installed.
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
from causaliq_core.r.session import run_r_script


# Test R is reachable via Rscript in this environment.
@pytest.mark.r_integration
def test_r_is_available():
    assert is_r_available()


# Test bnlearn R package is installed and loadable.
@pytest.mark.r_integration
def test_bnlearn_is_available():
    assert is_r_package_available("bnlearn")


# Test run_r_script executes a simple R expression via stdin.
@pytest.mark.r_integration
def test_run_r_script_returns_output():
    output = run_r_script('cat("hello from R\\n")')
    assert "hello from R" in output


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
