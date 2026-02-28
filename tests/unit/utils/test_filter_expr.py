"""Tests for filter expression evaluation utilities."""

import pytest
from pytest_mock import MockerFixture

from causaliq_core.utils.filter_expr import (
    FilterExpressionError,
    FilterSyntaxError,
    evaluate_filter,
    filter_entries,
    get_filter_variables,
    validate_filter,
)


# Test validate_filter with valid expressions.
def test_validate_filter_valid_expressions() -> None:
    validate_filter("x == 1")
    validate_filter("name == 'asia'")
    validate_filter("a > 5 and b < 10")
    validate_filter("x in [1, 2, 3]")
    validate_filter("(a or b) and c")
    validate_filter("not x")


# Test validate_filter raises FilterSyntaxError for invalid syntax.
def test_validate_filter_invalid_syntax() -> None:
    with pytest.raises(FilterSyntaxError):
        validate_filter("x ==")
    with pytest.raises(FilterSyntaxError):
        validate_filter("== x")
    with pytest.raises(FilterSyntaxError):
        validate_filter("x &&& y")


# Test validate_filter raises FilterSyntaxError for empty expression.
def test_validate_filter_empty_expression() -> None:
    with pytest.raises(FilterSyntaxError):
        validate_filter("")
    with pytest.raises(FilterSyntaxError):
        validate_filter("   ")


# Test validate_filter raises TypeError for non-string input.
def test_validate_filter_non_string() -> None:
    with pytest.raises(TypeError):
        validate_filter(123)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        validate_filter(None)  # type: ignore[arg-type]


# Test evaluate_filter with equality comparisons.
def test_evaluate_filter_equality() -> None:
    metadata = {"network": "asia", "status": "ok"}
    assert evaluate_filter("network == 'asia'", metadata) is True
    assert evaluate_filter("network == 'alarm'", metadata) is False
    assert evaluate_filter("status != 'error'", metadata) is True


# Test evaluate_filter with numeric comparisons.
def test_evaluate_filter_numeric_comparisons() -> None:
    metadata = {"sample_size": 1000, "threshold": 0.5}
    assert evaluate_filter("sample_size > 500", metadata) is True
    assert evaluate_filter("sample_size >= 1000", metadata) is True
    assert evaluate_filter("sample_size < 2000", metadata) is True
    assert evaluate_filter("sample_size <= 1000", metadata) is True
    assert evaluate_filter("threshold > 0.3", metadata) is True


# Test evaluate_filter with boolean operators.
def test_evaluate_filter_boolean_operators() -> None:
    metadata = {"a": True, "b": False, "x": 10}
    assert evaluate_filter("a and not b", metadata) is True
    assert evaluate_filter("a or b", metadata) is True
    assert evaluate_filter("not b", metadata) is True
    assert evaluate_filter("x > 5 and x < 20", metadata) is True
    assert evaluate_filter("x < 5 or x > 5", metadata) is True


# Test evaluate_filter with membership testing.
def test_evaluate_filter_membership() -> None:
    metadata = {"network": "asia", "algorithm": "pc"}
    assert evaluate_filter("network in ['asia', 'alarm']", metadata) is True
    assert evaluate_filter("network in ['sports']", metadata) is False
    assert (
        evaluate_filter("algorithm in ['pc', 'fci', 'ges']", metadata) is True
    )


# Test evaluate_filter with parentheses for grouping.
def test_evaluate_filter_grouping() -> None:
    metadata = {"a": 1, "b": 2, "c": 3}
    assert evaluate_filter("(a == 1 or b == 1) and c == 3", metadata) is True
    assert evaluate_filter("a == 1 or (b == 1 and c == 3)", metadata) is True
    assert evaluate_filter("(a == 2 or b == 2) and c == 3", metadata) is True
    assert evaluate_filter("(a == 2 or b == 3) and c == 3", metadata) is False


