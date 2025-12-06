from abc import ABC, abstractmethod
from typing import Dict, Tuple

import numpy as np


class BNFit(ABC):
    """
    Minimal interface for Bayesian Network parameter estimation.

    This interface provides the essential methods required for fitting
    conditional probability tables (CPT) and linear Gaussian models
    in Bayesian Networks.
    """

    @abstractmethod
    def marginals(
        self, node: str, parents: Dict, values_reqd: bool = False
    ) -> Tuple:
        """Return marginal counts for a node and its parents.

        Args:
            node: Node for which marginals required.
            parents: Dictionary {node: parents} for non-orphan nodes.
            values_reqd: Whether parent and child values required.

        Returns:
            Tuple of counts, and optionally, values:

            - ndarray counts: 2D array, rows=child, cols=parents
            - int maxcol: Maximum number of parental values
            - tuple rowval: Child values for each row
            - tuple colval: Parent combo (dict) for each col

        Raises:
            TypeError: For bad argument types.
        """
        pass

    @abstractmethod
    def values(self, nodes: Tuple[str, ...]) -> np.ndarray:
        """Return the (float) values for specified nodes.

        Suitable for passing into e.g. linear regression fitting.

        Args:
            nodes: Nodes for which data required.

        Returns:
            Numpy array of values, each column for a node.

        Raises:
            TypeError: If bad argument type.
            ValueError: If bad argument value.
        """
        pass

    @property
    @abstractmethod
    def N(self) -> int:
        """Total sample size.

        Returns:
            Current sample size being used.
        """
        pass

    @N.setter
    @abstractmethod
    def N(self, value: int) -> None:
        """Set total sample size."""
        pass

    @property
    @abstractmethod
    def node_values(self) -> Dict[str, Dict]:
        """Node value counts for categorical variables.

        Returns:
            Values and their counts of categorical nodes in sample.
            Format: {node1: {val1: count1, val2: count2, ...}, ...}
        """
        pass

    @node_values.setter
    @abstractmethod
    def node_values(self, value: Dict[str, Dict]) -> None:
        """Set node value counts."""
        pass
