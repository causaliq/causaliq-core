# GraphML Format I/O

GraphML I/O functions for reading and writing graphs in GraphML format.
Supports both standard graphs (SDG, PDAG, DAG) and probabilistic
dependency graphs (PDG).

## Overview

GraphML is an XML-based format for graphs. This module supports:

- Reading and writing SDG, PDAG, and DAG graphs
- Reading and writing PDG (probabilistic) graphs
- Both filesystem paths and file-like objects (e.g., StringIO)
- Interoperability with workflow caches

Reference: [GraphML Specification](http://graphml.graphdrawing.org/)

## Functions

### Standard Graph I/O

#### `read()`

Read a graph from a GraphML file or file-like object.

```python
from causaliq_core.graph.io import graphml

# From file path
graph = graphml.read("graph.graphml")

# From file-like object
from io import StringIO
xml_content = '<graphml>...</graphml>'
graph = graphml.read(StringIO(xml_content))
```

Returns SDG, PDAG, or DAG depending on edge types in the graph.

#### `write()`

Write a graph to a GraphML file or file-like object.

```python
from causaliq_core.graph import DAG
from causaliq_core.graph.io import graphml

dag = DAG(["A", "B"], [("A", "->", "B")])

# To file path
graphml.write(dag, "output.graphml")

# To file-like object
from io import StringIO
buffer = StringIO()
graphml.write(dag, buffer)
xml_content = buffer.getvalue()
```

### PDG I/O

#### `read_pdg()`

Read a Probabilistic Dependency Graph from GraphML.

```python
from causaliq_core.graph.io import graphml

pdg = graphml.read_pdg("probabilistic_graph.graphml")
```

#### `write_pdg()`

Write a Probabilistic Dependency Graph to GraphML.

```python
from causaliq_core.graph import PDG
from causaliq_core.graph.io import graphml

pdg = PDG(nodes, edges)
graphml.write_pdg(pdg, "output.graphml")
```

## Type Alias

### `FileLike`

Type alias for file path or file-like object:

```python
FileLike = Union[str, Path, TextIO]
```

## Reference

::: causaliq_core.graph.io.graphml.read
    options:
        show_source: false

::: causaliq_core.graph.io.graphml.write
    options:
        show_source: false

::: causaliq_core.graph.io.graphml.read_pdg
    options:
        show_source: false

::: causaliq_core.graph.io.graphml.write_pdg
    options:
        show_source: false
