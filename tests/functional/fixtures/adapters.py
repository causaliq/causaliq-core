"""Shared test fixtures for functional tests."""

from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from causaliq_core.bn.bnfit import BNFit


class DataFrameAdapter(BNFit):
    """Adapter to make pandas DataFrame work with existing BN.fit interface"""

    def __init__(self, df):
        self.df = df
        self._N = len(df)
        # Convert string/object columns to categorical
        for col in df.columns:
            dtype_name = str(df[col].dtype)
            if dtype_name in ("object", "string", "str"):
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
                rowval = tuple(str(val) for val in crosstab.index)
                # Handle case where there's only one parent
                #  (columns are scalars, not tuples)
                if len(parent_list) == 1:
                    colval = tuple(
                        {parent_list[0]: str(col)} for col in crosstab.columns
                    )
                else:
                    colval = tuple(
                        dict(zip(parent_list, [str(v) for v in col]))
                        for col in crosstab.columns
                    )
                return crosstab.values, crosstab.shape[1], rowval, colval
            else:
                return crosstab.values, crosstab.shape[1]

    def values(self, nodes: Tuple[str, ...]) -> np.ndarray:
        """Return the (float) values for specified nodes."""
        return self.df[list(nodes)].values.astype(float)

    @property
    def N(self) -> int:
        """Return the number of samples."""
        return self._N

    @N.setter
    def N(self, value: int) -> None:
        """Set the number of samples."""
        self._N = value

    @property
    def node_values(self) -> Dict[str, Dict]:
        """Return node value counts for categorical variables."""
        return self._node_values

    @node_values.setter
    def node_values(self, value: Dict[str, Dict]) -> None:
        """Set node value counts."""
        self._node_values = value

    @property
    def nodes(self) -> Tuple[str, ...]:
        """Column names in the dataset."""
        return tuple(self.df.columns)

    @property
    def sample(self) -> Any:
        """Access to underlying data sample."""
        return self.df

    @property
    def node_types(self) -> Dict[str, str]:
        """Node type mapping for each variable."""
        return {col: str(self.df[col].dtype) for col in self.df.columns}

    def write(self, filename: str) -> None:
        """Write data to file - not implemented for test adapter."""
        raise NotImplementedError("write not implemented for test adapter")

    @property
    def dstype(self):
        """Return the dataset type."""
        # Check if any columns are categorical
        has_categorical = any(
            self.df[col].dtype.name == "category" for col in self.df.columns
        )
        return "categorical" if has_categorical else "continuous"
