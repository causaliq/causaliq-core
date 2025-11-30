# Graph DAG Module

The `DAG` (Directed Acyclic Graph) class provides functionality for working with fully directed acyclic graphs, commonly used to represent causal structures.

## Classes

### `DAG`

Directed Acyclic Graph class for representing fully oriented causal structures.

**Features:**

- Fully directed edges only
- Strict acyclicity enforcement
- Topological ordering
- String representation (bnlearn format)
- Causal model representation

**Usage:**

```python
from causaliq_core.graph import DAG

# Create a DAG
nodes = ['X', 'Y', 'Z']
edges = [
    ('X', '->', 'Y'),    # X causes Y
    ('Y', '->', 'Z'),    # Y causes Z
]
dag = DAG(nodes, edges)

# Get topological ordering
for node in dag.ordered_nodes():
    print(f"Node: {node}")

# Get string representation
print(dag.to_string())  # e.g. [X][Y|X][Z|Y]
```

### `NotDAGError`

Exception raised when attempting to create an invalid DAG (e.g., contains cycles).

## Reference

::: causaliq_core.graph.dag
    options:
        show_root_heading: false
        show_source: false
        heading_level: 3
        members_order: source
        group_by_category: true
        show_category_heading: true