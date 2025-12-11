# Unit test Linear Gaussian Distribution

import numpy as np
import pytest
from pandas import DataFrame

from causaliq_core.bn.bnfit import BNFit
from causaliq_core.bn.dist.lingauss import LinGauss
from causaliq_core.utils.same import values_same


class DataFrameAdapter(BNFit):
    """Adapter to make DataFrame work with BNFit interface"""

    def __init__(self, df):
        self._df = df
        self.sample = df  # Legacy Pandas class has this attribute
        self._N = len(df)
        # Only compute node_values for categorical columns, not continuous
        self._node_values = {
            col: {val: count for val, count in df[col].value_counts().items()}
            for col in df.columns
            if df[col].dtype == "category"
        }

    def values(self, columns):
        # Check for node appearing as own parent (duplicate in columns)
        if len(columns) != len(set(columns)):
            raise ValueError("Node cannot be its own parent")

        # Check for invalid columns and convert KeyError to ValueError
        try:
            return self._df[list(columns)].values
        except KeyError as e:
            raise ValueError(f"Invalid column name: {e}")

    def marginals(self, nodes, parents):
        raise NotImplementedError("marginals not implemented for test adapter")

    @property
    def nodes(self):
        """Return the nodes in the dataset."""
        return tuple(self._df.columns)

    @property
    def sample(self):
        """Return the underlying DataFrame."""
        return self._df

    @sample.setter
    def sample(self, value):
        """Set the underlying DataFrame."""
        self._df = value

    @property
    def node_types(self):
        """Return the types of all nodes."""
        return {col: str(self._df[col].dtype) for col in self._df.columns}

    def write(self, filename):
        """Write data to file - not implemented for test adapter."""
        raise NotImplementedError("write not implemented for test adapter")

    @property
    def N(self):
        return self._N

    @N.setter
    def N(self, value):
        self._N = value

    @property
    def node_values(self):
        return self._node_values

    @node_values.setter
    def node_values(self, value):
        self._node_values = value


@pytest.fixture(scope="function")  # simple lg specification
def lg():
    return {"coeffs": {"A": 1.1, "B": -0.25}, "mean": 2.2, "sd": 0.34}


@pytest.fixture(scope="module")  # generate data used to test .fit()
def data():
    N = 10000000
    np.random.seed(42)
    t = 3.0 + 1.0 * np.random.randn(N)
    u = 1.0 + 3.0 * np.random.randn(N) - 4.0 * t
    v = 0.5 + 0.5 * np.random.randn(N) + 1.0 * t - 0.1 * u
    return DataFrameAdapter(DataFrame({"T": t, "U": u, "V": v}))


# Test the LinGauss() constructor


# no aruments
def test_lingauss_type_error_1():
    with pytest.raises(TypeError):
        LinGauss()


# argument is not a dictionary
def test_lingauss_type_error_2(lg):
    with pytest.raises(TypeError):
        LinGauss(12)
    with pytest.raises(TypeError):
        LinGauss(True)
    with pytest.raises(TypeError):
        LinGauss([lg])


# lg has missing/extra keys
def test_lingauss_type_error_3(lg):
    lg.update({"extra": 23.2})
    with pytest.raises(TypeError):
        LinGauss(lg)
    lg.pop("extra")
    lg.pop("sd")
    with pytest.raises(TypeError):
        LinGauss(lg)
    lg.update({"invalid": 2.0})
    with pytest.raises(TypeError):
        LinGauss(lg)


# lg values have incorrect types
def test_lingauss_type_error_4(lg):
    lg.update({"coeffs": 23.1})
    with pytest.raises(TypeError):
        LinGauss(lg)
    lg.update({"coeffs": {"A": 3.0}, "mean": 2})
    with pytest.raises(TypeError):
        LinGauss(lg)
    lg.update({"mean": -3.4, "sd": True})
    with pytest.raises(TypeError):
        LinGauss(lg)


