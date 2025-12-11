from pathlib import Path

import pandas as pd
import pytest

from causaliq_core.bn import BN, CPT, read_bn, write_bn
from causaliq_core.utils import values_same
from tests.functional.fixtures import example_bns as bn
from tests.functional.fixtures import example_dags as dag
from tests.functional.fixtures.adapters import DataFrameAdapter

TESTDATA_DIR = Path("tests/data/functional/bn")


@pytest.fixture(scope="module")  # simple Data object
def data():
    df = pd.read_csv(TESTDATA_DIR / "ab_3.csv", dtype="category")
    return DataFrameAdapter(df)


# no arguments
def test_bn_fit_type_error_1():
    with pytest.raises(TypeError):
        BN.fit()


# invalid DAG argument
def test_bn_fit_type_error_2(data):
    with pytest.raises(TypeError):
        BN.fit(1, data)
    with pytest.raises(TypeError):
        BN.fit([dag.ab()], data)
    with pytest.raises(TypeError):
        BN.fit(["A", "B"], data)


# column mismatch
def test_bn_fit_value_error_1(data):
    with pytest.raises(ValueError):
        BN.fit(dag.a(), data)


# Test error when variable has only one value
def test_bn_fit_value_error_2():
    # Create data where a variable has only one value
    df = pd.DataFrame(
        {
            "A": ["0", "0", "0", "0"],  # Only one value
            "B": ["0", "1", "0", "1"],  # Multiple values
        },
        dtype="category",
    )
    data = DataFrameAdapter(df)

    with pytest.raises(ValueError, match="Some variables have only one value"):
        BN.fit(dag.ab(), data)


# Test creating an empty BN with no nodes or edges
def test_bn_empty_ok():
    bn = BN(dag.empty(), {})
    assert isinstance(bn, BN)


# Create categorical BNs with constructor


# A
def test_bn_a_1_ok():
    bn.a(bn.a())


# Test creating categorical BN with A->B structure
def test_bn_ab_1_ok():
    bn.ab(bn.ab())


# Create continuous BNs with constructor


# X
def test_bn_x_1_ok():
    bn.x(bn.x())


# X --> Y
def test_bn_xy_1_ok():
    bn.xy(bn.xy())


# X   Y
def test_bn_x_y_1_ok():
    bn.x_y(bn.x_y())


# X --> Y --> Z
def test_bn_xyz_1_ok():
    bn.xyz(bn.xyz())


# X --> Y <-- Z
def test_bn_xy_zy_1_ok():
    bn.xy_zy(bn.xy_zy())


# Check fitting BN to categorical data


# Test fitting BN to categorical data with ab_3 dataset
def test_bn_fit_ab_3_ok():
    df = pd.read_csv(TESTDATA_DIR / "ab_3.csv", dtype="category")
    data = DataFrameAdapter(df)
    bn = BN.fit(dag.ab(), data)
    dag.ab(bn.dag)  # check DAG in BN is as expected
    assert bn.cnds["A"] == CPT({"1": 0.666666667, "0": 0.333333333})
    assert bn.cnds["B"] == CPT(
        [
            ({"A": "0"}, {"0": 1.0, "1": 0.0}),
            ({"A": "1"}, {"0": 0.5, "1": 0.5}),
        ]
    )
    assert bn.free_params == 3
    assert bn.estimated_pmfs == {}


# Test fitting BN to categorical data with abc_4 dataset
def test_bn_fit_ac_bc_4_ok():
    df = pd.read_csv(TESTDATA_DIR / "abc_4.csv", dtype="category")
    data = DataFrameAdapter(df)
    bn = BN.fit(dag.ac_bc(), data)
    dag.ac_bc(bn.dag)  # check DAG in BN is as expected
    assert bn.cnds["A"] == CPT({"1": 0.75, "0": 0.25})
    assert bn.cnds["B"] == CPT({"1": 0.75, "0": 0.25})
    assert bn.cnds["C"] == CPT(
        [
            ({"A": "0", "B": "0"}, {"0": 0.75, "1": 0.25}),
            ({"A": "0", "B": "1"}, {"0": 1.0, "1": 0.0}),
            ({"A": "1", "B": "0"}, {"0": 1.0, "1": 0.0}),
            ({"A": "1", "B": "1"}, {"0": 0.5, "1": 0.5}),
        ]
    )
    assert bn.free_params == 6
    assert bn.estimated_pmfs == {"C": 1}


# Test fitting BN to categorical data with abc_5 dataset
def test_bn_fit_ac_bc_5_ok():
    df = pd.read_csv(TESTDATA_DIR / "abc_5.csv", dtype="category")
    data = DataFrameAdapter(df)
    bn = BN.fit(dag.ac_bc(), data)
    dag.ac_bc(bn.dag)  # check DAG in BN is as expected
    assert bn.cnds["A"] == CPT({"1": 0.6, "0": 0.4})
    assert bn.cnds["B"] == CPT({"1": 0.6, "0": 0.4})
    assert bn.cnds["C"] == CPT(
        [
            ({"A": "0", "B": "0"}, {"0": 1.0, "1": 0.0}),
            ({"A": "0", "B": "1"}, {"0": 1.0, "1": 0.0}),
            ({"A": "1", "B": "0"}, {"0": 1.0, "1": 0.0}),
            ({"A": "1", "B": "1"}, {"0": 0.5, "1": 0.5}),
        ]
    )
    assert bn.free_params == 6
    assert bn.estimated_pmfs == {}


# Check fitting BN to Gaussian data


