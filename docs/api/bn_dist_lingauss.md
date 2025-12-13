# LinGauss (Linear Gaussian Distribution)

The `LinGauss` class represents Linear Gaussian distributions for continuous variables in Bayesian Networks. It models variables that follow normal distributions with linear dependencies on their parent variables.

## Overview

A Linear Gaussian distribution models a continuous variable as:

```
X = μ + Σ βᵢ * Parentᵢ + ε
```

Where:

 - **μ (mean)**: Base mean value when all parents are zero
 - **βᵢ (coefficients)**: Linear coefficients for each parent variable
 - **σ (sd)**: Standard deviation of the Gaussian noise term ε
 - **ε**: Zero-mean Gaussian noise with variance σ²

## Key Features

 - **Linear Relationships**: Models linear dependencies on parent variables
 - **Mixed Parents**: Support for both continuous and discrete parent variables
 - **Parameter Learning**: Efficient estimation from data using regression
 - **Probabilistic Inference**: Exact inference for Gaussian networks
 - **Robust Estimation**: Handles missing data and numerical stability

## Model Specification

The distribution is fully specified by:

 - **Mean (μ)**: Baseline value of the variable
 - **Standard Deviation (σ)**: Noise level/uncertainty  
 - **Coefficients**: Linear weights for each parent variable
 - **Parents**: Names of parent variables in the network

## Example Usage

```python
from causaliq_core.bn.dist import LinGauss

# Simple unconditional Gaussian
temperature = LinGauss(
    mean=20.0,    # 20°C baseline
    sd=3.0,       # 3°C standard deviation
    coeffs={},    # No parents
    parents=[]
)

# Linear dependency on one continuous parent
outdoor_temp = LinGauss(
    mean=15.0,        # Base indoor temperature  
    sd=2.0,           # Noise level
    coeffs={'OutdoorTemp': 0.7},  # 0.7 * OutdoorTemp
    parents=['OutdoorTemp']
)

# Multiple parent dependencies
room_temp = LinGauss(
    mean=18.0,
    sd=1.5, 
    coeffs={
        'OutdoorTemp': 0.4,    # Outdoor influence
        'HeatingLevel': 2.0    # Heating system effect
    },
    parents=['OutdoorTemp', 'HeatingLevel']
)

# Sample from distribution
sample = room_temp.sample({'OutdoorTemp': 10.0, 'HeatingLevel': 5.0})
print(f"Room temperature sample: {sample:.1f}°C")

# Compute probability density
density = room_temp.pdf(22.0, {'OutdoorTemp': 15.0, 'HeatingLevel': 3.0})
print(f"PDF at 22°C: {density:.4f}")
```

## Learning from Data

LinGauss distributions can learn parameters from data using linear regression:

```python
import pandas as pd
from causaliq_core.bn.dist import LinGauss

# Training data
data = pd.DataFrame({
    'OutdoorTemp': [10, 15, 20, 25, 30],
    'HeatingLevel': [8, 6, 4, 2, 0], 
    'IndoorTemp': [18, 19, 21, 23, 24]
})

# Learn distribution from data
learned_dist = LinGauss.from_data(
    variable='IndoorTemp',
    parents=['OutdoorTemp', 'HeatingLevel'],
    data=data
)

print(f"Learned mean: {learned_dist.mean}")
print(f"Learned coefficients: {learned_dist.coeffs}")
print(f"Learned standard deviation: {learned_dist.sd}")
```

## Discrete Parents

LinGauss can also handle discrete parent variables by treating them as indicator variables:

```python
# Distribution with discrete parent
energy_usage = LinGauss(
    mean=100.0,      # Base energy usage
    sd=10.0,
    coeffs={
        'Season': 20.0,     # Extra usage in winter
        'OutdoorTemp': -2.0  # Decrease with higher temp
    },
    parents=['Season', 'OutdoorTemp']  # Season is discrete, OutdoorTemp continuous
)

# Season would be encoded as 0 (Summer) or 1 (Winter)
usage = energy_usage.sample({'Season': 1, 'OutdoorTemp': 5.0})  # Winter, 5°C
```

## Inference Properties

Linear Gaussian networks have special properties:

 - **Exact Inference**: Marginal and conditional distributions remain Gaussian
 - **Efficient Computation**: No approximation needed for probabilistic queries
 - **Analytical Solutions**: Closed-form expressions for most operations
 - **Numerical Stability**: Well-conditioned linear algebra operations

## API Reference

::: causaliq_core.bn.dist.lingauss
    options:
      show_source: false
      heading_level: 3