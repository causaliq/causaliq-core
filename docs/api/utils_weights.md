# Weight Computation Utilities

Metadata-driven weight computation for aggregation operations in workflows.

This module provides functions for computing weights from metadata using
a weight specification. Weights are computed as the product of matching
field-value weights, with a default of 1.0 for unspecified values.

## Core Functions

::: causaliq_core.utils.compute_weight
    options:
      show_source: false

::: causaliq_core.utils.validate_weight_spec
    options:
      show_source: false

::: causaliq_core.utils.get_weight_fields
    options:
      show_source: false

## Exceptions

::: causaliq_core.utils.WeightSpecError
    options:
      show_source: false

## Weight Specification Format

Weight specifications are dictionaries mapping metadata field names to
value-weight pairs:

```python
weight_spec = {
    "field_name": {
        "value1": 1.0,
        "value2": 0.5,
    },
    "another_field": {
        "valueA": 0.8,
        "valueB": 1.2,
    },
}
```

### Weight Calculation

The final weight is the **product** of all matching field-value weights:

- If a metadata field is in the weight spec and its value matches, that
  weight is multiplied into the result
- If a field is not in metadata, or value is not in the spec, weight 1.0
  is used (no effect on product)

## Usage Examples

### Basic Weight Computation

```python
from causaliq_core.utils import compute_weight

weight_spec = {
    "action": {"generate_graph": 1.0, "migrate_trace": 0.5},
    "algorithm": {"pc": 1.0, "fci": 0.8},
}

# Both fields match
metadata = {"action": "migrate_trace", "algorithm": "fci"}
compute_weight(metadata, weight_spec)  # 0.5 * 0.8 = 0.4

# Only action matches
metadata = {"action": "migrate_trace", "algorithm": "ges"}
compute_weight(metadata, weight_spec)  # 0.5 * 1.0 = 0.5

# No matches - default weight
metadata = {"network": "asia"}
compute_weight(metadata, weight_spec)  # 1.0
```

### Validating Weight Specifications

```python
from causaliq_core.utils import validate_weight_spec, WeightSpecError

# Valid specification
validate_weight_spec({"action": {"pc": 1.0, "fci": 0.5}})  # OK

# Invalid - negative weight
try:
    validate_weight_spec({"action": {"pc": -1.0}})
except WeightSpecError as e:
    print(f"Invalid: {e}")
```

### Getting Weight Fields

```python
from causaliq_core.utils import get_weight_fields

weight_spec = {
    "action": {"generate_graph": 1.0},
    "algorithm": {"pc": 1.0},
}

fields = get_weight_fields(weight_spec)
print(fields)  # {'action', 'algorithm'}
```

## Workflow Integration

Weight specifications are used in workflow configurations for aggregation:

```yaml
actions:
  merge_graphs:
    input: discovery_results.db
    weights:
      action:
        generate_graph: 1.0
        migrate_trace: 0.5
      algorithm:
        pc: 1.0
        fci: 0.8
    output: merged_graphs.db
```

Entries are weighted during aggregation based on their metadata values.
This enables flexible weighting by source action, algorithm, sample size,
or any other metadata field.
