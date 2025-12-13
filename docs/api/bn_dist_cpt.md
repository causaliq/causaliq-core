# CPT (Conditional Probability Table)

The `CPT` class represents conditional probability tables for discrete/categorical variables in Bayesian Networks. It stores and manages probability distributions that map parent value combinations to child variable probabilities.

## Overview

A Conditional Probability Table (CPT) defines the local probability distribution for a discrete node given its parent values. It consists of:

 - **Values**: The possible states/categories for this variable
 - **Table**: Probability values organized by parent combinations
 - **Parents**: Names of parent variables (if any)
 - **Normalization**: Ensures probabilities sum to 1 for each parent combination

## Key Features

 - **Flexible Parent Support**: Handle any number of discrete parent variables
 - **Efficient Storage**: Compact representation of probability tables
 - **Automatic Validation**: Ensures probability constraints are satisfied
 - **Missing Data Handling**: Robust handling of incomplete data during learning
 - **Fast Lookup**: Optimized probability queries

## Table Organization

For a node with parents, the probability table is organized as:

 - **Rows**: Each parent value combination
 - **Columns**: Each possible value of the child variable  
 - **Entries**: P(child=value | parents=combination)

## Example Usage

```python
from causaliq_core.bn.dist import CPT

# Simple unconditional distribution
weather = CPT(
    values=['Sunny', 'Rainy'],
    table=[0.8, 0.2]  # P(Sunny)=0.8, P(Rainy)=0.2
)

# Conditional distribution with one parent
sprinkler = CPT(
    values=['On', 'Off'], 
    parents=['Weather'],
    table=[
        0.1, 0.9,  # P(Sprinkler | Weather=Sunny) = [0.1, 0.9] 
        0.7, 0.3   # P(Sprinkler | Weather=Rainy) = [0.7, 0.3]
    ]
)

# Conditional distribution with multiple parents
grass = CPT(
    values=['Wet', 'Dry'],
    parents=['Weather', 'Sprinkler'], 
    table=[
        # Weather=Sunny, Sprinkler=On:  P(Wet)=0.9, P(Dry)=0.1
        # Weather=Sunny, Sprinkler=Off: P(Wet)=0.2, P(Dry)=0.8  
        # Weather=Rainy, Sprinkler=On:  P(Wet)=0.95, P(Dry)=0.05
        # Weather=Rainy, Sprinkler=Off: P(Wet)=0.8, P(Dry)=0.2
        0.9, 0.1, 0.2, 0.8, 0.95, 0.05, 0.8, 0.2
    ]
)

# Access probabilities
prob = sprinkler.prob('On', parents_values={'Weather': 'Rainy'})
print(f"P(Sprinkler=On | Weather=Rainy) = {prob}")
```

## Data Learning

CPTs can learn parameters from data:

```python
import pandas as pd
from causaliq_core.bn.dist import CPT

# Training data
data = pd.DataFrame({
    'Weather': ['Sunny', 'Rainy', 'Sunny', 'Rainy', 'Sunny'],
    'Sprinkler': ['Off', 'On', 'On', 'Off', 'Off']
})

# Learn CPT from data
learned_cpt = CPT.from_data(
    variable='Sprinkler',
    parents=['Weather'], 
    data=data,
    values=['On', 'Off']
)
```

## NodeValueCombinations Utility

The module also provides the `NodeValueCombinations` utility class for handling parent value combinations:

```python
from causaliq_core.bn.dist import NodeValueCombinations

# Create combinations for multiple parents
nvc = NodeValueCombinations(['Weather', 'Season'], 
                          [['Sunny', 'Rainy'], ['Summer', 'Winter']])

# Get all combinations
combinations = nvc.combinations()
# Result: [('Sunny', 'Summer'), ('Sunny', 'Winter'), 
#          ('Rainy', 'Summer'), ('Rainy', 'Winter')]
```

## API Reference

::: causaliq_core.bn.dist.cpt
    options:
      show_source: false
      heading_level: 3