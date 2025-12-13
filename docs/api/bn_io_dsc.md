# DSC Format I/O

The DSC format is CausalIQ's text-based format for specifying Bayesian Network structures and parameters. It provides a human-readable way to define networks that can be easily edited, version controlled, and shared.

## Overview

DSC (Directed Structure Configuration) files contain:

 - **Network Structure**: Node definitions and parent-child relationships
 - **Distribution Specifications**: Parameters for conditional distributions
 - **Metadata**: Additional information about the network
 - **Comments**: Documentation and annotations

## File Format Structure

A DSC file typically contains sections for:

```
# Network structure
nodes: A, B, C
edges: A -> B, A -> C, B -> C

# Distribution parameters  
node A {
    type: discrete
    values: true, false
    table: 0.3, 0.7
}

node B {
    type: discrete
    values: on, off
    parents: A
    table: 0.9, 0.1, 0.2, 0.8
}
```

## Key Features

 - **Human Readable**: Plain text format that's easy to understand
 - **Version Control Friendly**: Text format works well with Git and other VCS
 - **Compact**: Efficient representation without XML verbosity
 - **Extensible**: Support for custom metadata and annotations
 - **Cross-Platform**: Works on all operating systems

## Reading DSC Files

```python
from causaliq_core.bn.io import read_bn

# Read DSC file
bn = read_bn('network.dsc')

# Access loaded network properties
print(f"Nodes: {list(bn.dag.nodes)}")
print(f"Edges: {list(bn.dag.edges)}")

# Access distributions
for node_name, cnd in bn.cnds.items():
    print(f"Node {node_name}: {type(cnd).__name__}")
```

## Writing DSC Files

```python
from causaliq_core.bn.io import write_bn
from causaliq_core.bn import BN, CPT
from causaliq_core.graph import DAG

# Create a simple network
dag = DAG(['Rain', 'Sprinkler', 'Grass'], 
          [('Rain', 'Sprinkler'), ('Rain', 'Grass'), ('Sprinkler', 'Grass')])

cnd_specs = {
    'Rain': CPT(values=['Yes', 'No'], table=[0.2, 0.8]),
    'Sprinkler': CPT(values=['On', 'Off'], 
                     table=[0.01, 0.99, 0.4, 0.6], 
                     parents=['Rain']),
    'Grass': CPT(values=['Wet', 'Dry'],
                 table=[0.95, 0.05, 0.8, 0.2, 0.9, 0.1, 0.0, 1.0],
                 parents=['Rain', 'Sprinkler'])
}

bn = BN(dag, cnd_specs)

# Write to DSC file
write_bn(bn, 'lawn_sprinkler.dsc')
```

## DSC Syntax Examples

### Simple Discrete Node

```dsc
node Weather {
    type: discrete
    values: Sunny, Rainy
    table: 0.8, 0.2
}
```

### Conditional Discrete Node

```dsc
node Sprinkler {
    type: discrete
    values: On, Off
    parents: Weather
    table: 0.1, 0.9,    # P(Sprinkler | Weather=Sunny)
           0.7, 0.3     # P(Sprinkler | Weather=Rainy)
}
```

### Continuous Node (Linear Gaussian)

```dsc
node Temperature {
    type: continuous
    parents: Season, Location
    mean: 20.0
    sd: 3.5
    coeffs: Season=5.0, Location=-2.0
}
```

### Network Structure

```dsc
# Define all nodes
nodes: Weather, Sprinkler, Rain, Grass

# Define relationships  
edges: Weather -> Sprinkler,
       Weather -> Rain,
       Sprinkler -> Grass,
       Rain -> Grass

# Optional metadata
title: Lawn Watering Network
description: Models grass wetness based on weather and sprinkler
version: 1.2
```

## Error Handling

The DSC parser provides detailed error messages for common issues:

 - **Syntax Errors**: Line numbers and descriptions for invalid syntax
 - **Missing Definitions**: Clear messages for undefined nodes or parents
 - **Parameter Errors**: Validation of probability tables and distributions
 - **Structure Errors**: Detection of cycles and invalid relationships

## Advanced Features

### Comments and Documentation

```dsc
# This is a comment
node Weather {
    # Weather conditions for the day
    type: discrete
    values: Sunny, Rainy, Cloudy  # Three possible states
    table: 0.6, 0.2, 0.2         # Prior probabilities
}
```

### Include Files

```dsc
# Include common definitions
include: common_nodes.dsc

# Define network-specific nodes
node SpecialCase {
    type: discrete
    values: Yes, No
    table: 0.1, 0.9
}
```

### Parameter Macros

```dsc
# Define reusable parameters
define NOISE_LEVEL 0.05
define DEFAULT_MEAN 0.0

node Measurement {
    type: continuous
    mean: DEFAULT_MEAN
    sd: NOISE_LEVEL
}
```

## API Reference

::: causaliq_core.bn.io.dsc
    options:
      show_source: false
      heading_level: 3