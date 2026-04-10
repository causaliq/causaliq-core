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

::: causaliq_core.utils.resolve_random_calls
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

Allowed functions: `len`, `str`, `int`, `float`, `bool`, `abs`,
`min`, `max`, `random`

### Random Sampling

The `random(count, seed)` function enables reproducible random
selection within filter expressions. When used as
`VAR in random(count, seed)`, it selects *count* values from the
distinct population of `VAR` across all entries, using a
hardware-stable random sequence.

```python
from causaliq_core.utils import filter_entries

entries = [
    {"seed": 1, "network": "asia"},
    {"seed": 5, "network": "asia"},
    {"seed": 10, "network": "asia"},
    {"seed": 15, "network": "asia"},
]

# Select 2 random seeds (deterministic with seed=42)
result = filter_entries(
    entries, "seed in random(2, 42)"
)
# Returns 2 entries with reproducibly chosen seed values
```

`random()` calls are pre-resolved by `resolve_random_calls()` before
expression evaluation, replacing them with concrete value sets.
Use `filter_entries()` for automatic resolution, or call
`resolve_random_calls()` directly for manual control.

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

### Random Sampling in Workflows

```yaml
steps:
  - name: "Evaluate Subset"
    uses: "causaliq-analysis"
    with:
      action: "evaluate_graph"
      input: "results/graphs.db"
      filter: "seed in random(5, 42)"
      output: "results/evaluation.db"
```

This selects 5 random seed values (deterministically with seed 42)
from the input cache entries.
