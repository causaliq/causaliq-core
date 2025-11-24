# Mathematical Functions

Mathematical utility functions for number formatting and logarithm calculations.

::: causaliq_core.utils.rndsf
    options:
      show_source: false

::: causaliq_core.utils.ln
    options:
      show_source: false

## Usage Examples

### Significant Figure Rounding

```python
from causaliq_core.utils import rndsf

# Basic rounding
rndsf(1.23456789, 4)  # Returns '1.235'

# Small numbers
rndsf(0.000123, 3)    # Returns '0.000123'

# Large numbers  
rndsf(1234567, 3)     # Returns '1230000.0'

# Custom zero threshold
rndsf(0.0001, 3, zero=0.001)  # Returns '0.0'
```

### Logarithm Calculations

```python
from causaliq_core.utils import ln

# Base 10 logarithm
ln(10, 10)  # Returns 1.0

# Base 2 logarithm
ln(8, 2)    # Returns 3.0

# Natural logarithm (default)
ln(2.718281828459045)  # Returns 1.0
ln(2.718281828459045, 'e')  # Same as above
```