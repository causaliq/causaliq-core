from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

import numpy as np


class BNFit(ABC):
    """
    Interface for Bayesian Network parameter estimation and data access.

    This interface provides the essential methods required for fitting
    conditional probability tables (CPT) and linear Gaussian models
    in Bayesian Networks, as well as data access methods for the BN class.

    Implementing classes should provide:
    - A constructor that accepts df=DataFrame parameter for BN compatibility
    - All abstract methods defined below
    - Properties for data access (.nodes, .sample, .node_types)
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

    @property
    @abstractmethod
    def nodes(self) -> Tuple[str, ...]:
        """Column names in the dataset.

        Returns:
            Tuple of node names (column names) in the dataset.
        """
        pass

    @property
    @abstractmethod
    def sample(self) -> Any:
        """Access to underlying data sample.

        Returns:
            The underlying DataFrame or data structure for direct access.
            Used for operations like .unique() on columns.
        """
        pass

    @property
    @abstractmethod
    def node_types(self) -> Dict[str, str]:
        """Node type mapping for each variable.

        Returns:
            Dictionary mapping node names to their types.
            Format: {node: 'category' | 'continuous'}
        """
        pass

    @abstractmethod
    def write(self, filename: str) -> None:
        """Write data to file.

        Args:
            filename: Path to output file.

        Raises:
            TypeError: If filename is not a string.
            FileNotFoundError: If output directory doesn't exist.
        """
        pass
