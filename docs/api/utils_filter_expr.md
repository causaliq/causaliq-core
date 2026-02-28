# Filter Expression Utilities

Safe filter expression evaluation for metadata filtering in workflows
and aggregation operations.

This module provides functions for evaluating Python-like filter expressions
against metadata dictionaries using the `simpleeval` library for safe
evaluation without security risks of `eval()`.

## Core Functions

::: causaliq_core.utils.evaluate_filter
    options:
      show_source: false

::: causaliq_core.utils.validate_filter
    options:
      show_source: false

::: causaliq_core.utils.get_filter_variables
    options:
      show_source: false

::: causaliq_core.utils.filter_entries
    options:
      show_source: false

## Exceptions

::: causaliq_core.utils.FilterExpressionError
    options:
      show_source: false

::: causaliq_core.utils.FilterSyntaxError
    options:
      show_source: false

## Expression Syntax

Filter expressions use Python syntax with the following supported operators:

| Category | Operators |
|----------|-----------|
| Comparison | `==`, `!=`, `>`, `<`, `>=`, `<=` |
| Boolean | `and`, `or`, `not` |
| Membership | `in` |
| Grouping | `()` |

Allowed functions: `len`, `str`, `int`, `float`, `bool`, `abs`, `min`, `max`

## Usage Examples

### Basic Filtering

```python
from causaliq_core.utils import evaluate_filter

metadata = {"network": "asia", "sample_size": 1000, "status": "completed"}

# Simple equality
evaluate_filter("network == 'asia'", metadata)  # True

# Numeric comparison
evaluate_filter("sample_size >= 500", metadata)  # True

# Boolean combination
evaluate_filter("network == 'asia' and sample_size > 500", metadata)  # True
```

### Validating Expressions

```python
from causaliq_core.utils import validate_filter, FilterSyntaxError

# Valid expression
validate_filter("x > 5 and y == 'value'")  # No exception

# Invalid syntax
try:
    validate_filter("x ==")  # Missing right operand
except FilterSyntaxError as e:
    print(f"Invalid: {e}")
```

### Extracting Variables

```python
from causaliq_core.utils import get_filter_variables

# Get variables referenced in expression
vars = get_filter_variables("network == 'asia' and sample_size > 500")
print(vars)  # {'network', 'sample_size'}
```

### Filtering Collections

```python
from causaliq_core.utils import filter_entries

entries = [
    {"network": "asia", "sample_size": 100},
    {"network": "asia", "sample_size": 1000},
    {"network": "alarm", "sample_size": 500},
]

# Filter to asia entries with sample_size > 500
result = filter_entries(entries, "network == 'asia' and sample_size > 500")
# Returns: [{"network": "asia", "sample_size": 1000}]
```

## Workflow Integration

Filter expressions are commonly used in workflow configurations:

```yaml
actions:
  merge_graphs:
    input: discovery_results.db
    filter: network == 'asia' and status == 'completed'
    output: merged_graphs.db
```

The filter is applied to cache entry metadata before aggregation.
