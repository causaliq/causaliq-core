"""Tests for relaxing bare literals in filter expressions."""

import pytest

from causaliq_core.utils.filter_expr import (
    FilterSyntaxError,
    evaluate_filter,
)
from causaliq_core.utils.filter_literals import relax_filter_literals


# A bare comparison value becomes a string literal.
def test_relax_bare_equality_value() -> None:
    assert relax_filter_literals("status == ok") == "status == 'ok'"


# Bare values in a membership list become string literals.
def test_relax_membership_list_values() -> None:
    relaxed = relax_filter_literals("network in [asia, cancer]")
    assert relaxed == "network in ['asia', 'cancer']"


# Bare values in a membership tuple become string literals.
def test_relax_membership_tuple_values() -> None:
    relaxed = relax_filter_literals("network in (asia, cancer)")
    assert relaxed == "network in ('asia', 'cancer')"


# Bare values in a membership set become string literals.
def test_relax_membership_set_value() -> None:
    relaxed = relax_filter_literals("network in {asia}")
    assert relaxed == "network in {'asia'}"


# A reserved parameter name stays a reference.
def test_relax_reserved_name_is_kept() -> None:
    relaxed = relax_filter_literals(
        "description == description", {"description"}
    )
    assert relaxed == "description == description"


# A name used as a left side elsewhere stays a reference.
def test_relax_left_hand_name_is_kept() -> None:
    relaxed = relax_filter_literals("a == b and b == c")
    assert relaxed == "a == b and b == 'c'"


# An identity comparison keeps a bare name as a reference.
def test_relax_identity_comparison_is_kept() -> None:
    relaxed = relax_filter_literals("status is ok")
    assert relaxed == "status is ok"


# A dotted name is a metadata path and is never rewritten.
def test_relax_dotted_name_is_kept() -> None:
    relaxed = relax_filter_literals("learn_graph.status == ok")
    assert relaxed == "learn_graph.status == 'ok'"


# A function call on the right is never rewritten.
def test_relax_function_call_is_kept() -> None:
    relaxed = relax_filter_literals("seed in random(3, 0)")
    assert relaxed == "seed in random(3, 0)"


# A builtin name on the right is never rewritten.
def test_relax_builtin_name_is_kept() -> None:
    relaxed = relax_filter_literals("value == len")
    assert relaxed == "value == len"


# An already quoted value produces an equivalent expression.
def test_relax_quoted_value_is_unchanged() -> None:
    relaxed = relax_filter_literals("status == 'ok'")
    assert relaxed == "status == 'ok'"
    assert evaluate_filter(relaxed, {"status": "ok"}) is True


# A literal that collides with a parameter keeps its quotes.
def test_relax_quoted_collision_is_unchanged() -> None:
    relaxed = relax_filter_literals(
        "description == 'description'", {"description"}
    )
    assert relaxed == "description == 'description'"


# Boolean operators and negation are preserved.
def test_relax_boolean_operators() -> None:
    relaxed = relax_filter_literals("not status == failed and mode == strict")
    assert relaxed == "not status == 'failed' and mode == 'strict'"


# An empty expression is returned unchanged.
def test_relax_empty_expression() -> None:
    assert relax_filter_literals("") == ""
    assert relax_filter_literals("   ") == "   "


# A non-string expression is rejected.
def test_relax_non_string_expression() -> None:
    with pytest.raises(TypeError):
        relax_filter_literals(123)  # type: ignore[arg-type]


# Invalid syntax is reported as a filter syntax error.
def test_relax_invalid_syntax() -> None:
    with pytest.raises(FilterSyntaxError):
        relax_filter_literals("status ==")


# The relaxed expression evaluates against metadata.
def test_relaxed_expression_evaluates() -> None:
    relaxed = relax_filter_literals("network == asia and f1 > 0.8")
    assert evaluate_filter(relaxed, {"network": "asia", "f1": 0.9}) is True
    assert evaluate_filter(relaxed, {"network": "asia", "f1": 0.5}) is False
