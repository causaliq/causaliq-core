# Graph PDG Module

The `PDG` (Probabilistic Dependency Graph) class represents a probability
distribution over edge states between node pairs. Unlike SDG which stores
a single deterministic edge type, PDG stores probabilities for each possible
edge state.

## Overview

PDG is designed for:

- **Graph averaging**: Combining multiple structure learning runs
- **Uncertainty representation**: Representing structural uncertainty in
  causal graphs
- **LLM fusion**: Integrating LLM-generated graphs with statistical methods

The PDG class is independent of the SDG class hierarchy (not a subclass)
as it represents a fundamentally different concept: a distribution over
graphs rather than a single graph.

## Classes

### `EdgeProbabilities`

Probability distribution over edge states between two nodes.

Stores probabilities for each possible edge state:

- `forward`: P(source -> target) directed edge in stored direction
- `backward`: P(target -> source) directed edge opposite to stored
- `undirected`: P(source -- target) undirected edge
- `none`: P(no edge between source and target)

**Properties:**

- `p_exist`: Probability that any edge exists (sum of forward, backward,
  undirected)
- `p_directed`: Probability of a directed edge (sum of forward, backward)
- `most_likely_state()`: Returns the most probable edge state

**Usage:**

```python
from causaliq_core.graph import EdgeProbabilities

# Create edge probability distribution
probs = EdgeProbabilities(
    forward=0.6,
    backward=0.2,
    undirected=0.1,
    none=0.1
)

# Query properties
print(probs.p_exist)      # 0.9 (probability edge exists)
print(probs.p_directed)   # 0.8 (probability edge is directed)
print(probs.most_likely_state())  # "forward"
```

### `PDG`

Probabilistic Dependency Graph - distribution over SDG structures.

**Features:**

- Stores probability distributions for each node pair
- Greedy DAG extraction with cycle avoidance
- Compact binary compression/decompression
- GraphML I/O for serialisation

**Usage:**

```python
from causaliq_core.graph import PDG, EdgeProbabilities

# Create a PDG
nodes = ["A", "B", "C"]
edges = {
    ("A", "B"): EdgeProbabilities(forward=0.8, none=0.2),
    ("A", "C"): EdgeProbabilities(forward=0.6, backward=0.3, none=0.1),
}
pdg = PDG(nodes, edges)

# Query edge probabilities
probs = pdg.get_probabilities("A", "B")
print(probs.forward)  # 0.8

# Extract a DAG greedily (edges ranked by probability)
result = pdg.to_dag_greedy(threshold=0.5)
print(result.dag)             # The extracted DAG
print(result.edges_included)  # Number of edges added
```

### `GreedyDAGResult`

NamedTuple returned by `PDG.to_dag_greedy()`.

**Fields:**

- `dag`: The extracted `DAG`.
- `edges_included`: Number of edges added to the DAG.
- `edges_skipped_cycle`: Edges skipped to avoid cycles.
- `edges_skipped_threshold`: Edges below the probability threshold.
- `tie_breaks_applied`: Edges where alphabetical tie-breaking was used.

### `PDG.to_dag_greedy(threshold=0.0)`

Extract a DAG from the PDG using a greedy algorithm.

**Algorithm:**

1. For each edge pair, compute effective forward and backward probabilities
   by splitting the undirected probability equally between directions.
2. Choose the direction with the higher effective probability.
3. For ties (effective forward equals effective backward), use alphabetical
   ordering (source < target, i.e. forward direction).
4. Sort candidate edges by descending probability.
5. Greedily add edges, skipping any that would create a cycle (checked
   via ancestor tracking with propagation to descendants).

**Parameters:**

- `threshold` (float): Minimum `p_exist` to consider an edge (default 0.0).

**Returns:**

- `GreedyDAGResult`: The extracted DAG and extraction statistics.

**Usage:**

```python
result = pdg.to_dag_greedy(threshold=0.5)
print(result.edges_included)        # 2
print(result.edges_skipped_cycle)    # 0
print(result.tie_breaks_applied)     # 0
```

### `PDG.compress()` / `PDG.decompress(data)`

Compact binary serialisation of a PDG.

`compress()` encodes the PDG to a compact binary format where each
probability is stored in 3 bytes (4 significant figures). The `p_none`
value is derived as `1.0 - (forward + backward + undirected)`.
`decompress()` reconstructs a `PDG` from the binary representation.

**Usage:**

```python
blob = pdg.compress()
pdg2 = PDG.decompress(blob)
```

## Reference

::: causaliq_core.graph.pdg
    options:
        show_root_heading: false
        show_source: false
        heading_level: 3
        members_order: source
        group_by_category: true
        show_category_heading: true
