# XDSL Format I/O

The XDSL format is an XML-based format used by GeNIe and SMILE software for representing complete Bayesian Networks. It provides comprehensive serialization including network structure, parameters, and visual layout information.

## Overview

XDSL (eXtended Decision Structures Language) files contain:

 - **Complete Network Definition**: All nodes, relationships, and parameters
 - **Visual Layout**: Node positions, colors, and graphical properties  
 - **Metadata**: Network properties, documentation, and annotations
 - **Tool Integration**: Full compatibility with GeNIe/SMILE software

## Key Features

 - **Industry Standard**: Widely supported format for Bayesian Network tools
 - **Complete Serialization**: Preserves all network properties and metadata
 - **Visual Information**: Maintains graphical layout and presentation
 - **Tool Interoperability**: Exchange networks with other BN software
 - **Rich Metadata**: Support for detailed network documentation

## Reading XDSL Files

```python
from causaliq_core.bn.io import read_bn

# Read XDSL file created by GeNIe or other tools
bn = read_bn('network.xdsl')

# Access network structure
print(f"Loaded network with {len(bn.dag.nodes)} nodes")
print(f"Nodes: {list(bn.dag.nodes)}")
print(f"Edges: {list(bn.dag.edges)}")

# Examine distributions
for node_name, cnd in bn.cnds.items():
    print(f"Node '{node_name}' has {cnd.param_count} parameters")
```

## Writing XDSL Files

```python
from causaliq_core.bn.io import write_bn
from causaliq_core.bn import BN, CPT
from causaliq_core.graph import DAG

# Create network
dag = DAG(['Disease', 'Symptom1', 'Symptom2'], 
          [('Disease', 'Symptom1'), ('Disease', 'Symptom2')])

cnd_specs = {
    'Disease': CPT(values=['Present', 'Absent'], table=[0.01, 0.99]),
    'Symptom1': CPT(values=['Yes', 'No'], 
                    table=[0.9, 0.1, 0.05, 0.95], 
                    parents=['Disease']),
    'Symptom2': CPT(values=['Yes', 'No'],
                    table=[0.8, 0.2, 0.02, 0.98],
                    parents=['Disease'])
}

bn = BN(dag, cnd_specs)

# Write to XDSL format (can be opened in GeNIe)
write_bn(bn, 'medical_diagnosis.xdsl')
```

## XDSL File Structure

A typical XDSL file contains XML sections like:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<smile version="1.0" id="Network" numsamples="10000">
  <nodes>
    <cpt id="Disease">
      <state id="Present" />
      <state id="Absent" />
      <probabilities>0.01 0.99</probabilities>
    </cpt>
    
    <cpt id="Symptom1">
      <state id="Yes" />
      <state id="No" />
      <parents>Disease</parents>
      <probabilities>0.9 0.1 0.05 0.95</probabilities>
    </cpt>
  </nodes>
  
  <extensions>
    <genie version="1.0" app="GeNIe">
      <node id="Disease">
        <name>Disease Status</name>
        <interior color="e5f6f7" />
        <outline color="000080" />
        <font color="000000" name="Arial" size="8" />
        <position>100 50 180 90</position>
      </node>
    </genie>
  </extensions>
</smile>
```

## Supported Elements

### Node Types

The XDSL reader/writer supports:

 - **CPT Nodes**: Discrete nodes with conditional probability tables
 - **Continuous Nodes**: Linear Gaussian nodes (limited support)
 - **Decision Nodes**: For influence diagrams (where supported)
 - **Utility Nodes**: For decision analysis (where supported)

### Network Properties

 - **Node States**: Discrete value labels and continuous ranges
 - **Probability Tables**: Full CPT specifications  
 - **Parent Relationships**: Conditional dependency structure
 - **Network Metadata**: Names, descriptions, and annotations

## Interoperability Examples

### From GeNIe to CausalIQ

```python
from causaliq_core.bn.io import read_bn

# Read network created in GeNIe
bn = read_bn('genie_network.xdsl')

# Use in CausalIQ analysis
marginals = bn.marginals(['NodeA', 'NodeB'])
print("Marginal probabilities:")
print(marginals)

# Perform inference
posterior = bn.conditional(['Disease'], ['Symptom1'], 'Yes')
print(f"P(Disease | Symptom1=Yes): {posterior}")
```

### From CausalIQ to GeNIe

```python
from causaliq_core.bn import BN
from causaliq_core.bn.io import write_bn

# Create network in CausalIQ
# ... network creation code ...

# Export for GeNIe
write_bn(bn, 'for_genie.xdsl')

# File can now be opened and edited in GeNIe software
# Visual layout and additional properties can be added
```

## Advanced Features

### Visual Layout Preservation

When reading XDSL files with visual information:

```python
# Read network with layout information
bn = read_bn('visual_network.xdsl')

# Layout information is preserved in metadata
# (Access depends on specific implementation)
```

### Metadata Handling

```python
# XDSL files can contain rich metadata
bn = read_bn('documented_network.xdsl')

# Access network documentation
# (Implementation-specific metadata access)
```

## Format Limitations

Current XDSL support has some limitations:

 - **Continuous Nodes**: Limited support for complex continuous distributions
 - **Visual Elements**: Layout information may not be fully preserved
 - **Extensions**: Some GeNIe-specific extensions may not be supported
 - **Decision Networks**: Influence diagrams have limited support

## Error Handling

The XDSL parser handles common issues:

 - **Invalid XML**: Clear error messages for malformed XML
 - **Missing Elements**: Detection of incomplete network definitions
 - **Version Compatibility**: Handling of different XDSL versions
 - **Encoding Issues**: Robust handling of character encodings

## Performance Notes

 - **Large Networks**: Efficient parsing of networks with many nodes
 - **Memory Usage**: Optimized memory usage during parsing
 - **Validation**: Optional validation for faster loading
 - **Streaming**: Support for large XDSL files

## API Reference

::: causaliq_core.bn.io.xdsl
    options:
      show_source: false
      heading_level: 3