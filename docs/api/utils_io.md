# I/O Operations

The I/O utilities module provides enhanced file and path handling functionality, including robust path validation and DataFrame writing with advanced formatting options.

## Overview

The `causaliq_core.utils.io` module provides:

 - **Path Validation**: Robust checking of file and directory paths
 - **Enhanced DataFrame Writing**: CSV output with compression and numerical formatting
 - **Cross-Platform Support**: Consistent behavior across operating systems
 - **Error Handling**: Clear error messages for common I/O issues

## Functions

### is_valid_path()

Validates that a path exists and matches the expected type (file or directory).

```python
from causaliq_core.utils.io import is_valid_path

# Check if file exists
if is_valid_path('data/network.dsc', is_file=True):
    print("File exists and is accessible")

# Check if directory exists  
if is_valid_path('output/', is_file=False):
    print("Directory exists and is accessible")

# Default behavior checks for file
try:
    is_valid_path('important_file.txt')
    print("File is valid")
except FileNotFoundError:
    print("File not found")
```

**Parameters:**

 - `path` (str): Full path to validate
 - `is_file` (bool): Whether path should be a file (True) or directory (False)

**Returns:**

 - `bool`: True if path exists and matches expected type

**Raises:**

 - `TypeError`: If arguments have invalid types
 - `FileNotFoundError`: If path doesn't exist or doesn't match expected type

### write_dataframe()

Enhanced DataFrame writing with numerical formatting, compression, and validation.

```python
from causaliq_core.utils.io import write_dataframe
import pandas as pd

# Create sample data
df = pd.DataFrame({
    'measurement': [1.234567, 2.789012, 3.456789],
    'category': ['A', 'B', 'C'],
    'value': [10.123456789, 20.987654321, 30.555555555]
})

# Basic usage
write_dataframe(df, 'output.csv')

# With numerical formatting (3 significant figures)
write_dataframe(df, 'formatted.csv', sf=3)

# With compression
write_dataframe(df, 'compressed.csv.gz', compress=True)

# Preserve original DataFrame (default)
write_dataframe(df, 'output.csv', preserve=True)

# Modify DataFrame in-place (faster for large data)
write_dataframe(df, 'output.csv', preserve=False)

# Custom zero threshold
write_dataframe(df, 'output.csv', sf=4, zero=1e-6)
```

**Parameters:**

 - `df` (DataFrame): Pandas DataFrame to write
 - `filename` (str): Output file path
 - `compress` (bool): Whether to gzip compress the output (default: False)
 - `sf` (int): Number of significant figures for numerical formatting (default: 10)
 - `zero` (float, optional): Values below this threshold are treated as zero (default: 10^(-sf))
 - `preserve` (bool): Whether to preserve original DataFrame unchanged (default: True)

**Returns:**

 - None

**Raises:**

 - `TypeError`: If arguments have invalid types
 - `ValueError`: If sf or zero parameters are out of valid ranges
 - `FileNotFoundError`: If destination directory doesn't exist

## Features

### Numerical Formatting

The `write_dataframe()` function provides sophisticated numerical formatting:

```python
import pandas as pd
from causaliq_core.utils.io import write_dataframe

# Data with varying precision
df = pd.DataFrame({
    'high_precision': [1.23456789012345, 2.98765432109876],
    'low_precision': [1.2, 3.4],
    'scientific': [1.23e-8, 4.56e12]
})

# Format to 3 significant figures
write_dataframe(df, 'formatted.csv', sf=3)
# Results: 1.23, 2.99, 1.20, 3.40, 1.23e-08, 4.56e+12
```

### Compression Support

Automatic compression for large datasets:

```python
# Large dataset
large_df = pd.DataFrame({
    'data': range(100000),
    'values': [random.random() for _ in range(100000)]
})

# Compressed output (much smaller file size)
write_dataframe(large_df, 'large_data.csv.gz', compress=True)
```

### Memory Efficiency

Control memory usage with the `preserve` parameter:

```python
# For large DataFrames, avoid copying
write_dataframe(huge_df, 'output.csv', preserve=False)
# Original DataFrame may be modified for efficiency

# For small DataFrames, preserve original
write_dataframe(small_df, 'output.csv', preserve=True)  # Default
# Original DataFrame remains unchanged
```

## Error Handling

The I/O utilities provide comprehensive error handling:

```python
from causaliq_core.utils.io import write_dataframe, is_valid_path

# Handle path validation errors
try:
    is_valid_path('nonexistent/path.txt')
except FileNotFoundError as e:
    print(f"Path error: {e}")

# Handle DataFrame writing errors
try:
    write_dataframe(df, '/invalid/path/output.csv')
except FileNotFoundError:
    print("Destination directory doesn't exist")

try:
    write_dataframe(df, 'output.csv', sf=50)  # Invalid sf
except ValueError as e:
    print(f"Parameter error: {e}")
```

## Usage Patterns

### Data Pipeline Integration

```python
from causaliq_core.utils.io import write_dataframe, is_valid_path
import pandas as pd
from pathlib import Path

def save_analysis_results(df, output_dir, filename, compress_large=True):
    """Save analysis results with appropriate formatting."""
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Full output path
    full_path = output_path / filename
    
    # Determine if compression is needed
    should_compress = compress_large and len(df) > 10000
    if should_compress:
        full_path = full_path.with_suffix('.csv.gz')
    
    # Write with appropriate settings
    write_dataframe(
        df, 
        str(full_path),
        compress=should_compress,
        sf=4,  # 4 significant figures for analysis data
        preserve=True  # Keep original data unchanged
    )
    
    print(f"Results saved to {full_path}")
    return full_path
```

### Validation Workflow

```python
from causaliq_core.utils.io import is_valid_path

def validate_inputs(file_paths):
    """Validate all required input files exist."""
    
    missing_files = []
    for path in file_paths:
        try:
            is_valid_path(path, is_file=True)
        except FileNotFoundError:
            missing_files.append(path)
    
    if missing_files:
        raise FileNotFoundError(f"Missing required files: {missing_files}")
    
    print("All input files validated successfully")
```

## API Reference

::: causaliq_core.utils.io
    options:
      show_source: false
      heading_level: 3