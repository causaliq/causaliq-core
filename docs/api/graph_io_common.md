# Common I/O Functions

The `causaliq_core.graph.io.common` module provides a unified interface for reading and writing graphs from different file formats. It automatically detects the file format based on the file suffix and delegates to the appropriate format-specific module.

## Supported Formats

| Extension | Format | Module | Description |
|-----------|--------|--------|-------------|
| `.csv` | Bayesys | `bayesys` | CSV-based format used by Bayesys software |
| `.tetrad` | Tetrad | `tetrad` | Native format used by Tetrad software |

## Functions

### `read(path: str) -> Union[PDAG]`

Read a graph from a file, automatically detecting the format from the file suffix.

**Parameters:**
- `path` (str): Full path name of file to read

**Returns:**
- `PDAG` or `DAG`: Graph read from file

**Raises:**
- `TypeError`: If path is not a string
- `ValueError`: If file suffix is not supported
- `FileNotFoundError`: If file is not found
- `FileFormatError`: If file format is invalid

**Example:**

```python
# Import from common module directly
from causaliq_core.graph.io.common import read

# Or import from top-level graph module (recommended)
from causaliq_core.graph import read

# Read Bayesys CSV file
csv_graph = read("data/graph.csv")

# Read Tetrad format file  
tetrad_graph = read("data/graph.tetrad")
```

### `write(graph: PDAG, path: str) -> None`

Write a graph to a file, automatically detecting the format from the file suffix.

**Parameters:**
- `graph` (PDAG): Graph to write to file
- `path` (str): Full path name of file to write

**Raises:**
- `TypeError`: If bad argument types
- `ValueError`: If file suffix is not supported
- `FileNotFoundError`: If path to file does not exist

**Example:**

```python
# Import from common module directly
from causaliq_core.graph.io.common import write

# Or import from top-level graph module (recommended)
from causaliq_core.graph import write, DAG

# Create a graph
dag = DAG(["A", "B", "C"], [("A", "->", "B"), ("B", "->", "C")])

# Write to Bayesys CSV format
write(dag, "output/result.csv")

# Write to Tetrad format
write(dag, "output/result.tetrad")
```

## Usage Patterns

### Format Detection

The module uses the file extension to determine the appropriate format:

```python
# Import from top-level graph module (recommended)
from causaliq_core.graph import read

# These will use different I/O modules automatically
bayesys_graph = read("data.csv")      # Uses bayesys.read()
tetrad_graph = read("data.tetrad")    # Uses tetrad.read()
```

### Error Handling

```python
from causaliq_core.graph import read

try:
    graph = read("data.txt")  # Unsupported format
except ValueError as e:
    print(f"Unsupported format: {e}")
    # Output: "common.read() unsupported file suffix: .txt"
```

### Round-trip Operations

```python
from causaliq_core.graph import read, write

# Read graph in one format
graph = read("input.csv")

# Write in different format  
write(graph, "output.tetrad")

# Verify round-trip
graph2 = read("output.tetrad")
assert set(graph.nodes) == set(graph2.nodes)
```

## Reference

::: causaliq_core.graph.io.common
    options:
        show_root_heading: false
        show_source: false
        heading_level: 3