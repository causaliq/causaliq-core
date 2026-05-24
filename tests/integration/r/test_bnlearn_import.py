"""Integration tests for bnlearn_import via live R/bnlearn.

These tests require a working R installation with bnlearn
installed. Auto-skipped when R is unavailable (conftest.py).
Run explicitly with: pytest -m r_integration
"""

import pytest

from causaliq_core.bn import BN, LinGauss
from causaliq_core.r.bnlearn import bnlearn_import
from causaliq_core.r.session import run_r_script


def _create_rda(script_lines: list, rda_path: str) -> None:
    """Run R to fit and save a bn.fit object to an .rda file.

    Args:
        script_lines: R code lines that assign a bn.fit to 'bn'.
        rda_path: Absolute path where the .rda file is written.
    """
    r_path = rda_path.replace("\\", "/")
    run_r_script(
        "\n".join(script_lines + [f'save(bn, file="{r_path}")']) + "\n"
    )


# Test importing a single-node LinGauss BN returns a BN instance.
@pytest.mark.r_integration
def test_bnlearn_import_single_node_bn(tmp_path):
    rda = str(tmp_path / "single.rda")
    _create_rda(
        [
            "library(bnlearn)",
            "set.seed(42)",
            "data <- data.frame(A = rnorm(100, mean=2.0, sd=1.0))",
            'net <- model2network("[A]")',
            "bn <- bn.fit(net, data)",
        ],
        rda,
    )
    result = bnlearn_import(rda)
    assert isinstance(result, BN)
    assert result.dag.nodes == ["A"]
    assert isinstance(result.cnds["A"], LinGauss)


# Test importing a two-node LinGauss BN preserves the A->B edge.
@pytest.mark.r_integration
def test_bnlearn_import_two_node_bn_preserves_structure(tmp_path):
    rda = str(tmp_path / "ab.rda")
    _create_rda(
        [
            "library(bnlearn)",
            "set.seed(42)",
            "n <- 200",
            "A <- rnorm(n, mean=2.0, sd=1.0)",
            "B <- 0.5 + 1.5 * A + rnorm(n, sd=0.5)",
            "data <- data.frame(A=A, B=B)",
            'net <- model2network("[A][B|A]")',
            "bn <- bn.fit(net, data)",
        ],
        rda,
    )
    result = bnlearn_import(rda)
    assert isinstance(result, BN)
    assert sorted(result.dag.nodes) == ["A", "B"]
    assert ("A", "B") in result.dag.edges
    assert isinstance(result.cnds["A"], LinGauss)
    assert isinstance(result.cnds["B"], LinGauss)


# Test imported BN has plausible coefficient for the A->B edge.
@pytest.mark.r_integration
def test_bnlearn_import_coefficient_is_plausible(tmp_path):
    # True coefficient is 1.5; with 200 samples the MLE should be close.
    rda = str(tmp_path / "coef.rda")
    _create_rda(
        [
            "library(bnlearn)",
            "set.seed(1)",
            "n <- 500",
            "A <- rnorm(n, mean=0.0, sd=1.0)",
            "B <- 1.5 * A + rnorm(n, sd=0.2)",
            "data <- data.frame(A=A, B=B)",
            'net <- model2network("[A][B|A]")',
            "bn <- bn.fit(net, data)",
        ],
        rda,
    )
    result = bnlearn_import(rda)
    coeff_a = result.cnds["B"].coeffs["A"]
    assert abs(coeff_a - 1.5) < 0.2