# X --> Y, 10K
def test_bn_fit_xy_1_ok():

    # X = Normal(2.0,1.0)
    # Y = 1.5*X+Normal(0.5,0.5)

    bn = read_bn(str(TESTDATA_DIR / "xy.xdsl"))
    df = bn.generate_cases(10000)
    data = DataFrameAdapter(df)

    bn = BN.fit(bn.dag, data)

    assert values_same(bn.cnds["X"].mean, 2.000, sf=4)
    assert values_same(bn.cnds["X"].sd, 1.00, sf=2)
    assert bn.cnds["X"].coeffs == {}

    assert values_same(bn.cnds["Y"].mean, 0.5, sf=1)
    assert values_same(bn.cnds["Y"].sd, 0.50, sf=2)
    assert set(bn.cnds["Y"].coeffs) == {"X"}
    assert values_same(bn.cnds["Y"].coeffs["X"], 1.50, sf=3)


# X --> Y --> Z, 10K
def test_bn_fit_xyz_1_ok():

    # X = Normal(0.0,1.0)
    # Y = 1.5*X+Normal(0.5,0.5)
    # Z = -2.0*Y+Normal(-2.0,0.2)

    bn = read_bn(str(TESTDATA_DIR / "xyz.xdsl"))
    df = bn.generate_cases(10000)
    data = DataFrameAdapter(df)

    bn = BN.fit(bn.dag, data)
    print("\nX = {}".format(bn.cnds["X"]))
    print("Y = {}".format(bn.cnds["Y"]))
    print("Z = {}".format(bn.cnds["Z"]))

    assert round(bn.cnds["X"].mean, 3) == 0.000
    assert values_same(bn.cnds["X"].sd, 1.00, sf=2)
    assert bn.cnds["X"].coeffs == {}

    assert values_same(bn.cnds["Y"].mean, 0.5, sf=2)
    assert values_same(bn.cnds["Y"].sd, 0.50, sf=2)
    assert set(bn.cnds["Y"].coeffs) == {"X"}
    assert values_same(bn.cnds["Y"].coeffs["X"], 1.50, sf=2)

    assert values_same(bn.cnds["Z"].mean, -2.00, sf=3)
    assert values_same(bn.cnds["Z"].sd, 0.200, sf=3)
    assert set(bn.cnds["Z"].coeffs) == {"Y"}
    assert values_same(bn.cnds["Z"].coeffs["Y"], -2.000, sf=4)


# X --> Y --> Z, 100K
def test_bn_fit_xy_zy_1_ok():

    # X = Normal(0.0, 1.0)
    # Y = 1.5*X - 2.2*Z + Normal(0.5, 0.5)
    # Z = Normal(-2.0, 0.2)

    bn = read_bn(str(TESTDATA_DIR / "xy_zy.xdsl"))
    df = bn.generate_cases(100000)
    data = DataFrameAdapter(df)

    bn = BN.fit(bn.dag, data)
    print("\nX = {}".format(bn.cnds["X"]))
    print("Y = {}".format(bn.cnds["Y"]))
    print("Z = {}".format(bn.cnds["Z"]))

    assert round(bn.cnds["X"].mean, 2) == 0.00
    assert values_same(bn.cnds["X"].sd, 1.00, sf=2)
    assert bn.cnds["X"].coeffs == {}

    assert values_same(bn.cnds["Y"].mean, 0.5, sf=1)
    assert values_same(bn.cnds["Y"].sd, 0.50, sf=2)
    assert set(bn.cnds["Y"].coeffs) == {"X", "Z"}
    assert values_same(bn.cnds["Y"].coeffs["X"], 1.50, sf=3)
    assert values_same(bn.cnds["Y"].coeffs["Z"], -2.2, sf=2)

    assert values_same(bn.cnds["Z"].mean, -2.000, sf=4)
    assert values_same(bn.cnds["Z"].sd, 0.200, sf=3)
    assert bn.cnds["Z"].coeffs == {}


# Fitting sachs to real cont data
def test_bn_fit_sachs_c_ok():

    bn = read_bn(str(TESTDATA_DIR / "sachs.dsc"))
    print(bn.dag)
    df = pd.read_csv(TESTDATA_DIR / "sachs_2005_cont.data.gz")
    data = DataFrameAdapter(df)
    print()
    print(data.df)
    print()

    fitted = BN.fit(bn.dag, data)
    print("\nLearnt functions are:\n")
    for node, cnd in fitted.cnds.items():
        print("{}: {}".format(node, cnd))

    # fitted.write(EXPTS_DIR + '/bn/xdsl/sachs_c.xdsl')

    read_bn(str(TESTDATA_DIR / "sachs_c.xdsl"))
    # assert ref == fitted  # but - fitted params will differ from reference


# Fitting covid to real cont data
def test_bn_fit_covid_c_ok():

    bn = read_bn(str(TESTDATA_DIR / "covid.dsc"))
    print(bn.dag)
    df = pd.read_csv(TESTDATA_DIR / "covid_cont.data.gz")
    data = DataFrameAdapter(df)
    print()
    print(data.df)
    print()

    fitted = BN.fit(bn.dag, data)
    print("\nLearnt functions are:\n")
    for node, cnd in fitted.cnds.items():
        print("{}: {}".format(node, cnd))

    write_bn(fitted, str(TESTDATA_DIR / "covid_c.xdsl"))

    # ref = read_bn(EXPTS_DIR + '/bn/xdsl/covid_c.xdsl')
    # assert ref == fitted


# Test BN __str__ method for cache stats
def test_bn_cache_str():
    # Test that BN cached_marginals object has __str__ method
    bn_test = bn.ab()
    cache_str = str(bn_test.cached_marginals)

    # Should return string representation of cache stats
    assert isinstance(cache_str, str)
    # Should contain some cache statistics
    assert "get" in cache_str or "put" in cache_str
