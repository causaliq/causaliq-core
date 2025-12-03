# CausalIQ Data Interface Specification

## Overview

This document defines the interface contract between CausalIQ Core and CausalIQ Data packages. The core package contains BN fitting algorithms (CPT.fit, LinGauss.fit) that require data access operations. The data package will provide concrete implementations of data sources.

## Abstract Data Interface

### `BNFit` (Abstract Base Class)

The core package requires data sources to implement this interface:

```python
from abc import ABC, abstractmethod
from typing import Dict, Tuple, Any
import numpy as np

class BNFit(ABC):
    """Abstract interface for data sources used in BN fitting."""

    @abstractmethod
    def marginals(self, node: str, parents: Dict, values_reqd: bool = False) -> Tuple:
        """Return marginal counts for a node and its parents.

        Args:
            node (str): Node for which marginals required.
            parents (dict): {node: parents} parents of non-orphan nodes
            values_reqd (bool): Whether parent and child values required

        Returns:
            tuple: Of counts, and optionally, values:
                   - ndarray counts: 2D, rows=child, cols=parents
                   - int maxcol: Maximum number of parental values
                   - tuple rowval: Child values for each row
                   - tuple colval: Parent combo (dict) for each col

        Raises:
            TypeError: For bad argument types
        """
        pass

    @abstractmethod
    def values(self, columns: Tuple[str, ...]) -> np.ndarray:
        """Return the (float) values for the specified set of columns.
        
        Suitable for passing into e.g. linearRegression fitting function

        Args:
            columns (tuple): Columns for which data required

        Returns:
            ndarray: Numpy array of values, each column for a node

        Raises:
            TypeError: If bad arg type
            ValueError: If bad arg value
        """
        pass

    @property
    @abstractmethod
    def N(self) -> int:
        """Total sample size.
        
        Returns:
            int: Current sample size being used
        """
        pass

    @property
    @abstractmethod
    def node_values(self) -> Dict[str, Dict]:
        """Node value counts for categorical variables.
        
        Returns:
            dict: Values and their counts of categorical nodes
                  in sample {n1: {v1: c1, v2: ...}, n2 ...}
        """
        pass
```

## Usage in Core Package

### CPT.fit() Dependencies

The CPT.fit() method requires these data operations:

```python
# For nodes with parents
counts, _, rowval, colval = data.marginals(node, {node: list(parents)}, True)

# For autocomplete functionality
data.N  # Total sample size
data.node_values[node]  # {value: count} for node
data.node_values[parent]  # {value: count} for each parent

# For orphan nodes
data.N
data.node_values[node]
```

### LinGauss.fit() Dependencies

The LinGauss.fit() method requires:

```python
# Get continuous values for regression
values = data.values((node,))  # For orphan nodes
values = data.values(tuple([node] + list(parents)))  # For nodes with parents
```

## Expected Concrete Implementations

The data package should provide these concrete classes:

### 1. `LegacyPandasAdapter` 
- Adapts existing legacy.data.Pandas class to DataInterface
- Delegates to existing marginals(), values(), N, node_values implementations
- Handles pandas DataFrames efficiently with crosstab-based marginals
- Ensures backward compatibility with existing test suites

### 2. `LegacyNumPyAdapter`
- Adapts existing legacy.data.NumPy class to BNFit interface  
- Delegates to existing marginals(), values(), N, node_values implementations
- **Enables NumPy support that doesn't currently work with core algorithms**
- For NumPy-based data sources

## Future Extensions

The interface is designed to be extensible for:
- **GPU-accelerated data sources** (e.g., CuPy, Rapids cuDF)
- **Database backends** (SQL, NoSQL)
- **Streaming data sources** 
- **Distributed data processing** (Dask, Spark)
- **Custom data transformations**

## Legacy Compatibility Requirements

The data package must maintain compatibility with existing usage patterns:

```python
# Existing legacy pattern that must continue working
from legacy.data.pandas import Pandas
data = Pandas(df)
cnd_spec, estimated = CPT.fit('B', ('A',), data)

# New pattern with adapter
from causaliq_data import LegacyDataAdapter
data_adapted = LegacyDataAdapter(data)
cnd_spec, estimated = CPT.fit('B', ('A',), data_adapted)
```

## Key Implementation Details

### marginals() Method Behavior

For **orphan nodes** (no parents):
- `parents` parameter: `{}` or `{node: []}`
- Returns: `(counts.reshape(-1, 1), 1, rowval, colval)`
- `rowval`: tuple of node values
- `colval`: tuple containing single empty dict `({},)`

For **nodes with single parent**:
- `parents` parameter: `{node: [parent_name]}`
- Returns: `(counts_2d, num_cols, rowval, colval)`
- `rowval`: tuple of child values
- `colval`: tuple of dicts `({parent: value},)`

For **nodes with multiple parents**:
- `parents` parameter: `{node: [parent1, parent2, ...]}`
- Returns: `(counts_2d, num_cols, rowval, colval)`
- `colval`: tuple of dicts `({parent1: val1, parent2: val2},)`

### values() Method Behavior

- Must return numpy array with float dtype
- Each column corresponds to a requested node
- Row order must be consistent with data source
- Should validate that all requested columns exist

### Error Handling Standards

All methods should raise:
- `TypeError`: For incorrect argument types
- `ValueError`: For invalid argument values (missing columns, etc.)

## Migration Path

1. **Phase 1**: Create data package with interface and implementations
2. **Phase 2**: Update core package to import DataInterface from data package
3. **Phase 3**: Update legacy tests to use adapters
4. **Phase 4**: Add new data source types as needed

## Testing Requirements

The data package should include:
- Unit tests for each concrete implementation
- Integration tests with core CPT.fit() and LinGauss.fit()
- Compatibility tests with legacy test suite
- Performance benchmarks for marginals calculation

## Future Extensions

The interface is designed to be extensible for:
- Database backends
- Streaming data sources
- Distributed data processing
- Custom data transformations

---

## Notes for Implementation

- Prioritize performance in marginals() calculation (this is the bottleneck)
- Consider caching computed marginals for repeated queries
- Ensure thread safety if needed for concurrent access
- Document any pandas version dependencies
- Consider memory efficiency for large datasets