"""Unit tests for enhanced enumeration classes."""

import pytest

from causaliq_core.utils.enums import EnumWithAttrs


class ExampleEnumWithAttrs(EnumWithAttrs):
    """Example enum for testing EnumWithAttrs functionality."""

    VALUE1 = "val_1", "Value 1"
    VALUE2 = "val_2", "Value 2"


# Test unknown attribute access
def test_enumwithattrs_unknown_enum_value():
    """Test that accessing unknown enum value raises AttributeError."""
    with pytest.raises(AttributeError):
        ExampleEnumWithAttrs.UNKNOWN


# Test unknown attribute access to enum instance
def test_enumwithattrs_unknown_attribute():
    """Test that accessing unknown attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        ExampleEnumWithAttrs.VALUE1.unknown


# Test read-only attributes
def test_enumwithattrs_value_readonly():
    """Test that value attribute is read-only."""
    with pytest.raises(AttributeError):
        ExampleEnumWithAttrs.VALUE1.value = "not allowed"


# Test label attribute is read-only
def test_enumwithattrs_label_readonly():
    """Test that label attribute is read-only."""
    with pytest.raises(AttributeError):
        ExampleEnumWithAttrs.VALUE1.label = "not allowed"


# Test string representation
def test_enumwithattrs_string_representation():
    """Test string representation returns enum value."""
    assert str(ExampleEnumWithAttrs.VALUE1) == "val_1"
    assert str(ExampleEnumWithAttrs.VALUE2) == "val_2"


# Test label access
def test_enumwithattrs_labels():
    """Test label property returns correct labels."""
    assert ExampleEnumWithAttrs.VALUE1.label == "Value 1"
    assert ExampleEnumWithAttrs.VALUE2.label == "Value 2"


# Test value access
def test_enumwithattrs_values():
    """Test value property returns correct values."""
    assert ExampleEnumWithAttrs.VALUE1.value == "val_1"
    assert ExampleEnumWithAttrs.VALUE2.value == "val_2"


# Test enum membership and identity
def test_enumwithattrs_membership():
    """Test enum membership and identity operations."""
    assert ExampleEnumWithAttrs.VALUE1 in ExampleEnumWithAttrs
    assert ExampleEnumWithAttrs.VALUE2 in ExampleEnumWithAttrs
    assert ExampleEnumWithAttrs.VALUE1 != ExampleEnumWithAttrs.VALUE2
    assert ExampleEnumWithAttrs.VALUE1 == ExampleEnumWithAttrs.VALUE1


# Test enum iteration
def test_enumwithattrs_iteration():
    """Test that enum can be iterated over."""
    values = list(ExampleEnumWithAttrs)
    assert len(values) == 2
    assert ExampleEnumWithAttrs.VALUE1 in values
    assert ExampleEnumWithAttrs.VALUE2 in values


# Test enum creation with different attribute patterns
class ExtendedEnumExample(EnumWithAttrs):
    """Example with extended attributes for testing flexibility."""

    OPTION_A = "a", "Option A"
    OPTION_B = "b", "Option B"


# Test enum with different naming patterns
def test_enumwithattrs_extended_usage():
    """Test enum with different naming patterns."""
    assert ExtendedEnumExample.OPTION_A.value == "a"
    assert ExtendedEnumExample.OPTION_A.label == "Option A"
    assert str(ExtendedEnumExample.OPTION_B) == "b"


# Test type annotations work correctly
def test_enumwithattrs_type_checking():
    """Test that enum instances have correct types."""
    assert isinstance(ExampleEnumWithAttrs.VALUE1, ExampleEnumWithAttrs)
    assert isinstance(ExampleEnumWithAttrs.VALUE1, EnumWithAttrs)
    # Test that VALUE1 is exactly of type ExampleEnumWithAttrs
    assert type(ExampleEnumWithAttrs.VALUE1) is ExampleEnumWithAttrs
