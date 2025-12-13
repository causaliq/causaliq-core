# CND (Conditional Node Distribution) Base Class

The `CND` class is the abstract base class for all conditional node distributions in Bayesian Networks. It defines the common interface and functionality that all distribution types must implement.

## Overview

The `CND` class establishes a consistent interface for:

 - **Probability Computation**: Methods for evaluating probabilities and densities
 - **Parameter Access**: Standardized ways to get and set distribution parameters  
 - **Validation**: Common validation and consistency checking
 - **Serialization**: Uniform methods for saving and loading distributions
 - **Type System**: Ensures all distributions work consistently within BNs

## Abstract Interface

All concrete distribution classes (CPT, LinGauss) must implement the CND interface:

```python
from abc import ABC, abstractmethod

class CND(ABC):
    @abstractmethod
    def prob(self, value, parents_values=None):
        """Compute probability/density for given value and parent values."""
        pass
        
    @abstractmethod  
    def sample(self, parents_values=None):
        """Generate a sample from the distribution."""
        pass
        
    @abstractmethod
    def validate(self):
        """Check distribution parameters for consistency."""
        pass
```

## Common Attributes

All CND instances provide:

 - **`parents`**: List of parent variable names
 - **`node_type`**: Type of distribution ('discrete' or 'continuous')  
 - **`param_count`**: Number of free parameters in the distribution

## Usage Patterns

The CND base class is typically used for:

 - **Type Checking**: Ensuring objects are valid distributions
 - **Polymorphism**: Writing code that works with any distribution type
 - **Interface Definition**: Understanding what methods distributions provide
 - **Extension**: Creating new distribution types

## Example Usage

```python
from causaliq_core.bn.dist import CPT, LinGauss, CND

# Create different distribution types
discrete_dist = CPT(values=['A', 'B'], table=[0.3, 0.7])
continuous_dist = LinGauss(mean=0.0, sd=1.0, coeffs={}, parents=[])

# Both implement the CND interface
distributions = [discrete_dist, continuous_dist]

for dist in distributions:
    assert isinstance(dist, CND)  # Type checking
    
    # Common interface methods
    sample = dist.sample()  # Generate sample
    dist.validate()         # Check consistency
    
    print(f"Distribution type: {dist.node_type}")
    print(f"Parameter count: {dist.param_count}")
    print(f"Sample: {sample}")
```

## Implementing Custom Distributions

To create a new distribution type, inherit from CND and implement the abstract methods:

```python
from causaliq_core.bn.dist.cnd import CND
import random

class BernoulliDistribution(CND):
    """Custom Bernoulli distribution example."""
    
    def __init__(self, p=0.5, parents=None):
        self.p = p
        self.parents = parents or []
        self.node_type = 'discrete'
        
    def prob(self, value, parents_values=None):
        """Compute probability for Bernoulli distribution."""
        if value == 1:
            return self.p
        elif value == 0:
            return 1 - self.p
        else:
            return 0.0
            
    def sample(self, parents_values=None):
        """Generate Bernoulli sample."""
        return 1 if random.random() < self.p else 0
        
    def validate(self):
        """Check parameter validity."""
        if not 0 <= self.p <= 1:
            raise ValueError("Bernoulli parameter must be in [0,1]")
            
    @property
    def param_count(self):
        return 1  # One free parameter (p)

# Use custom distribution
custom_dist = BernoulliDistribution(p=0.3)
assert isinstance(custom_dist, CND)
sample = custom_dist.sample()
```

## Validation Framework

The CND base class provides a validation framework that:

 - **Parameter Checking**: Ensures parameters are in valid ranges
 - **Consistency Validation**: Checks internal consistency of distributions
 - **Parent Validation**: Verifies parent relationships are valid
 - **Error Reporting**: Provides clear error messages for invalid configurations

## Integration with BN Class

The CND interface ensures that:

 - Any CND subclass can be used in a BN
 - Probabilistic inference works consistently across distribution types
 - Parameter learning follows the same patterns
 - Serialization and I/O operations are uniform

## API Reference

::: causaliq_core.bn.dist.cnd
    options:
      show_source: false
      heading_level: 3