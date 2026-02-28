"""Tests for metadata-driven weight computation utilities."""

import pytest

from causaliq_core.utils.weights import (
    WeightSpecError,
    compute_weight,
    get_weight_fields,
    validate_weight_spec,
)


# Test validate_weight_spec accepts valid specifications.
def test_validate_weight_spec_valid() -> None:
    validate_weight_spec({})
    validate_weight_spec({"action": {}})
    validate_weight_spec({"action": {"pc": 1.0}})
    validate_weight_spec({"action": {"pc": 1.0, "fci": 0.5}})
    validate_weight_spec(
        {
            "action": {"generate_graph": 1.0, "migrate_trace": 0.5},
            "algorithm": {"pc": 1.0, "fci": 0.8},
        }
    )


# Test validate_weight_spec accepts zero weights.
def test_validate_weight_spec_zero_weight() -> None:
    validate_weight_spec({"action": {"disabled": 0.0}})


# Test validate_weight_spec accepts integer weights.
def test_validate_weight_spec_integer_weight() -> None:
    validate_weight_spec({"action": {"pc": 1, "fci": 2}})


# Test validate_weight_spec rejects non-dict top-level.
def test_validate_weight_spec_not_dict() -> None:
    with pytest.raises(WeightSpecError, match="must be a dictionary"):
        validate_weight_spec("not a dict")  # type: ignore
    with pytest.raises(WeightSpecError, match="must be a dictionary"):
        validate_weight_spec([{"action": {"pc": 1.0}}])  # type: ignore


# Test validate_weight_spec rejects non-string field names.
def test_validate_weight_spec_non_string_field() -> None:
    with pytest.raises(WeightSpecError, match="field name must be a string"):
        validate_weight_spec({123: {"pc": 1.0}})  # type: ignore


# Test validate_weight_spec rejects non-dict value mappings.
def test_validate_weight_spec_non_dict_values() -> None:
    with pytest.raises(WeightSpecError, match="must be a dictionary"):
        validate_weight_spec({"action": "not a dict"})  # type: ignore
    with pytest.raises(WeightSpecError, match="must be a dictionary"):
        validate_weight_spec({"action": 1.0})  # type: ignore


# Test validate_weight_spec rejects non-numeric weights.
def test_validate_weight_spec_non_numeric_weight() -> None:
    with pytest.raises(WeightSpecError, match="must be a number"):
        validate_weight_spec({"action": {"pc": "high"}})  # type: ignore
    with pytest.raises(WeightSpecError, match="must be a number"):
        validate_weight_spec({"action": {"pc": None}})  # type: ignore


# Test validate_weight_spec rejects negative weights.
def test_validate_weight_spec_negative_weight() -> None:
    with pytest.raises(WeightSpecError, match="non-negative"):
        validate_weight_spec({"action": {"pc": -0.5}})
    with pytest.raises(WeightSpecError, match="non-negative"):
        validate_weight_spec({"action": {"pc": -1}})


# Test compute_weight with empty weight spec.
def test_compute_weight_empty_spec() -> None:
    assert compute_weight({"action": "pc"}, {}) == 1.0


# Test compute_weight with empty metadata.
def test_compute_weight_empty_metadata() -> None:
    assert compute_weight({}, {"action": {"pc": 0.5}}) == 1.0


# Test compute_weight with single matching field.
def test_compute_weight_single_field() -> None:
    weight_spec = {"action": {"pc": 0.5, "fci": 0.8}}
    assert compute_weight({"action": "pc"}, weight_spec) == 0.5
    assert compute_weight({"action": "fci"}, weight_spec) == 0.8


# Test compute_weight with multiple matching fields.
def test_compute_weight_multiple_fields() -> None:
    weight_spec = {
        "action": {"generate_graph": 1.0, "migrate_trace": 0.5},
        "algorithm": {"pc": 1.0, "fci": 0.8},
    }
    # Both fields match
    result = compute_weight(
        {"action": "migrate_trace", "algorithm": "fci"}, weight_spec
    )
    assert result == pytest.approx(0.4)  # 0.5 * 0.8

    # Only action matches
    result = compute_weight(
        {"action": "migrate_trace", "algorithm": "ges"}, weight_spec
    )
    assert result == pytest.approx(0.5)

    # Only algorithm matches
    result = compute_weight(
        {"action": "unknown", "algorithm": "fci"}, weight_spec
    )
    assert result == pytest.approx(0.8)


# Test compute_weight with metadata field not in spec.
def test_compute_weight_unspecified_field() -> None:
    weight_spec = {"action": {"pc": 0.5}}
    # Field not in weight spec - default weight 1.0
    assert compute_weight({"other": "value"}, weight_spec) == 1.0


# Test compute_weight with value not in spec.
def test_compute_weight_unspecified_value() -> None:
    weight_spec = {"action": {"pc": 0.5, "fci": 0.8}}
    # Value not in weight spec - default weight 1.0
    assert compute_weight({"action": "ges"}, weight_spec) == 1.0


# Test compute_weight with zero weight.
def test_compute_weight_zero() -> None:
    weight_spec = {"action": {"disabled": 0.0, "enabled": 1.0}}
    assert compute_weight({"action": "disabled"}, weight_spec) == 0.0
    assert compute_weight({"action": "enabled"}, weight_spec) == 1.0


# Test compute_weight converts non-string values to string for lookup.
def test_compute_weight_non_string_value() -> None:
    weight_spec = {"sample_size": {"100": 0.5, "1000": 1.0}}
    assert compute_weight({"sample_size": 100}, weight_spec) == 0.5
    assert compute_weight({"sample_size": 1000}, weight_spec) == 1.0


# Test compute_weight with extra metadata fields.
def test_compute_weight_extra_metadata() -> None:
    weight_spec = {"action": {"pc": 0.5}}
    metadata = {"action": "pc", "network": "asia", "seed": 42}
    assert compute_weight(metadata, weight_spec) == 0.5


# Test get_weight_fields with empty spec.
def test_get_weight_fields_empty() -> None:
    assert get_weight_fields({}) == set()


# Test get_weight_fields with single field.
def test_get_weight_fields_single() -> None:
    assert get_weight_fields({"action": {"pc": 1.0}}) == {"action"}


# Test get_weight_fields with multiple fields.
def test_get_weight_fields_multiple() -> None:
    weight_spec = {
        "action": {"generate_graph": 1.0},
        "algorithm": {"pc": 1.0},
        "network": {"asia": 1.0},
    }
    assert get_weight_fields(weight_spec) == {"action", "algorithm", "network"}


# Test compute_weight example from docstring.
def test_compute_weight_docstring_example() -> None:
    weight_spec = {
        "action": {"generate_graph": 1.0, "migrate_trace": 0.5},
        "algorithm": {"pc": 1.0, "fci": 0.8},
    }
    result = compute_weight(
        {"action": "migrate_trace", "algorithm": "fci"}, weight_spec
    )
    assert result == pytest.approx(0.4)

    result = compute_weight({"action": "generate_graph"}, weight_spec)
    assert result == pytest.approx(1.0)

    result = compute_weight({"other": "value"}, weight_spec)
    assert result == pytest.approx(1.0)
