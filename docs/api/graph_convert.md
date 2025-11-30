# Graph Conversion Functions

The `convert` module provides functions for transforming between different graph representations used in causal discovery algorithms and utilities for working with adjacency matrices.

## Functions

### `dag_to_pdag(dag)`

Convert a DAG to its corresponding PDAG representation (equivalence class).

**Parameters:**

- `dag` (DAG): The directed acyclic graph to convert

**Returns:**

- `PDAG`: PDAG representing the Markov equivalence class

**Usage:**

```python
from causaliq_core.graph import DAG, dag_to_pdag

# Create a DAG
dag = DAG(['X', 'Y', 'Z'], [('X', '->', 'Y'), ('Y', '->', 'Z')])

# Convert to PDAG equivalence class
pdag = dag_to_pdag(dag)
```

### `pdag_to_cpdag(pdag)`

Convert a PDAG to its completed PDAG (CPDAG) form.

**Parameters:**

- `pdag` (PDAG): The partially directed graph to complete

**Returns:**

- `PDAG` or `None`: Completed PDAG, or None if completion fails

**Usage:**

```python
from causaliq_core.graph import PDAG, pdag_to_cpdag

# Create a PDAG
pdag = PDAG(['A', 'B', 'C'], [('A', '--', 'B'), ('B', '->', 'C')])

# Complete to CPDAG
cpdag = pdag_to_cpdag(pdag)
```

### `dict_to_adjmat(adjmat_dict, labels=None)`

Convert a dictionary representation of an adjacency matrix to a pandas DataFrame.

**Parameters:**

- `adjmat_dict` (Dict): Dictionary with (row, col) tuple keys and numeric values
- `labels` (List[str], optional): Variable labels. If None, creates labels A, B, C, etc.

**Returns:**

- `DataFrame`: Adjacency matrix as a pandas DataFrame

**Raises:**

- `TypeError`: If adjmat_dict is not a dictionary or labels is not a list
- `ValueError`: If keys are not tuples of length 2 or contain non-integer indices

**Usage:**

```python
from causaliq_core.graph.convert import dict_to_adjmat

# Create adjacency matrix from dictionary
adjmat_dict = {(0, 1): 1.0, (1, 2): 1.0}
labels = ['X', 'Y', 'Z']
df = dict_to_adjmat(adjmat_dict, labels)
```

### `extend_pdag(pdag)`

Extend a PDAG to a consistent DAG by orienting undirected edges.

**Parameters:**

- `pdag` (PDAG): The partially directed graph to extend

**Returns:**

- `DAG`: A DAG extension of the PDAG

**Usage:**

```python
from causaliq_core.graph import PDAG, extend_pdag

# Create a PDAG
pdag = PDAG(['X', 'Y'], [('X', '--', 'Y')])

# Extend to DAG
dag = extend_pdag(pdag)
```

### `is_cpdag(pdag)`

Check whether a PDAG is a completed PDAG (CPDAG).

**Parameters:**

- `pdag` (PDAG): The graph to check

**Returns:**

- `bool`: True if the PDAG is completed, False otherwise

**Usage:**

```python
from causaliq_core.graph import PDAG, is_cpdag

# Check if PDAG is complete
pdag = PDAG(['A', 'B'], [('A', '->', 'B')])
is_complete = is_cpdag(pdag)  # True
```

## Reference

::: causaliq_core.graph.convert
    options:
        show_root_heading: false
        show_source: false
        heading_level: 3
        members_order: source
        group_by_category: true
        show_category_heading: true