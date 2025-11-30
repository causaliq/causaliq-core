# Graph PDAG Module

The `PDAG` (Partially Directed Acyclic Graph) class extends SDG to work specifically with partially directed acyclic graphs used in causal discovery.

## Classes

### `PDAG`

Partially Directed Acyclic Graph class for representing causal graph structures.

**Features:**

- Directed and undirected edges only
- Acyclicity validation
- Causal discovery algorithm support
- Conversion to/from other graph types

**Usage:**

```python
from causaliq_core.graph import PDAG

# Create a PDAG
nodes = ['X', 'Y', 'Z']
edges = [
    ('X', '->', 'Y'),    # Directed edge (oriented)
    ('Y', '--', 'Z'),    # Undirected edge (unoriented)
]
pdag = PDAG(nodes, edges)
```

### `NotPDAGError`

Exception raised when attempting to create an invalid PDAG.

## Reference

::: causaliq_core.graph.pdag
    options:
        show_root_heading: false
        show_source: false
        heading_level: 3
        members_order: source
        group_by_category: true
        show_category_heading: true