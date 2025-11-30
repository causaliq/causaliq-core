# Graph SDG Module

This module supports Simple Dependency Graphs (SDGs) which are a general
form of graph that has at most one edge between any pair of nodes.

The two endpoints of each edge can be a head ">", tail "-" or circle "o"
(which means either head or tail).

This format can represent most dependency graph types including:
 - Markov Graphs
 - Directed Acyclic Graphs (DAGs)
 - Partially Directed Acyclic Graphs (PDAGs)
 - Maximal Ancestral Graphs (MAGs)
 - Partial Ancestral Graphs (PAGs)
 
## Classes

### `SDG`

Simple Dependency Graph class that supports multiple edge types.

**Features:**

- Mixed edge types (directed, undirected, bidirected)
- Node and edge validation
- Graph manipulation and traversal
- Adjacency matrix representation

**Usage:**

```python
from causaliq_core.graph import SDG, EdgeType

# Create an SDG with mixed edges
nodes = ['A', 'B', 'C']
edges = [
    ('A', '->', 'B'),    # Directed edge
    ('B', '--', 'C'),    # Undirected edge
]
sdg = SDG(nodes, edges)
```

## Reference

::: causaliq_core.graph.sdg
    options:
        show_root_heading: false
        show_source: false
        heading_level: 3
        members_order: source
        group_by_category: true
        show_category_heading: true