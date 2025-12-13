# Bayesian Network I/O

The I/O module provides functionality for reading and writing Bayesian Networks in various standard formats. This enables interoperability with other tools and persistence of network models.

## Overview

The `causaliq_core.bn.io` module supports multiple file formats commonly used for Bayesian Networks:

 - **DSC Format**: CausalIQ's native format for network specification
 - **XDSL Format**: GeNIe/SMILE's XML-based format for complete networks
 - **Common Interface**: Unified functions for format-agnostic I/O operations

## Supported Formats

### [DSC Format](bn_io_dsc.md)
A text-based format for specifying Bayesian Network structures and parameters.

**Features:**

 - Human-readable network specification
 - Support for both discrete and continuous distributions  
 - Compact representation of network structure
 - Easy manual editing and version control

### [XDSL Format](bn_io_xdsl.md)  
An XML-based format used by GeNIe and SMILE software.

**Features:**

 - Complete network serialization including visual layout
 - Industry-standard format for tool interoperability
 - Support for complex network metadata
 - Preservation of all network properties

## Main Functions

The module provides convenient top-level functions:

```python
from causaliq_core.bn.io import read_bn, write_bn

# Read BN from file (format auto-detected)
bn = read_bn('network.dsc')     # DSC format
bn = read_bn('network.xdsl')    # XDSL format

# Write BN to file (format determined by extension)  
write_bn(bn, 'output.dsc')      # Save as DSC
write_bn(bn, 'output.xdsl')     # Save as XDSL
```

## Format Detection

The I/O system automatically detects formats based on:

 - **File Extension**: `.dsc` for DSC format, `.xdsl` for XDSL format
 - **Content Analysis**: Inspection of file headers and structure
 - **Explicit Specification**: Manual format specification when needed

## Usage Patterns

### Loading Networks

```python
from causaliq_core.bn.io import read_bn

# Load from different formats
dsc_network = read_bn('models/weather.dsc')
xdsl_network = read_bn('models/medical.xdsl') 

# Verify loaded network
print(f"Nodes: {list(dsc_network.dag.nodes)}")
print(f"Edges: {list(dsc_network.dag.edges)}")
```

### Saving Networks

```python
from causaliq_core.bn.io import write_bn
from causaliq_core.bn import BN

# Create or modify network
# ... bn creation code ...

# Save in different formats
write_bn(bn, 'output/final_model.dsc')     # DSC format
write_bn(bn, 'output/final_model.xdsl')    # XDSL format

# Backup with timestamp
import datetime
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
write_bn(bn, f'backups/model_{timestamp}.dsc')
```

### Format Conversion

```python
from causaliq_core.bn.io import read_bn, write_bn

# Convert between formats
bn = read_bn('input.dsc')       # Read DSC
write_bn(bn, 'output.xdsl')     # Write XDSL

# Batch conversion
import glob
for dsc_file in glob.glob('*.dsc'):
    bn = read_bn(dsc_file)
    xdsl_file = dsc_file.replace('.dsc', '.xdsl')
    write_bn(bn, xdsl_file)
```

## Error Handling

The I/O system provides robust error handling:

 - **Format Validation**: Checks for valid file formats and structure
 - **Parse Errors**: Clear messages for syntax and content errors
 - **Missing Files**: Helpful error messages for file access issues
 - **Recovery**: Graceful handling of partial or corrupted files

## Performance Considerations

 - **Lazy Loading**: Large networks are loaded efficiently
 - **Memory Management**: Minimal memory footprint during I/O operations
 - **Streaming**: Support for large files that don't fit in memory
 - **Caching**: Intelligent caching of frequently accessed networks

## API Reference

::: causaliq_core.bn.io
    options:
      show_source: false
      heading_level: 3