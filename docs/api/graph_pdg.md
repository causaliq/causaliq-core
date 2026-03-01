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
- Supports threshold-based graph extraction
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

# Extract graph at threshold
pdag = pdg.to_pdag(threshold=0.5)
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