# Test evaluate_filter with allowed functions.
def test_evaluate_filter_allowed_functions() -> None:
    metadata = {"name": "test", "value": -5, "items": [1, 2, 3]}
    assert evaluate_filter("len(name) == 4", metadata) is True
    assert evaluate_filter("abs(value) == 5", metadata) is True
    assert evaluate_filter("len(items) > 2", metadata) is True


# Test evaluate_filter raises FilterExpressionError for undefined variable.
def test_evaluate_filter_undefined_variable() -> None:
    metadata = {"x": 1}
    with pytest.raises(FilterExpressionError, match="Undefined variable"):
        evaluate_filter("y == 1", metadata)


# Test evaluate_filter raises TypeError for non-string expression.
def test_evaluate_filter_non_string_expression() -> None:
    with pytest.raises(TypeError):
        evaluate_filter(123, {"x": 1})  # type: ignore[arg-type]


# Test evaluate_filter raises TypeError for non-dict metadata.
def test_evaluate_filter_non_dict_metadata() -> None:
    with pytest.raises(TypeError):
        evaluate_filter("x == 1", [1, 2, 3])  # type: ignore[arg-type]


# Test evaluate_filter raises FilterSyntaxError for invalid syntax.
def test_evaluate_filter_invalid_syntax() -> None:
    with pytest.raises(FilterSyntaxError):
        evaluate_filter("x ==", {"x": 1})


# Test get_filter_variables extracts variable names.
def test_get_filter_variables_basic() -> None:
    assert get_filter_variables("x == 1") == {"x"}
    assert get_filter_variables("a > b") == {"a", "b"}
    assert get_filter_variables("network == 'asia'") == {"network"}


# Test get_filter_variables with complex expressions.
def test_get_filter_variables_complex() -> None:
    expr = "network == 'asia' and sample_size > 500 or status in ['ok']"
    variables = get_filter_variables(expr)
    assert variables == {"network", "sample_size", "status"}


# Test get_filter_variables excludes built-in constants.
def test_get_filter_variables_excludes_constants() -> None:
    assert get_filter_variables("x == True") == {"x"}
    assert get_filter_variables("y == False") == {"y"}
    assert get_filter_variables("z == None") == {"z"}


# Test get_filter_variables excludes allowed functions.
def test_get_filter_variables_excludes_functions() -> None:
    assert get_filter_variables("len(x) > 0") == {"x"}
    assert get_filter_variables("abs(y) == 5") == {"y"}


# Test get_filter_variables raises FilterSyntaxError for invalid syntax.
def test_get_filter_variables_invalid_syntax() -> None:
    with pytest.raises(FilterSyntaxError):
        get_filter_variables("x ==")


# Test get_filter_variables raises TypeError for non-string.
def test_get_filter_variables_non_string() -> None:
    with pytest.raises(TypeError):
        get_filter_variables(123)  # type: ignore[arg-type]


# Test filter_entries filters list of entry dicts.
def test_filter_entries_basic() -> None:
    entries = [
        {"metadata": {"network": "asia", "size": 100}},
        {"metadata": {"network": "alarm", "size": 200}},
        {"metadata": {"network": "asia", "size": 300}},
    ]
    result = filter_entries(entries, "network == 'asia'")
    assert len(result) == 2
    assert result[0]["metadata"]["size"] == 100
    assert result[1]["metadata"]["size"] == 300


# Test filter_entries with numeric filter.
def test_filter_entries_numeric() -> None:
    entries = [
        {"metadata": {"x": 10}},
        {"metadata": {"x": 20}},
        {"metadata": {"x": 30}},
    ]
    result = filter_entries(entries, "x > 15")
    assert len(result) == 2


# Test filter_entries skips entries with missing metadata fields.
def test_filter_entries_skips_missing_fields() -> None:
    entries = [
        {"metadata": {"network": "asia"}},
        {"metadata": {"other": "value"}},  # missing 'network'
        {"metadata": {"network": "alarm"}},
    ]
    result = filter_entries(entries, "network == 'asia'")
    assert len(result) == 1


# Test filter_entries with custom metadata key.
def test_filter_entries_custom_metadata_key() -> None:
    entries = [
        {"data": {"x": 1}},
        {"data": {"x": 2}},
    ]
    result = filter_entries(entries, "x == 1", metadata_key="data")
    assert len(result) == 1


