# Test methods which analyse and update the parameters (probabilities) of
# a CPT

import gzip
from pathlib import Path

import pandas as pd

from causaliq_core.bn import CPT
from causaliq_core.bn.bnfit import BNFit
from causaliq_core.bn.io import read_bn

TESTDATA_DIR = Path("tests/data/functional/bn")


class DataFrameAdapter(BNFit):
    """Adapter to make pandas DataFrame work with existing CPT.fit interface"""

    def __init__(self, df):
        self.df = df
        self._N = len(df)
        # Convert categorical columns if dstype was categorical
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype("category")
        # Compute node_values for categorical columns
        self._node_values = {
            col: dict(df[col].value_counts())
            for col in df.columns
            if df[col].dtype.name == "category"
        }

    def marginals(self, node, parents, values_reqd=False):
        """Return marginal counts for a node and its parents."""
        if parents is None or len(parents) == 0:
            # Node has no parents - return simple value counts
            counts = self.df[node].value_counts().sort_index()
            if values_reqd:
                rowval = tuple(counts.index)
                colval = tuple()
                return counts.values.reshape(-1, 1), 1, rowval, colval
            else:
                return counts.values.reshape(-1, 1), 1
        else:
            # Node has parents - return cross-tabulation
            parent_list = (
                list(parents[node]) if node in parents else list(parents)
            )
            crosstab = pd.crosstab(
                self.df[node], [self.df[p] for p in parent_list]
            )

            if values_reqd:
                rowval = tuple(crosstab.index)
                colval = tuple(
                    dict(zip(parent_list, col)) for col in crosstab.columns
                )
                return crosstab.values, crosstab.shape[1], rowval, colval
            else:
                return crosstab.values, crosstab.shape[1]

    @property
    def N(self):
        return self._N

    @N.setter
    def N(self, value):
        self._N = value

    @property
    def nodes(self):
        return tuple(self.df.columns)

    def values(self, columns):
        """Return values for specified columns"""
        return self.df[list(columns)].values

    @property
    def node_values(self):
        return self._node_values

    @node_values.setter
    def node_values(self, value):
        self._node_values = value

    @property
    def sample(self):
        return self.df

    @property
    def node_types(self):
        return {col: str(self.df[col].dtype) for col in self.df.columns}

    def write(self, filename):
        """Write data to file - not implemented for test adapter."""
        raise NotImplementedError("write not implemented for test adapter")


def read_data(filepath, dstype=None, N=None):
    """Read CSV data using standard pandas"""
    # Convert Path to string for string operations
    filepath_str = str(filepath)

    # Handle gzipped files
    if filepath_str.endswith(".gz"):
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            # Read all data as strings initially to match original behavior
            df = pd.read_csv(f, nrows=N, dtype=str)
    else:
        # Read all data as strings initially to match original behavior
        df = pd.read_csv(filepath, nrows=N, dtype=str)

    # Convert to categorical if specified (preserving string values)
    if dstype == "categorical":
        for col in df.columns:
            df[col] = df[col].astype("category")

    return DataFrameAdapter(df)


def test_cpt_param_ratios_ab_1_ok():
    bn = read_bn(str(TESTDATA_DIR / "ab.dsc"))
    print("\nCPT for node A in A-->B is:\n{}".format(bn.cnds["A"]))
    print("\nCPT for node B in A-->B is:\n{}".format(bn.cnds["B"]))
    print("\nValue pairs for B are: {}".format(bn.cnds["B"].param_ratios()))


def test_cpt_param_ratios_ab2_1_ok():
    bn = read_bn(str(TESTDATA_DIR / "ab2.dsc"))
    print("\nCPT for node B in A-->B is:\n{}".format(bn.cnds["B"]))
    bn.cnds["A"].param_ratios()
    bn.cnds["B"].param_ratios()


def test_cpt_param_ratios_ab_cb_1_ok():
    bn = read_bn(str(TESTDATA_DIR / "ab_cb.dsc"))
    print("\nCPT for node A in A-->B<--C is:\n{}".format(bn.cnds["A"]))
    print("\nCPT for node B in A-->B<--C is:\n{}".format(bn.cnds["B"]))
    print("\nCPT for node C in A-->B<--C is:\n{}".format(bn.cnds["C"]))
    print("\nValue pairs for B are: {}".format(bn.cnds["B"].param_ratios()))


def check_fit(node, parents, data, expected=None, autocomplete=True):
    """
    Check fitted CPT is as expected.

    :param tuple args: arguments for CPT.fit()
    :param Data data: data to fit CPT from
    :param CPT expected: expected CPT
    :param bool autocomplete: whether CPT should have all parental combos
    """
    (_class, cptdata), est_pmfs = CPT.fit(node, parents, data, autocomplete)
    assert _class == CPT
    cpt = CPT(cptdata, est_pmfs)
    if expected is None:
        print(cptdata, est_pmfs)
        return
    print(
        "CPT.fit({}, {}) estimated {} PMFs and returned:\n{}\n".format(
            node, parents, cpt.estimated, cpt
        )
    )
    assert cpt == expected
    assert cpt.estimated == expected.estimated


def test_cpt_fit_ab3_1_ok():
    data = read_data(TESTDATA_DIR / "ab_3.csv", dstype="categorical")
    print(
        "\n\nFitting CPTs to {} rows of:\n{}\n".format(data.N, data.df.head())
    )

    check_fit("A", None, data, CPT({"1": 2 / 3, "0": 1 / 3}))

    check_fit("B", None, data, CPT({"1": 1 / 3, "0": 2 / 3}))

    check_fit(
        "A",
        ("B",),
        data,
        CPT(
            [
                ({"B": "0"}, {"0": 0.5, "1": 0.5}),
                ({"B": "1"}, {"0": 0.0, "1": 1.0}),
            ]
        ),
    )

    check_fit(
        "B",
        ("A",),
        data,
        CPT(
            [
                ({"A": "0"}, {"0": 1.0, "1": 0.0}),
                ({"A": "1"}, {"0": 0.5, "1": 0.5}),
            ]
        ),
    )


