# Bayesys Format I/O

The `causaliq_core.graph.io.bayesys` module provides functions for reading and writing graphs in the Bayesys CSV format.

## Format Description

The Bayesys format uses CSV files to represent graphs where:
- Each row represents an edge in the graph
- Columns specify source node, edge type, and target node
- Edge types include directed (`->`) and undirected (`--`) edges

## Functions

### `read(path: str, all_nodes: Optional[List[str]] = None, strict: bool = True) -> Union[PDAG, DAG]`

Read a graph from a Bayesys CSV format file.

**Parameters:**
- `path` (str): Full path name of file to read
- `all_nodes` (List[str], optional): Complete list of nodes that should be included in the graph. If provided, nodes not appearing in edges will be added as isolated nodes
- `strict` (bool): If True, enforces strict format validation

**Returns:**
- `PDAG` or `DAG`: Graph read from file. Returns DAG if all edges are directed, PDAG otherwise

**Raises:**
- `TypeError`: If path is not a string
- `FileNotFoundError`: If file is not found
- `FileFormatError`: If file format is invalid

**Example:**

```python
from causaliq_core.graph.io.bayesys import read

# Read graph with automatic node detection
graph = read("data/graph.csv")

# Read graph with explicit node list
all_nodes = ['A', 'B', 'C', 'D'] 
graph = read("data/graph.csv", all_nodes=all_nodes)
```

### `write(graph: Union[PDAG, DAG], path: str) -> None`

Write a graph to a Bayesys CSV format file.

**Parameters:**
- `graph` (PDAG or DAG): Graph to write
- `path` (str): Full path name of file to create

**Raises:**
- `TypeError`: If graph is not a PDAG or DAG instance, or path is not a string
- `OSError`: If file cannot be created

**Example:**

```python
from causaliq_core.graph import PDAG
from causaliq_core.graph.io.bayesys import write

# Create and write a PDAG
pdag = PDAG(['X', 'Y', 'Z'], [('X', '->', 'Y'), ('Y', '--', 'Z')])
write(pdag, "output/graph.csv")
```

## File Format Details

The CSV file contains rows with three columns:
1. Source node name
2. Edge type (`->` for directed, `--` for undirected)  
3. Target node name

Example CSV content:
```csv
A,->,B
B,--,C
A,--,C
```

This represents a PDAG with nodes A, B, C where:
- A → B (directed edge)
- B — C (undirected edge)
- A — C (undirected edge)