# Test filter_entries raises TypeError for non-list entries.
def test_filter_entries_non_list() -> None:
    with pytest.raises(TypeError):
        filter_entries("not a list", "x == 1")  # type: ignore[arg-type]


# Test filter_entries raises FilterSyntaxError for invalid expression.
def test_filter_entries_invalid_expression() -> None:
    with pytest.raises(FilterSyntaxError):
        filter_entries([{"metadata": {"x": 1}}], "x ==")


# Test evaluate_filter coerces result to boolean.
def test_evaluate_filter_coerces_to_bool() -> None:
    metadata = {"x": 0, "y": "", "z": []}
    # These should all return False when coerced
    assert evaluate_filter("x", metadata) is False
    assert evaluate_filter("y", metadata) is False
    assert evaluate_filter("z", metadata) is False

    metadata2 = {"x": 1, "y": "text", "z": [1]}
    # These should all return True when coerced
    assert evaluate_filter("x", metadata2) is True
    assert evaluate_filter("y", metadata2) is True
    assert evaluate_filter("z", metadata2) is True


# Test validate_filter raises FilterSyntaxError for invalid expression.
def test_validate_filter_invalid_expression(mocker: MockerFixture) -> None:
    # Mock parse to raise InvalidExpression (defensive code path)
    from simpleeval import InvalidExpression

    mock_evaluator = mocker.MagicMock()
    mock_evaluator.parse.side_effect = InvalidExpression("test error")
    mocker.patch(
        "causaliq_core.utils.filter_expr._create_evaluator",
        return_value=mock_evaluator,
    )
    with pytest.raises(FilterSyntaxError, match="Invalid filter"):
        validate_filter("x == 1")


# Test evaluate_filter raises FilterSyntaxError for empty expression.
def test_evaluate_filter_empty_expression() -> None:
    with pytest.raises(FilterSyntaxError, match="cannot be empty"):
        evaluate_filter("", {"x": 1})
    with pytest.raises(FilterSyntaxError, match="cannot be empty"):
        evaluate_filter("   ", {"x": 1})


# Test evaluate_filter raises FilterSyntaxError for disallowed operators.
def test_evaluate_filter_invalid_expression() -> None:
    # Lambda triggers FeatureNotAvailable (InvalidExpression subclass)
    with pytest.raises(FilterSyntaxError, match="Invalid filter"):
        evaluate_filter("lambda x: x", {"x": 3})


# Test get_filter_variables raises FilterSyntaxError for empty expression.
def test_get_filter_variables_empty_expression() -> None:
    with pytest.raises(FilterSyntaxError, match="cannot be empty"):
        get_filter_variables("")
    with pytest.raises(FilterSyntaxError, match="cannot be empty"):
        get_filter_variables("   ")


# Test evaluate_filter handles NameError via mock (defensive code path).
def test_evaluate_filter_name_error(mocker: MockerFixture) -> None:
    """Cover defensive NameError handler using mock."""
    mock_evaluator = mocker.MagicMock()
    mock_evaluator.eval.side_effect = NameError("undefined_var")
    mocker.patch(
        "causaliq_core.utils.filter_expr._create_evaluator",
        return_value=mock_evaluator,
    )
    with pytest.raises(FilterExpressionError, match="Undefined variable"):
        evaluate_filter("x == 1", {"x": 1})


# Test evaluate_filter handles generic Exception via mock (defensive code).
def test_evaluate_filter_generic_exception(mocker: MockerFixture) -> None:
    """Cover defensive Exception handler using mock."""
    mock_evaluator = mocker.MagicMock()
    mock_evaluator.eval.side_effect = RuntimeError("unexpected error")
    mocker.patch(
        "causaliq_core.utils.filter_expr._create_evaluator",
        return_value=mock_evaluator,
    )
    with pytest.raises(
        FilterExpressionError, match="Filter evaluation failed"
    ):
        evaluate_filter("x == 1", {"x": 1})