def test_cpt_fit_abc36_1_ok():
    data = read_data(TESTDATA_DIR / "abc_36.csv", dstype="categorical")
    print(
        "\n\nFitting CPTs to {} rows of:\n{}\n".format(data.N, data.df.tail())
    )

    check_fit("A", None, data, CPT({"1": 13 / 18, "0": 5 / 18}))

    check_fit(
        "A",
        ("B",),
        data,
        CPT(
            [
                ({"B": "0"}, {"0": 3 / 14, "1": 11 / 14}),
                ({"B": "1"}, {"0": 7 / 22, "1": 15 / 22}),
            ]
        ),
    )

    check_fit(
        "A",
        ("C",),
        data,
        CPT(
            [
                ({"C": "0"}, {"0": 4 / 16, "1": 12 / 16}),
                ({"C": "1"}, {"0": 6 / 20, "1": 14 / 20}),
            ]
        ),
    )

    check_fit(
        "A",
        ("B", "C"),
        data,
        CPT(
            [
                ({"B": "0", "C": "0"}, {"0": 1 / 6, "1": 5 / 6}),
                ({"B": "0", "C": "1"}, {"0": 2 / 8, "1": 6 / 8}),
                ({"B": "1", "C": "0"}, {"0": 3 / 10, "1": 7 / 10}),
                ({"B": "1", "C": "1"}, {"0": 4 / 12, "1": 8 / 12}),
            ]
        ),
    )

    check_fit("B", None, data, CPT({"1": 11 / 18, "0": 7 / 18}))

    check_fit(
        "B",
        ("A",),
        data,
        CPT(
            [
                ({"A": "0"}, {"0": 0.3, "1": 0.7}),
                ({"A": "1"}, {"0": 11 / 26, "1": 15 / 26}),
            ]
        ),
    )

    check_fit(
        "B",
        ("C",),
        data,
        CPT(
            [
                ({"C": "0"}, {"0": 6 / 16, "1": 10 / 16}),
                ({"C": "1"}, {"0": 8 / 20, "1": 12 / 20}),
            ]
        ),
    )

    check_fit(
        "B",
        ("A", "C"),
        data,
        CPT(
            [
                ({"A": "0", "C": "0"}, {"0": 1 / 4, "1": 3 / 4}),
                ({"A": "0", "C": "1"}, {"0": 2 / 6, "1": 4 / 6}),
                ({"A": "1", "C": "0"}, {"0": 5 / 12, "1": 7 / 12}),
                ({"A": "1", "C": "1"}, {"0": 6 / 14, "1": 8 / 14}),
            ]
        ),
    )


def test_cpt_fit_asia_1_ok():
    data = read_data(
        TESTDATA_DIR / "asia/asia.data.gz", dstype="categorical", N=100
    )
    print(
        "\n\nFitting CPTs to {} rows of:\n{}\n".format(data.N, data.df.tail())
    )

    # 2 parental combinations don't exist and will be estimated

    check_fit(
        "either",
        ("bronc", "lung", "asia"),
        data,
        CPT(
            [
                (
                    {"bronc": "no", "lung": "no", "asia": "no"},
                    {"no": 0.981132, "yes": 0.0188679},
                ),
                (
                    {"bronc": "no", "lung": "no", "asia": "yes"},
                    {"no": 1.0, "yes": 0.0},
                ),
                (
                    {"bronc": "no", "lung": "yes", "asia": "no"},
                    {"no": 0.0, "yes": 1.0},
                ),
                (
                    {"bronc": "yes", "lung": "no", "asia": "no"},
                    {"no": 1.0, "yes": 0.0},
                ),
                (
                    {"bronc": "yes", "lung": "no", "asia": "yes"},
                    {"no": 1.0, "yes": 0.0},
                ),
                (
                    {"bronc": "yes", "lung": "yes", "asia": "no"},
                    {"no": 0.0, "yes": 1.0},
                ),
                (
                    {"asia": "yes", "bronc": "no", "lung": "yes"},  # estimated
                    {"no": 0.92, "yes": 0.08},
                ),
                (
                    {"asia": "yes", "bronc": "yes", "lung": "yes"},  # estim.
                    {"no": 0.92, "yes": 0.08},
                ),
            ],
            2,
        ),
    )

    # don't estimate the 2 missing parental combinations

    check_fit(
        "either",
        ("bronc", "lung", "asia"),
        data,
        CPT(
            [
                (
                    {"bronc": "no", "lung": "no", "asia": "no"},
                    {"no": 0.981132, "yes": 0.0188679},
                ),
                (
                    {"bronc": "no", "lung": "no", "asia": "yes"},
                    {"no": 1.0, "yes": 0.0},
                ),
                (
                    {"bronc": "no", "lung": "yes", "asia": "no"},
                    {"no": 0.0, "yes": 1.0},
                ),
                (
                    {"bronc": "yes", "lung": "no", "asia": "no"},
                    {"no": 1.0, "yes": 0.0},
                ),
                (
                    {"bronc": "yes", "lung": "no", "asia": "yes"},
                    {"no": 1.0, "yes": 0.0},
                ),
                (
                    {"bronc": "yes", "lung": "yes", "asia": "no"},
                    {"no": 0.0, "yes": 1.0},
                ),
            ],
            0,
        ),
        False,
    )
