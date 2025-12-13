# BN Class

The `BN` class is the main class for representing Bayesian Networks in CausalIQ Core. It combines a directed acyclic graph (DAG) structure with conditional probability distributions to create a complete probabilistic model.

## Overview

A Bayesian Network consists of:

 - A **DAG structure** defining the conditional independence relationships
 - **Conditional Node Distributions (CNDs)** for each node specifying local probability distributions
 - **Parameters** that can be learned from data or specified manually

## Key Features

 - **Probabilistic Inference**: Compute marginal and conditional probabilities
 - **Parameter Learning**: Fit distributions from data using the `fit()` method
 - **Multiple Distribution Types**: Support for both discrete (CPT) and continuous (LinGauss) distributions
 - **Caching**: Efficient computation with cached marginals
 - **Serialization**: Save and load networks in multiple formats

## Class Methods

The BN class provides several key methods:

 - **Construction**: Initialize from DAG and conditional distribution specifications
 - **Inference**: Compute marginals and conditional probabilities
 - **Learning**: Fit parameters from data
 - **Validation**: Check network consistency and parameter validity

## Example Usage

```python
from causaliq_core.bn import BN, CPT
from causaliq_core.graph import DAG

# Create DAG structure
dag = DAG(['Weather', 'Sprinkler', 'Grass'], 
          [('Weather', 'Sprinkler'), ('Weather', 'Grass'), ('Sprinkler', 'Grass')])

# Define conditional distributions  
cnd_specs = {
    'Weather': CPT(values=['Sunny', 'Rainy'], table=[0.7, 0.3]),
    'Sprinkler': CPT(values=['On', 'Off'], 
                     table=[0.1, 0.9, 0.8, 0.2], 
                     parents=['Weather']),
    'Grass': CPT(values=['Wet', 'Dry'],
                 table=[0.95, 0.05, 0.8, 0.2, 0.9, 0.1, 0.05, 0.95],
                 parents=['Weather', 'Sprinkler'])
}

# Create Bayesian Network
bn = BN(dag, cnd_specs)

# Compute marginal probabilities
marginals = bn.marginals(['Weather', 'Grass'])
print(marginals)

# Compute conditional probability
conditional = bn.conditional(['Grass'], ['Weather'], 'Rainy')
print(conditional)
```

## API Reference

::: causaliq_core.bn.bn.BN
    options:
      show_source: false
      heading_level: 3