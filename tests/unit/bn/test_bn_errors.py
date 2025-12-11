import pytest

from causaliq_core.bn import BN, CPT, LinGauss
from tests.functional.fixtures import example_dags as dag


def test_bn_type_error_1_():  # bad argument types
    with pytest.raises(TypeError):
        BN()
    with pytest.raises(TypeError):
        BN(32)
    with pytest.raises(TypeError):
        BN("not", "right")
    with pytest.raises(TypeError):
        BN(dag.ab(), "not right")


def test_bn_type_error_2_():  # bad type within nodes
    with pytest.raises(TypeError):
        BN([1], [])


def test_bn_type_error_3_():  # bad type for cpts arg
    with pytest.raises(TypeError):
        BN(["A", "B"], [("A", "->", "B")], [])


def test_bn_type_error_4_():  # bad type within cpts values
    with pytest.raises(TypeError):
        BN(["A", "B"], [("A", "->", "B")], {"A": 3, "B": 4})


def test_bn_value_error_1_():  # nodes in DAG and cpts don't match
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "C": (
            CPT,
            [
                ({"A": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.ab(), cpts)


def test_bn_value_error_2_():  # cpts keys don't match DAG nodes
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "C": (
            CPT,
            [
                ({"A": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.ab(), cpts)


def test_bn_value_error_3_():  # cpt keys vary
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "B": (
            CPT,
            [({"A": "0"}, {"0": 0.2, "1": 0.8}), ({}, {"0": 0.7, "1": 0.3})],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.ab(), cpts)


def test_bn_value_error_4_():  # cpt pmf keys vary
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "B": (
            CPT,
            [
                ({"A": "0"}, {"0": 0.2, "2": 0.8}),
                ({"A": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.ab(), cpts)


def test_bn_value_error_5_():  # cpt pmf keys vary
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "B": (
            CPT,
            [({"A": "0"}, {"0": 0.2}), ({"A": "1"}, {"0": 0.7, "1": 0.3})],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.ab(), cpts)


def test_bn_value_error_6_():  # parents in CPT key don't match DAG
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "B": (
            CPT,
            [
                ({"C": "0"}, {"0": 0.2, "1": 0.8}),
                ({"C": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.ab(), cpts)


def test_bn_value_error_7_():  # parents in CPT key don't match DAG
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "B": (
            CPT,
            [
                ({"B": "0"}, {"0": 0.2, "1": 0.8}),
                ({"B": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.ab(), cpts)


def test_bn_value_error_8_():  # parents in CPT key don't match DAG
    cpts = {
        "B": (CPT, {"0": 0.25, "1": 0.75}),
        "A": (
            CPT,
            [
                ({"B": "0"}, {"0": 0.2, "1": 0.8}),
                ({"B": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.ab(), cpts)


def test_bn_value_error_9_():  # parents in CPT key don't match DAG
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "B": (
            CPT,
            [
                ({"A": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.a_b(), cpts)


def test_bn_value_error_10_():  # parents in CPT key don't match DAG
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "B": (
            CPT,
            [
                ({"B": "0"}, {"0": 0.2, "1": 0.8}),
                ({"B": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.a_b(), cpts)


def test_bn_value_error_11_():  # parents in CPT key don't match DAG
    cpts = {
        "B": (
            CPT,
            [
                ({"A": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
        "A": (
            CPT,
            [
                ({"B": "0"}, {"0": 0.2, "1": 0.8}),
                ({"B": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.ab(), cpts)


def test_bn_value_error_12_():  # parents in CPT key don't match DAG
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "B": (
            CPT,
            [
                ({"A": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
        "C": (CPT, {"0": 0.25, "1": 0.75}),
    }
    with pytest.raises(ValueError):
        BN(dag.abc(), cpts)


def test_bn_value_error_13_():  # parents in CPT key don't match DAG
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "B": (
            CPT,
            [
                ({"A": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
        "C": (
            CPT,
            [
                ({"A": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.abc(), cpts)


def test_bn_value_error_14_():  # parents in CPT key don't match DAG
    cpts = {
        "A": (
            CPT,
            [
                ({"B": "0"}, {"0": 0.2, "1": 0.8}),
                ({"B": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
        "B": (CPT, {"0": 0.25, "1": 0.75}),
        "C": (
            CPT,
            [
                ({"B": "0"}, {"0": 0.2, "1": 0.8}),
                ({"B": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.abc(), cpts)


def test_bn_value_error_15_():  # values in CPT key don't match parent values
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "B": (
            CPT,
            [
                ({"A": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": "1"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
        "C": (
            CPT,
            [
                ({"B": "2"}, {"0": 0.2, "1": 0.8}),
                ({"B": "3"}, {"0": 0.7, "1": 0.3}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.abc(), cpts)


def test_bn_value_error_16_():  # values in CPT key don't match parent values
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "B": (CPT, {"0": 0.40, "1": 0.60}),
        "C": (
            CPT,
            [
                ({"A": "0", "B": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": "0", "B": "2"}, {"0": 0.7, "1": 0.3}),
                ({"A": "1", "B": "0"}, {"0": 0.1, "1": 0.9}),
                ({"A": "1", "B": "2"}, {"0": 0.4, "1": 0.6}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.ac_bc(), cpts)


def test_bn_value_error_17_():  # values in CPT key don't match parent values
    cpts = {
        "A": (CPT, {"2": 0.25, "3": 0.75}),
        "B": (CPT, {"0": 0.40, "1": 0.60}),
        "C": (
            CPT,
            [
                ({"A": "0", "B": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": "0", "B": "1"}, {"0": 0.7, "1": 0.3}),
                ({"A": "1", "B": "0"}, {"0": 0.1, "1": 0.9}),
                ({"A": "1", "B": "1"}, {"0": 0.4, "1": 0.6}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.ac_bc(), cpts)


def test_bn_value_error_18_():  # not all parental combos in CPT
    cpts = {
        "A": (CPT, {"0": 0.25, "1": 0.75}),
        "B": (CPT, {"0": 0.40, "1": 0.60}),
        "C": (
            CPT,
            [
                ({"A": "0", "B": "0"}, {"0": 0.2, "1": 0.8}),
                ({"A": "0", "B": "1"}, {"0": 0.7, "1": 0.3}),
                ({"A": "1", "B": "1"}, {"0": 0.4, "1": 0.6}),
            ],
        ),
    }
    with pytest.raises(ValueError):
        BN(dag.ac_bc(), cpts)


def test_bn_value_error_19_():  # nodes in DAG and LinGauss don't match
    lgs = {
        "A": (LinGauss, {"coeffs": {}, "mean": 0.0, "sd": 1.0}),
        "B": (LinGauss, {"coeffs": {}, "mean": 0.0, "sd": 1.0}),
    }
    with pytest.raises(ValueError):
        BN(dag.ab(), lgs)


def test_bn_value_error_20_():  # nodes in DAG and LinGauss don't match
    lgs = {
        "A": (LinGauss, {"coeffs": {}, "mean": 0.0, "sd": 1.0}),
        "B": (LinGauss, {"coeffs": {"A": 1.0}, "mean": 0.0, "sd": 1.0}),
    }
    with pytest.raises(ValueError):
        BN(dag.a_b(), lgs)


def test_bn_value_error_21_():  # nodes in DAG and LinGauss don't match
    lgs = {
        "A": (LinGauss, {"coeffs": {}, "mean": 0.0, "sd": 1.0}),
        "B": (LinGauss, {"coeffs": {"C": 1.0}, "mean": 0.0, "sd": 1.0}),
    }
    with pytest.raises(ValueError):
        BN(dag.ab(), lgs)
