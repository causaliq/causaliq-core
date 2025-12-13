# Bayesian Networks Module

The Bayesian Networks module provides comprehensive functionality for working with probabilistic graphical models. It includes classes for representing Bayesian Networks, conditional node distributions, and various I/O formats.

## Overview

The `causaliq_core.bn` module consists of several key components:

 - **Core Classes**: Main BN and BNFit classes for network representation
 - **Distributions**: Conditional node distribution implementations
 - **I/O Operations**: Reading and writing BNs in various formats

## Main Classes

### [BN](bn_bn.md)
The main Bayesian Network class that combines a DAG structure with conditional probability distributions.

### [BNFit](bn_bnfit.md)  
A fitted Bayesian Network with learned parameters from data.

## Distribution Types

### [CPT (Conditional Probability Table)](bn_dist_cpt.md)
Discrete conditional probability distributions for categorical variables.

### [LinGauss (Linear Gaussian)](bn_dist_lingauss.md)
Continuous conditional distributions for normally distributed variables.

## I/O Formats

### [DSC Format](bn_io_dsc.md)
Reading and writing Bayesian Networks in DSC format.

### [XDSL Format](bn_io_xdsl.md) 
Reading and writing Bayesian Networks in GeNIe XDSL format.

## Key Features

 - **Probabilistic Inference**: Compute marginal and conditional probabilities
 - **Parameter Learning**: Fit network parameters from data
 - **Multiple Formats**: Support for DSC and XDSL file formats  
 - **Flexible Distributions**: Both discrete (CPT) and continuous (LinGauss) distributions
 - **Graph Integration**: Built on the causaliq_core.graph DAG structure

## Example Usage

```python
from causaliq_core.bn import BN, CPT
from causaliq_core.graph import DAG

# Create a simple DAG
dag = DAG(['A', 'B'], [('A', 'B')])

# Define conditional distributions
cnd_specs = {
    'A': CPT(values=['T', 'F'], table=[0.3, 0.7]),
    'B': CPT(values=['T', 'F'], table=[0.9, 0.1, 0.2, 0.8], parents=['A'])
}

# Create Bayesian Network
bn = BN(dag, cnd_specs)

# Compute marginals
marginals = bn.marginals(['A', 'B'])
```

## Module Structure

::: causaliq_core.bn
    options:
      show_source: false
      heading_level: 3