# coeffs have wrong key types
def test_lingauss_type_error_5(lg):
    lg.update({"coeffs": {1: 2.5}})
    with pytest.raises(TypeError):
        LinGauss(lg)
    lg.update({"coeffs": {"good": 2.7, True: 1.0}})
    with pytest.raises(TypeError):
        LinGauss(lg)


# coeffs have wrong value types
def test_lingauss_type_error_6(lg):
    lg.update({"coeffs": {"ok": 2.5, "invalid": 3}})
    with pytest.raises(TypeError):
        LinGauss(lg)
    lg.update({"coeffs": {"ok": 2.5, "invalid": True}})
    with pytest.raises(TypeError):
        LinGauss(lg)
    lg.update({"coeffs": {"ok": 2.5, "invalid": (2.0,)}})
    with pytest.raises(TypeError):
        LinGauss(lg)
    lg.update({"coeffs": {"ok": 2.5, "invalid": True}})
    with pytest.raises(TypeError):
        LinGauss(lg)
    lg.update({"coeffs": {"ok": 2.5, "invalid": True}})
    with pytest.raises(TypeError):
        LinGauss(lg)


# SD is negative
def test_lingauss_value_error_1(lg):
    lg.update({"sd": -0.1})
    with pytest.raises(ValueError):
        LinGauss(lg)
    lg.update({"sd": -1.0e-20})
    with pytest.raises(ValueError):
        LinGauss(lg)


# lg fixture OK
def test_lingauss_lg_1_ok(lg):
    cnd = LinGauss(lg)
    assert isinstance(cnd, LinGauss)
    assert cnd.coeffs == {"A": 1.1, "B": -0.25}
    assert cnd.mean == 2.2
    assert cnd.sd == 0.34
    assert "{}".format(cnd) == "1.1*A-0.25*B+Normal(2.2,0.34)"
    print("\nLinGauss: {}".format(cnd))


# leading negative coefficient
def test_lingauss_lg_2_ok(lg):
    lg.update({"coeffs": {"A": -0.02, "B": -0.25}})
    cnd = LinGauss(lg)
    assert isinstance(cnd, LinGauss)
    assert cnd.coeffs == {"A": -0.02, "B": -0.25}
    assert cnd.mean == 2.2
    assert cnd.sd == 0.34
    assert "{}".format(cnd) == "-0.02*A-0.25*B+Normal(2.2,0.34)"
    print("\nLinGauss: {}".format(cnd))


# v small coeffs dropped in string
def test_lingauss_lg_3_ok(lg):
    lg.update({"coeffs": {"A": -1e-11, "B": -0.25}})
    cnd = LinGauss(lg)
    assert isinstance(cnd, LinGauss)
    assert cnd.coeffs == {"A": -1e-11, "B": -0.25}
    assert cnd.mean == 2.2
    assert cnd.sd == 0.34
    assert "{}".format(cnd) == "-0.25*B+Normal(2.2,0.34)"
    print("\nLinGauss: {}".format(cnd))


# rounding to 10 s.f.. string
def test_lingauss_lg_4_ok(lg):
    lg.update({"coeffs": {"A": 1.0123456789, "B": -0.00987654321}})
    cnd = LinGauss(lg)
    assert isinstance(cnd, LinGauss)
    assert cnd.coeffs == {"A": 1.0123456789, "B": -0.00987654321}
    assert cnd.mean == 2.2
    assert cnd.sd == 0.34
    assert "{}".format(cnd) == "1.012345679*A-0.00987654321*B+Normal(2.2,0.34)"
    print("\nLinGauss: {}".format(cnd))


# orphan node OK
def test_lingauss_lg_5_ok(lg):
    lg.update({"coeffs": {}})
    cnd = LinGauss(lg)
    assert isinstance(cnd, LinGauss)
    assert cnd.coeffs == {}
    assert cnd.mean == 2.2
    assert cnd.sd == 0.34
    assert "{}".format(cnd) == "Normal(2.2,0.34)"
    print("\nLinGauss: {}".format(cnd))


