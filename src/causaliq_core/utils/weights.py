"""Metadata-driven weight computation utilities.

This module provides functions for computing weights from metadata using
a weight specification. Weights are computed as the product of matching
field-value weights, with a default of 1.0 for unspecified values.

Example weight specification::

    weight_spec = {
        "action": {
            "generate_graph": 1.0,
            "migrate_trace": 0.5,
        },
        "algorithm": {
            "pc": 1.0,
            "fci": 0.8,
        },
    }

An entry with ``action=migrate_trace`` and ``algorithm=fci`` receives
weight ``0.5 * 0.8 = 0.4``.
"""

from typing import Any, Dict


class WeightSpecError(Exception):
    """Exception raised for invalid weight specifications."""

    pass


def validate_weight_spec(weight_spec: Dict[str, Dict[str, float]]) -> None:
    """Validate a weight specification.

    Checks that the weight specification is well-formed:
    - Must be a dictionary
    - Keys must be strings (metadata field names)
    - Values must be dictionaries mapping field values to weights
    - Weights must be non-negative numbers

    Args:
        weight_spec: Mapping from metadata field to value-weight pairs.

    Raises:
        WeightSpecError: If the weight specification is invalid.

    Example:
        >>> validate_weight_spec({"action": {"pc": 1.0, "fci": 0.5}})
        >>> validate_weight_spec({"action": {"pc": -1.0}})
        Traceback (most recent call last):
        ...
        WeightSpecError: Weight for 'action.pc' must be non-negative, got -1.0
    """
    if not isinstance(weight_spec, dict):
        raise WeightSpecError(
            f"Weight specification must be a dictionary, "
            f"got {type(weight_spec).__name__}"
        )

    for field_name, value_weights in weight_spec.items():
        if not isinstance(field_name, str):
            raise WeightSpecError(
                f"Weight field name must be a string, "
                f"got {type(field_name).__name__}"
            )

        if not isinstance(value_weights, dict):
            raise WeightSpecError(
                f"Weight values for '{field_name}' must be a dictionary, "
                f"got {type(value_weights).__name__}"
            )

        for value, weight in value_weights.items():
            if not isinstance(weight, (int, float)):
                raise WeightSpecError(
                    f"Weight for '{field_name}.{value}' must be a number, "
                    f"got {type(weight).__name__}"
                )
            if weight < 0:
                raise WeightSpecError(
                    f"Weight for '{field_name}.{value}' must be "
                    f"non-negative, got {weight}"
                )


def compute_weight(
    metadata: Dict[str, Any],
    weight_spec: Dict[str, Dict[str, float]],
) -> float:
    """Compute a weight from metadata using a weight specification.

    The weight is computed as the product of all matching field-value
    weights. For fields in the weight specification that are not present
    in the metadata, or for values not in the weight specification, a
    default weight of 1.0 is used.

    Args:
        metadata: Dictionary of metadata field names to values.
        weight_spec: Mapping from metadata field to value-weight pairs.
            Each field maps to a dictionary of value-to-weight mappings.

    Returns:
        The computed weight (product of all matching weights).

    Example:
        >>> weight_spec = {
        ...     "action": {"generate_graph": 1.0, "migrate_trace": 0.5},
        ...     "algorithm": {"pc": 1.0, "fci": 0.8},
        ... }
        >>> compute_weight({"action": "migrate_trace", "algorithm": "fci"},
        ...                weight_spec)
        0.4
        >>> compute_weight({"action": "generate_graph"}, weight_spec)
        1.0
        >>> compute_weight({"other": "value"}, weight_spec)
        1.0
    """
    weight = 1.0

    for field_name, value_weights in weight_spec.items():
        if field_name in metadata:
            field_value = metadata[field_name]
            # Convert to string for lookup if needed (handles enums, etc.)
            lookup_key = (
                str(field_value)
                if not isinstance(field_value, str)
                else field_value
            )
            if lookup_key in value_weights:
                weight *= value_weights[lookup_key]

    return weight


def get_weight_fields(weight_spec: Dict[str, Dict[str, float]]) -> set:
    """Get the set of metadata field names used in a weight specification.

    Useful for validating that required metadata fields are present.

    Args:
        weight_spec: Mapping from metadata field to value-weight pairs.

    Returns:
        Set of field names referenced in the weight specification.

    Example:
        >>> weight_spec = {
        ...     "action": {"generate_graph": 1.0},
        ...     "algorithm": {"pc": 1.0},
        ... }
        >>> get_weight_fields(weight_spec)
        {'action', 'algorithm'}
    """
    return set(weight_spec.keys())
