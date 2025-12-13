# Distribution Classes

The distribution module provides conditional node distribution (CND) classes for representing local probability distributions in Bayesian Networks. These classes define how each node's values depend on its parents in the network.

## Overview

The distribution classes implement different types of conditional probability distributions:

 - **CPT**: Discrete conditional probability tables for categorical variables
 - **LinGauss**: Linear Gaussian distributions for continuous variables  
 - **CND**: Abstract base class defining the common interface

## Distribution Types

### [Conditional Probability Tables (CPT)](bn_dist_cpt.md)

Used for discrete/categorical variables. Stores probability tables that map parent value combinations to child value probabilities.

**Key Features:**

 - Support for multiple discrete parent variables
 - Efficient storage and lookup of probability values
 - Automatic normalization and validation
 - Missing data handling

### [Linear Gaussian (LinGauss)](bn_dist_lingauss.md)

Used for continuous variables that follow normal distributions with linear dependencies on parents.

**Key Features:**

 - Linear regression relationships with parent variables
 - Support for both continuous and discrete parent variables
 - Gaussian noise modeling
 - Parameter estimation from data

### [Base Class (CND)](bn_dist_cnd.md)

Abstract base class that defines the common interface for all conditional node distributions.

**Key Features:**

 - Common methods for probability computation
 - Standardized parameter access
 - Consistent serialization interface
 - Type checking and validation

## Common Operations

All distribution classes support common operations:

 - **Probability Evaluation**: Computing P(child | parents)
 - **Sampling**: Generating samples from the distribution
 - **Parameter Access**: Getting and setting distribution parameters
 - **Validation**: Checking parameter consistency

## Example Usage

```python
from causaliq_core.bn.dist import CPT, LinGauss

# Create discrete distribution (CPT)
weather_dist = CPT(
    values=['Sunny', 'Rainy'], 
    table=[0.7, 0.3]  # P(Weather=Sunny)=0.7, P(Weather=Rainy)=0.3
)

# Create conditional discrete distribution
sprinkler_dist = CPT(
    values=['On', 'Off'],
    table=[0.1, 0.9, 0.8, 0.2],  # Depends on Weather
    parents=['Weather']
)

# Create continuous distribution
temperature_dist = LinGauss(
    mean=20.0,      # Base temperature
    sd=2.0,         # Standard deviation  
    coeffs={},      # No parent dependencies in this example
    parents=[]
)
```

## Distribution Selection

Choose the appropriate distribution type based on your variable characteristics:

 - **Use CPT** for categorical/discrete variables (e.g., weather conditions, disease status)
 - **Use LinGauss** for continuous variables with linear relationships (e.g., temperature, measurements)

## API Reference

::: causaliq_core.bn.dist
    options:
      show_source: false
      heading_level: 3