# Test equality


# LinGauss equals itself
def test_eq_1_ok(lg):
    lg = LinGauss(lg)
    assert lg == lg


# LinGauss equals identical LinGauss
def test_eq_2_ok(lg):
    lg1 = LinGauss(lg)
    lg2 = LinGauss(lg)
    assert id(lg1) != id(lg2)
    assert lg1 == lg2


# LinGauss equals very similar LinGauss
def test_eq_3_ok(lg):
    lg1 = LinGauss(lg)
    lg.update({"mean": 2.2000000001})
    lg2 = LinGauss(lg)
    assert id(lg1) != id(lg2)
    assert lg1 == lg2
    lg.update({"mean": 2.2, "sd": 0.33999999999})
    lg3 = LinGauss(lg)
    assert id(lg1) != id(lg3)
    assert lg1 == lg3
    lg.update({"coeffs": {"A": 1.1000000001, "B": -0.24999999996}})
    lg4 = LinGauss(lg)
    assert id(lg1) != id(lg4)
    assert lg1 == lg4


# Test inequality


# not equal to non LinGauss objects
def test_ne_ok_1(lg):
    lg = LinGauss(lg)
    assert lg != 1
    assert lg != {"mean": 0.0, "sd": 1.0, "coeffs": {}}
    assert lg is not None
    assert lg is not True
    assert lg is not False


# not equal if mean different
def test_ne_ok_2(lg):
    lg1 = LinGauss(lg)
    lg.update({"mean": 2.199999999})
    lg2 = LinGauss(lg)
    assert id(lg1) != id(lg2)
    assert lg1 != lg2


# not equal if sd different
def test_ne_ok_3(lg):
    lg1 = LinGauss(lg)
    lg.update({"sd": 0.3400000001})
    lg2 = LinGauss(lg)
    assert id(lg1) != id(lg2)
    assert lg1 != lg2


# not equal if coeff key different
def test_ne_ok_4(lg):
    lg1 = LinGauss(lg)
    lg.update({"coeffs": {"AA": 1.1, "B": -0.25}})
    lg2 = LinGauss(lg)
    assert id(lg1) != id(lg2)
    assert lg1 != lg2


# not equal if missing coeff
def test_ne_ok_5(lg):
    lg1 = LinGauss(lg)
    lg.update({"coeffs": {"B": -0.25}})
    lg2 = LinGauss(lg)
    assert id(lg1) != id(lg2)
    assert lg1 != lg2


# not equal if extra coeff
def test_ne_ok_6(lg):
    lg1 = LinGauss(lg)
    lg.update({"coeffs": {"A": 1.1, "B": -0.25, "C": 3.9}})
    lg2 = LinGauss(lg)
    assert id(lg1) != id(lg2)
    assert lg1 != lg2


# not equal if coeff value different
def test_ne_ok_7(lg):
    lg1 = LinGauss(lg)
    lg.update({"coeffs": {"A": 1.1, "B": -0.2499999999}})
    lg2 = LinGauss(lg)
    assert id(lg1) != id(lg2)
    assert lg1 != lg2


# Test Data fitting


# no parameters specified
def test_fit_type_error_1():
    with pytest.raises(TypeError):
        LinGauss.fit()


# node is not a string
def test_fit_type_error_2(data):
    with pytest.raises(TypeError):
        LinGauss.fit(None, None, data)
    with pytest.raises(TypeError):
        LinGauss.fit(12, None, data)
    with pytest.raises(TypeError):
        LinGauss.fit(["T"], None, data)


# parents is not None or tuple of strings
def test_fit_type_error_3(data):
    with pytest.raises(TypeError):
        LinGauss.fit("T", False, data)
    with pytest.raises(TypeError):
        LinGauss.fit("U", ["T"], data)
    with pytest.raises(TypeError):
        LinGauss.fit("U", "T", data)
    with pytest.raises(TypeError):
        LinGauss.fit("U", tuple(), data)
    with pytest.raises(TypeError):
        LinGauss.fit("U", (1, 2), data)


