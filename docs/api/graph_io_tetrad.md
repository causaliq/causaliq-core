# Tetrad Format I/O

The `causaliq_core.graph.io.tetrad` module provides functions for reading and writing graphs in the Tetrad native format.

## Format Description

The Tetrad format is a text-based format used by the Tetrad software suite for representing graphs:
- Each line represents an edge with numbered format
- Supports directed (`-->`) and undirected (`---`) edges  
- Nodes are identified by names, edges by source and target nodes

## Functions

### `read(path: str) -> Union[DAG, PDAG]`

Read a graph from a Tetrad format file.

**Parameters:**
- `path` (str): Full path name of file to read

**Returns:**
- `DAG` or `PDAG`: Graph read from file. Returns DAG if all edges are directed, PDAG otherwise

**Raises:**
- `TypeError`: If path is not a string
- `FileNotFoundError`: If file is not found  
- `FileFormatError`: If file format is invalid or contains syntax errors

**Example:**

```python
from causaliq_core.graph.io.tetrad import read

# Read graph from Tetrad format file
graph = read("data/graph.tetrad")
```

### `write(graph: Union[PDAG, DAG], path: str) -> None`

Write a graph to a Tetrad format file.

**Parameters:**
- `graph` (PDAG or DAG): Graph to write
- `path` (str): Full path name of file to create

**Raises:**
- `TypeError`: If graph is not a PDAG or DAG instance, or path is not a string
- `OSError`: If file cannot be created

**Example:**

```python
from causaliq_core.graph import DAG
from causaliq_core.graph.io.tetrad import write

# Create and write a DAG
dag = DAG(['X', 'Y', 'Z'], [('X', '->', 'Y'), ('Y', '->', 'Z')])
write(dag, "output/graph.tetrad")
```

## File Format Details

The Tetrad format uses numbered lines to represent edges:
- Each edge line starts with a number followed by a period
- Format: `{number}. {source} {edge_type} {target}`
- Edge types: `-->` for directed, `---` for undirected

Example Tetrad file content:
```
Graph Nodes:
X,Y,Z

Graph Edges:
1. X --> Y
2. Y --> Z  
```

This represents a DAG with nodes X, Y, Z and directed edges X → Y → Z.

## Compatibility

This module is compatible with graphs exported from:
- Tetrad software suite
- PCALG R package (when using Tetrad export format)
- Other causal discovery tools that support Tetrad format