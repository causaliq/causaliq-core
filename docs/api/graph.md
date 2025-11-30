# Graph Module Overview

The `causaliq_core.graph` module provides graph-related classes and utilities for representing different types of graphs used in causal discovery algorithms, including directed acyclic graphs (DAGs), partially directed acyclic graphs (PDAGs), and summary dependence graphs (SDGs).

## Core Components

### [SDG - Summary Dependence Graph](graph_sdg.md)
Base graph class supporting mixed edge types:

- Directed, undirected, and bidirected edges
- General graph operations and validation
- Foundation for specialized graph types

### [PDAG - Partially Directed Acyclic Graph](graph_pdag.md) 
Specialized graph for causal discovery:

- Directed and undirected edges (no bidirected)
- Represents uncertainty in edge orientation
- Used in constraint-based causal discovery

### [DAG - Directed Acyclic Graph](graph_dag.md)
Fully oriented causal structures:

- Only directed edges
- Represents definite causal relationships
- Topological ordering and string representation

### [Graph Conversion Functions](graph_convert.md)
Transform between graph representations:

- `dag_to_pdag()` - DAG to equivalence class PDAG
- `pdag_to_cpdag()` - Complete a PDAG to CPDAG form
- `extend_pdag()` - Extend PDAG to consistent DAG
- `is_cpdag()` - Check if PDAG is completed
- `dict_to_adjmat()` - Convert dictionary to adjacency matrix DataFrame

## I/O Functions

### [Common I/O Functions](graph_io_common.md)
Unified interface for reading and writing graphs:

- `read()` - Automatically detects format and reads graphs
- `write()` - Automatically detects format and writes graphs
- Supports `.csv` (Bayesys) and `.tetrad` (Tetrad) formats
- Available directly from `causaliq_core.graph` for convenience

### [Bayesys Format I/O](graph_io_bayesys.md)
CSV-based graph file format:

- `read()` - Read graphs from Bayesys CSV files
- `write()` - Write graphs to Bayesys CSV format

### [Tetrad Format I/O](graph_io_tetrad.md)
Native Tetrad software format:

- `read()` - Read graphs from Tetrad format files
- `write()` - Write graphs to Tetrad format
- Supports both DAGs and PDAGs

### [Tetrad Format I/O](graph_io_tetrad.md)
Native Tetrad graph file format:

- `read()` - Read graphs from Tetrad format files
- `write()` - Write graphs to Tetrad format
- Supports both DAGs and PDAGs

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
        filters: ["!^SDG$", "!^PDAG$", "!^DAG$", "!^dag_to_pdag$", "!^pdag_to_cpdag$", "!^extend_pdag$", "!^is_cpdag$"]

## Implementation Notes

These classes and functions provide a standardised way to represent and manipulate different graph types commonly used in causal discovery algorithms. The hierarchy (SDG → PDAG → DAG) reflects increasing constraints on edge types and graph structure.