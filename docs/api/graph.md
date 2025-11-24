# Graph Module

The `causaliq_core.graph` module provides graph-related enumerations and utilities for representing different types of edges used in causal discovery algorithms.

## Constants

### `BAYESYS_VERSIONS`

List of supported BayeSys versions for graph comparison semantics.

**Value:** `['v1.3', 'v1.5+']`

**Usage:**

```python
from causaliq_core.graph import BAYESYS_VERSIONS

# Check version compatibility
if version in BAYESYS_VERSIONS:
    print(f"Version {version} is supported")
```

## Functions

### `adjmat(columns)`

Create an adjacency matrix with specified entries.

**Parameters:**

- `columns` (dict): Data for matrix specified by column, where each key is a column name and each value is a list of integers representing edge types

**Returns:**

- `DataFrame`: The adjacency matrix with proper indexing

**Raises:**

- `TypeError`: If argument types are incorrect
- `ValueError`: If values specified are invalid (wrong lengths or invalid edge codes)

**Usage:**

```python
from causaliq_core.graph import adjmat, EdgeType

# Create a simple adjacency matrix
columns = {
    'A': [0, 1, 0],  # No edge, directed edge, no edge
    'B': [0, 0, 1],  # No edge, no edge, directed edge  
    'C': [0, 0, 0]   # No edge, no edge, no edge
}
adj_matrix = adjmat(columns)
```

## Classes

### `EdgeMark`

Enumeration of supported 'ends' of an edge in a graph.

**Values:**

- `NONE = 0`: No marking on edge end
- `LINE = 1`: Line marking (e.g., for undirected edges)
- `ARROW = 2`: Arrow marking (e.g., for directed edges)  
- `CIRCLE = 3`: Circle marking (e.g., for partial direction)

**Usage:**

```python
from causaliq_core.graph import EdgeMark

# Check edge marking
if edge_end == EdgeMark.ARROW:
    print("This end is directed")
```

### `EdgeType`

Enumeration of supported edge types and their symbols, combining start and end markings.

**Structure:**

Each edge type is defined as a tuple containing:
- `(value, start_mark, end_mark, symbol)`

**Usage:**

```python
from causaliq_core.graph import EdgeType, EdgeMark

# Access edge type components
edge = EdgeType.DIRECTED
print(f"Symbol: {edge.symbol}")
print(f"Start: {edge.start_mark}")
print(f"End: {edge.end_mark}")
```

## Reference

::: causaliq_core.graph
    options:
        show_root_heading: false
        show_source: false
        heading_level: 3
        members_order: source
        group_by_category: true
        show_category_heading: true

## Implementation Notes

These enumerations provide a standardised way to represent edge types commonly used in causal discovery algorithms, including directed edges, undirected edges, and partially directed edges found in PDAGs (Partially Directed Acyclic Graphs).