# data is not Data type
def test_fit_type_error_4(data):
    with pytest.raises(TypeError):
        LinGauss.fit("U", ("T",), True)
    with pytest.raises(TypeError):
        LinGauss.fit("U", ("T",), data.sample)


# node is one of parents
def test_fit_value_error_1(data):
    with pytest.raises(ValueError):
        LinGauss.fit("U", ("T", "U"), data)


# node or parent is not in data
def test_fit_value_error_2(data):
    with pytest.raises(ValueError):
        LinGauss.fit("invalid", ("T", "U"), data)
    with pytest.raises(ValueError):
        LinGauss.fit("T", ("invalid", "U"), data)


# Check fitted values for T (orphan) node
def test_fit_1_ok(data):
    lg, _ = LinGauss.fit("T", None, data)

    # t = 3.0 + 1.0 * np.random.randn(N)

    assert values_same(lg[1]["mean"], 3.00, sf=4)
    assert values_same(lg[1]["sd"], 1.00, sf=5)
    assert lg[1]["coeffs"] == {}
    print("\nT: mean: {:.4f}, s.d.: {:.4f}".format(lg[1]["mean"], lg[1]["sd"]))


# Check fitted values for U with parent T
def test_fit_2_ok(data):
    lg, _ = LinGauss.fit("U", ("T",), data)

    # u = 1.0 + 3.0 * np.random.randn(N) - 4.0 * t

    assert values_same(lg[1]["mean"], 1.000, sf=4)
    assert values_same(lg[1]["sd"], 3.000, sf=4)
    assert set(lg[1]["coeffs"]) == {"T"}
    assert values_same(lg[1]["coeffs"]["T"], -4.0, sf=4)
    print(
        "\nU: mean: {:.4f}, s.d.: {:.4f}, T: {:.4f}".format(
            lg[1]["mean"], lg[1]["sd"], lg[1]["coeffs"]["T"]
        )
    )


# Check fitted values for V with parents T & U
def test_fit_3_ok(data):
    lg, _ = LinGauss.fit("V", ("T", "U"), data)

    # v = 0.5 + 0.5 * np.random.randn(N) + 1.0 * t - 0.1 * u

    assert values_same(lg[1]["mean"], 0.50, sf=2)
    assert values_same(lg[1]["sd"], 0.500, sf=3)
    assert set(lg[1]["coeffs"]) == {"T", "U"}
    assert values_same(lg[1]["coeffs"]["T"], 1.0, sf=3)
    assert values_same(lg[1]["coeffs"]["U"], -0.1, sf=4)
    print(
        "\nU: mean: {:.4f}, s.d.: {:.4f}, T: {:.4f}, U: {:.4f}".format(
            lg[1]["mean"],
            lg[1]["sd"],
            lg[1]["coeffs"]["T"],
            lg[1]["coeffs"]["U"],
        )
    )


# test to_spec function including name mapping


# no arguments
def test_to_spec_type_error_1(lg):
    with pytest.raises(TypeError):
        LinGauss(lg).to_spec()


# name_map not a dictionary
def test_to_spec_type_error_2(lg):
    with pytest.raises(TypeError):
        LinGauss(lg).to_spec(False)
    with pytest.raises(TypeError):
        LinGauss(lg).to_spec(None)
    with pytest.raises(TypeError):
        LinGauss(lg).to_spec(1)
    with pytest.raises(TypeError):
        LinGauss(lg).to_spec(23.2)
    with pytest.raises(TypeError):
        LinGauss(lg).to_spec(["A"])


# name_map keys not strings
def test_to_spec_type_error_3(lg):
    with pytest.raises(TypeError):
        LinGauss(lg).to_spec({1: "A", "B": "S"})


# name_map values not strings
def test_to_spec_type_error_4(lg):
    with pytest.raises(TypeError):
        LinGauss(lg).to_spec({"A": "A", "B": 0.05})


