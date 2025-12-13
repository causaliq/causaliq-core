# BNFit Class

The `BNFit` class represents a fitted Bayesian Network with parameters learned from data. It provides convenient access to the learned conditional distributions and enables evaluation of the fitted model.

## Overview

A `BNFit` object is typically created as a result of parameter learning using the `BN.fit()` method. It contains:

 - The **original DAG structure** from the parent BN
 - **Learned conditional distributions** with parameters fitted to data  
 - **Metadata** about the fitting process (e.g., number of estimated PMFs)

## Key Features

 - **Access to Fitted Parameters**: Direct access to learned conditional distributions
 - **Model Evaluation**: Methods for assessing fit quality and making predictions
 - **Serialization**: Save and load fitted models
 - **Integration**: Works seamlessly with the broader BN ecosystem

## Usage Patterns

The `BNFit` class is primarily used for:

 - **Model Inspection**: Examining learned parameters and distributions
 - **Prediction**: Making probabilistic predictions on new data
 - **Model Persistence**: Saving fitted models for later use
 - **Model Comparison**: Comparing different fitted models

## Example Usage

```python
from causaliq_core.bn import BN, CPT
from causaliq_core.graph import DAG
import pandas as pd

# Create a BN structure
dag = DAG(['A', 'B', 'C'], [('A', 'B'), ('B', 'C')])
cnd_specs = {
    'A': CPT(values=['T', 'F']),
    'B': CPT(values=['T', 'F'], parents=['A']),  
    'C': CPT(values=['T', 'F'], parents=['B'])
}

bn = BN(dag, cnd_specs)

# Prepare training data
data = pd.DataFrame({
    'A': ['T', 'F', 'T', 'F', 'T'],
    'B': ['T', 'F', 'T', 'T', 'F'], 
    'C': ['T', 'F', 'T', 'T', 'F']
})

# Fit the model
fitted_bn = BN.fit(bn.dag, data)

# Access fitted distributions
print("Fitted CPT for node B:")
print(fitted_bn.cnds['B'])

# Examine model structure
print(f"Number of free parameters: {fitted_bn.free_params}")
print(f"Nodes: {list(fitted_bn.cnds.keys())}")
```

## Relationship to BN Class

The `BNFit` class is closely related to the `BN` class:

 - **BN**: Represents a network structure with specified or unspecified parameters
 - **BNFit**: Represents a network with parameters learned from data
 - **Conversion**: BNFit objects can be used wherever BN objects are expected

## API Reference

::: causaliq_core.bn.bnfit.BNFit
    options:
      show_source: false
      heading_level: 3