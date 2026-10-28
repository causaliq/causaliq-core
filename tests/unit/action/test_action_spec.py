"""Unit tests for causaliq_core.action.spec."""

from causaliq_core import (
    NO_DEFAULT,
    ActionInput,
    ActionOutput,
    ActionPattern,
)

# ---------------------------------------------------------------------------
# ActionInput and ActionOutput tests
# ---------------------------------------------------------------------------


# Test ActionInput dataclass has expected fields and defaults.
def test_action_input_defaults() -> None:
    inp = ActionInput(name="test", description="A test input")
    assert inp.name == "test"
    assert inp.description == "A test input"
    assert inp.required is False
    assert inp.default is NO_DEFAULT
    assert inp.type_hint == "Any"
    assert inp.choices is None


# Test ActionInput with all fields specified.
def test_action_input_full() -> None:
    inp = ActionInput(
        name="param",
        description="A parameter",
        required=False,
        default="value",
        type_hint="str",
        choices=("value", "other"),
    )
    assert inp.name == "param"
    assert inp.required is False
    assert inp.default == "value"
    assert inp.type_hint == "str"
    assert inp.choices == ("value", "other")


# Test ActionOutput dataclass has expected fields.
def test_action_output_fields() -> None:
    out = ActionOutput(name="result", description="Output result", value=42)
    assert out.name == "result"
    assert out.description == "Output result"
    assert out.value == 42


# Test the sentinel is readable in documentation and logs.
def test_no_default_repr() -> None:
    assert repr(NO_DEFAULT) == "NO_DEFAULT"


# Test the default sentinel is distinct from a supplied null value.
def test_no_default_is_not_none() -> None:
    assert NO_DEFAULT is not None


# ---------------------------------------------------------------------------
# ActionPattern enum tests
# ---------------------------------------------------------------------------


# Test ActionPattern has exactly the two documented pattern values.
def test_action_pattern_values() -> None:
    """ActionPattern values match the documented patterns."""
    assert ActionPattern.CREATE.value == "create"
    assert ActionPattern.AGGREGATE.value == "aggregate"
    assert {member.value for member in ActionPattern} == {
        "create",
        "aggregate",
    }
