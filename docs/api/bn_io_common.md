# Common I/O Interface

The common I/O interface provides unified functions for reading and writing Bayesian Networks regardless of file format. These functions automatically detect formats and route to the appropriate format-specific handlers.

## Overview

The common interface simplifies BN I/O by providing:

 - **Format Auto-Detection**: Automatically determines file format from extension and content
 - **Unified API**: Same functions work with all supported formats
 - **Error Handling**: Consistent error reporting across formats
 - **Format Conversion**: Easy conversion between different formats

## Main Functions

### read_bn()

The primary function for loading Bayesian Networks from files:

```python
from causaliq_core.bn.io import read_bn

# Auto-detect format from extension
bn_dsc = read_bn('network.dsc')     # DSC format
bn_xdsl = read_bn('network.xdsl')   # XDSL format

# Explicit format specification (optional)
bn = read_bn('network.txt', format='dsc')
```

### write_bn()

The primary function for saving Bayesian Networks to files:

```python
from causaliq_core.bn.io import write_bn

# Auto-detect format from extension
write_bn(bn, 'output.dsc')      # Saves as DSC
write_bn(bn, 'output.xdsl')     # Saves as XDSL

# Explicit format specification (optional)
write_bn(bn, 'output.txt', format='dsc')
```

## Format Detection

The system determines file format using:

### Extension-Based Detection

 - `.dsc` → DSC format
 - `.xdsl` → XDSL format
 - Unknown extensions → Content-based detection

### Content-Based Detection

For files without clear extensions:

```python
# System examines file content
bn = read_bn('network')  # No extension

# Looks for:
# - XML headers → XDSL format  
# - DSC syntax → DSC format
# - Fallback to default format
```

## Error Handling

The common interface provides consistent error handling:

```python
from causaliq_core.bn.io import read_bn, write_bn
from causaliq_core.bn.io.common import FileFormatError

try:
    bn = read_bn('nonexistent.dsc')
except FileNotFoundError:
    print("File not found")
    
try:
    bn = read_bn('invalid.dsc')  
except FileFormatError as e:
    print(f"Format error: {e}")
    
try:
    write_bn(invalid_bn, 'output.dsc')
except ValueError as e:
    print(f"Invalid network: {e}")
```

## Usage Examples

### Basic File Operations

```python
from causaliq_core.bn.io import read_bn, write_bn

# Load network
original_bn = read_bn('input/network.dsc')

# Perform analysis or modifications
# ... network operations ...

# Save results
write_bn(modified_bn, 'output/result.dsc')
```

### Format Conversion

```python
from causaliq_core.bn.io import read_bn, write_bn

# Convert DSC to XDSL
bn = read_bn('network.dsc')
write_bn(bn, 'network.xdsl')

# Convert XDSL to DSC
bn = read_bn('genie_network.xdsl') 
write_bn(bn, 'causaliq_network.dsc')

# Batch conversion
import glob
for dsc_file in glob.glob('*.dsc'):
    bn = read_bn(dsc_file)
    xdsl_file = dsc_file.replace('.dsc', '.xdsl')
    write_bn(bn, xdsl_file)
```

### Robust File Handling

```python
from pathlib import Path
from causaliq_core.bn.io import read_bn, write_bn

def safe_load_bn(filename):
    """Safely load BN with error handling."""
    try:
        path = Path(filename)
        if not path.exists():
            raise FileNotFoundError(f"Network file not found: {filename}")
            
        bn = read_bn(filename)
        print(f"Successfully loaded network with {len(bn.dag.nodes)} nodes")
        return bn
        
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None

def safe_save_bn(bn, filename, backup=True):
    """Safely save BN with optional backup."""
    try:
        path = Path(filename)
        
        # Create backup if file exists
        if backup and path.exists():
            backup_path = path.with_suffix(path.suffix + '.backup')
            path.rename(backup_path)
            
        write_bn(bn, filename)
        print(f"Successfully saved network to {filename}")
        
    except Exception as e:
        print(f"Error saving {filename}: {e}")
```

## Format-Specific Options

While the common interface handles most cases, format-specific options are available:

```python
from causaliq_core.bn.io.dsc import read_dsc, write_dsc
from causaliq_core.bn.io.xdsl import read_xdsl, write_xdsl

# DSC-specific options
bn = read_dsc('network.dsc', strict_validation=True)
write_dsc(bn, 'output.dsc', include_comments=True)

# XDSL-specific options  
bn = read_xdsl('network.xdsl', preserve_layout=True)
write_xdsl(bn, 'output.xdsl', genie_compatible=True)
```

## Performance Considerations

 - **Large Files**: Streaming support for very large networks
 - **Memory Usage**: Efficient parsing without loading entire file into memory
 - **Validation**: Optional validation can be disabled for faster loading
 - **Caching**: Intelligent caching for frequently accessed files

## File Path Handling

The interface supports various path formats:

```python
from pathlib import Path

# String paths
bn = read_bn('data/network.dsc')

# Path objects
path = Path('data') / 'network.dsc'
bn = read_bn(path)

# Absolute paths
bn = read_bn('/full/path/to/network.dsc')

# Relative paths
bn = read_bn('../networks/model.xdsl')
```

## Integration Examples

### With Data Pipelines

```python
def process_network_batch(input_dir, output_dir):
    """Process multiple networks."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for network_file in input_path.glob('*.dsc'):
        bn = read_bn(network_file)
        
        # Process network (fit parameters, analyze, etc.)
        processed_bn = process_network(bn)
        
        # Save result
        output_file = output_path / network_file.name
        write_bn(processed_bn, output_file)
```

### With Configuration Management

```python
import yaml
from causaliq_core.bn.io import read_bn

def load_network_config(config_file):
    """Load network based on configuration."""
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    network_file = config['network']['file']
    bn = read_bn(network_file)
    
    return bn, config
```

## API Reference

::: causaliq_core.bn.io.common
    options:
      show_source: false
      heading_level: 3