# name_map doesn't include all coeff keys
def test_to_spec_value_error_1(lg):
    with pytest.raises(ValueError):
        LinGauss(lg).to_spec({"A": "X", "C": "Y"})


# names remaining the same
def test_to_spec_1_ok(lg):
    lg1 = LinGauss(lg)
    name_map = {n: n for n in lg1.coeffs}
    spec = lg1.to_spec(name_map)
    print("\n\nSpec is {}".format(spec))
    assert spec == {"coeffs": {"A": 1.1, "B": -0.25}, "mean": 2.2, "sd": 0.34}


# mapping names
def test_to_spec_2_ok(lg):
    lg1 = LinGauss(lg)
    name_map = {"A": "AA", "B": "BB"}
    spec = lg1.to_spec(name_map)
    print("\n\nSpec is {}".format(spec))
    assert spec == {
        "coeffs": {"AA": 1.1, "BB": -0.25},
        "mean": 2.2,
        "sd": 0.34,
    }


# parents method with empty coeffs
def test_lingauss_parents_empty():
    """Test parents method with empty coeffs returns empty list."""
    lg = LinGauss({"mean": 1.0, "sd": 0.5, "coeffs": {}})
    assert lg.parents() == []


# to_spec raises ValueError when key missing
def test_lingauss_to_spec_missing_key():
    """Test to_spec raises ValueError when coefficient key not in name_map."""
    lg = LinGauss({"mean": 1.0, "sd": 0.5, "coeffs": {"A": 0.5, "B": 0.3}})

    # Test with missing key in name_map
    with pytest.raises(ValueError, match="bad arg value"):
        lg.to_spec({"A": "A_new"})  # Missing 'B' in name_map


# cdist raises TypeError for coeff/parent mismatch
def test_lingauss_cdist_type_error():
    """Test cdist raises TypeError for coefficient/parent mismatch."""
    # Test case 1: has coeffs but parental_values is None
    lg = LinGauss({"mean": 0.0, "sd": 1.0, "coeffs": {"A": 0.5}})
    with pytest.raises(TypeError, match="coeffs/parent values mismatch"):
        lg.cdist(None)

    # Test case 2: no coeffs but parental_values provided
    lg = LinGauss({"mean": 0.0, "sd": 1.0, "coeffs": {}})
    with pytest.raises(TypeError, match="coeffs/parent values mismatch"):
        lg.cdist({"A": 1.0})

    # Test case 3: coeffs and parental_values keys don't match
    lg = LinGauss({"mean": 0.0, "sd": 1.0, "coeffs": {"A": 0.5}})
    with pytest.raises(TypeError, match="coeffs/parent values mismatch"):
        lg.cdist({"B": 1.0})


# random_value method with/without parents
def test_lingauss_random_value():
    """Test random_value method."""
    lg = LinGauss({"mean": 10.0, "sd": 2.0, "coeffs": {"A": 0.5}})

    # Test with parental values
    value = lg.random_value({"A": 2.0})
    assert isinstance(value, float)

    # Test with no parents
    lg_no_parents = LinGauss({"mean": 5.0, "sd": 1.0, "coeffs": {}})
    value = lg_no_parents.random_value(None)
    assert isinstance(value, float)


# validate_parents raises ValueError for mismatch
def test_lingauss_validate_parents_error():
    """Test validate_parents raises ValueError for parent mismatch."""
    lg = LinGauss({"mean": 0.0, "sd": 1.0, "coeffs": {"A": 0.5, "B": 0.3}})

    # Test case 1: node not in parents but has coeffs
    with pytest.raises(ValueError, match="parent mismatch"):
        lg.validate_parents("X", {}, {})

    # Test case 2: node in parents but coefficient keys don't match
    with pytest.raises(ValueError, match="parent mismatch"):
        lg.validate_parents("Y", {"Y": ["A", "C"]}, {})
