"""Unit tests for mathematical utility functions."""

import pytest

from causaliq_core.math import ln, rndsf


# Test rndsf function - type errors
def test_rndsf_type_error_x_not_number():
    """Test rndsf raises TypeError for non-numeric x."""
    with pytest.raises(TypeError, match="rndsf bad arg types"):
        rndsf("not a number", 3)


# Test rndsf function - boolean x parameter
def test_rndsf_type_error_x_boolean():
    """Test rndsf raises TypeError for boolean x."""
    with pytest.raises(TypeError, match="rndsf bad arg types"):
        rndsf(True, 3)


# Test rndsf function - sf not integer
def test_rndsf_type_error_sf_not_int():
    """Test rndsf raises TypeError for non-integer sf."""
    with pytest.raises(TypeError, match="rndsf bad arg types"):
        rndsf(1.23, "3")


# Test rndsf function - sf boolean
def test_rndsf_type_error_sf_boolean():
    """Test rndsf raises TypeError for boolean sf."""
    with pytest.raises(TypeError, match="rndsf bad arg types"):
        rndsf(1.23, True)


# Test rndsf function - zero not float when provided
def test_rndsf_type_error_zero_not_float():
    """Test rndsf raises TypeError for non-float zero when provided."""
    with pytest.raises(TypeError, match="rndsf bad arg types"):
        rndsf(1.23, 3, "0.01")


# Test rndsf function - sf too small
def test_rndsf_value_error_sf_too_small():
    """Test rndsf raises ValueError for sf < 2."""
    with pytest.raises(ValueError, match="rndsf bad arg values"):
        rndsf(1.23, 1)


# Test rndsf function - sf too large
def test_rndsf_value_error_sf_too_large():
    """Test rndsf raises ValueError for sf > 10."""
    with pytest.raises(ValueError, match="rndsf bad arg values"):
        rndsf(1.23, 11)


# Test rndsf function - zero too small
def test_rndsf_value_error_zero_too_small():
    """Test rndsf raises ValueError for zero < 10**-20."""
    with pytest.raises(ValueError, match="rndsf bad arg values"):
        rndsf(1.23, 3, 1e-21)


# Test rndsf function - zero too large
def test_rndsf_value_error_zero_too_large():
    """Test rndsf raises ValueError for zero > 0.1."""
    with pytest.raises(ValueError, match="rndsf bad arg values"):
        rndsf(1.23, 3, 0.2)


# Test rndsf function - valid formatting cases
def test_rndsf_basic_formatting():
    """Test rndsf basic number formatting."""
    assert rndsf(1.23456789, 4) == "1.235"
    assert rndsf(12.3456789, 4) == "12.35"
    assert rndsf(123.456789, 4) == "123.5"


# Test rndsf function - zero threshold behaviour
def test_rndsf_zero_threshold():
    """Test rndsf zero threshold functionality."""
    assert rndsf(0.0001, 3) == "0.0"  # Default zero threshold
    assert rndsf(0.01, 3, 0.001) == "0.01"  # Above custom threshold
    assert rndsf(0.0001, 3, 0.001) == "0.0"  # Below custom threshold


# Test rndsf function - negative numbers
def test_rndsf_negative_numbers():
    """Test rndsf with negative numbers."""
    assert rndsf(-1.23456, 3) == "-1.23"
    assert rndsf(-0.00001, 3) == "0.0"  # Below threshold


# Test rndsf function - large numbers
def test_rndsf_large_numbers():
    """Test rndsf with large numbers.

    Note: Legacy function returns .0 for large rounded numbers.
    """
    assert rndsf(1234567, 3) == "1230000.0"
    assert rndsf(9876543, 4) == "9877000.0"


# Test rndsf function - decimal formatting edge cases
def test_rndsf_decimal_formatting():
    """Test rndsf decimal formatting edge cases.

    Note: Legacy function strips trailing zeros but preserves .0 endings.
    """
    assert rndsf(1.0, 3) == "1.0"
    assert rndsf(10.0, 3) == "10.0"
    # Legacy strips trailing zeros: 0.100 -> 0.1 (not 0.10)
    assert rndsf(0.100, 2) == "0.1"


# Test rndsf function - integer input
def test_rndsf_integer_input():
    """Test rndsf with integer input.

    Note: Legacy function returns .0 suffix for rounded integers.
    """
    assert rndsf(123, 2) == "120.0"
    assert rndsf(5, 3) == "5.0"


# Test ln function - type errors
def test_ln_type_error_x_not_number():
    """Test ln raises TypeError for non-numeric x."""
    with pytest.raises(TypeError, match="ln bad argument type"):
        ln("not a number")


# Test ln function - x boolean
def test_ln_type_error_x_boolean():
    """Test ln raises TypeError for boolean x."""
    with pytest.raises(TypeError, match="ln bad argument type"):
        ln(True)


# Test ln function - base invalid type
def test_ln_type_error_base_invalid():
    """Test ln raises TypeError for invalid base type."""
    with pytest.raises(TypeError, match="ln bad argument type"):
        ln(10, 3.0)


# Test ln function - base boolean
def test_ln_type_error_base_boolean():
    """Test ln raises TypeError for boolean base."""
    with pytest.raises(TypeError, match="ln bad argument type"):
        ln(10, False)


# Test ln function - invalid base value
def test_ln_value_error_invalid_base():
    """Test ln raises ValueError for invalid base value."""
    with pytest.raises(ValueError, match="ln bad argument value"):
        ln(10, 5)


# Test ln function - base 10 calculations
def test_ln_base_10():
    """Test ln with base 10."""
    assert ln(10, 10) == 1.0
    assert ln(100, 10) == 2.0
    assert ln(1, 10) == 0.0
    assert abs(ln(2, 10) - 0.30102999566398119) < 1e-10


# Test ln function - base 2 calculations
def test_ln_base_2():
    """Test ln with base 2."""
    assert ln(2, 2) == 1.0
    assert ln(8, 2) == 3.0
    assert ln(1, 2) == 0.0
    assert abs(ln(10, 2) - 3.3219280948873626) < 1e-10


# Test ln function - natural logarithm (base e)
def test_ln_natural_logarithm():
    """Test ln with natural logarithm (base e)."""
    assert ln(1) == 0.0
    assert ln(1, "e") == 0.0
    # Test with e (approximately)
    e_approx = 2.718281828459045
    assert abs(ln(e_approx) - 1.0) < 1e-10
    assert abs(ln(e_approx, "e") - 1.0) < 1e-10


# Test ln function - return type is float
def test_ln_return_type():
    """Test ln returns float values."""
    result = ln(10, 10)
    assert isinstance(result, float)
    result = ln(8, 2)
    assert isinstance(result, float)
    result = ln(2.718281828459045)
    assert isinstance(result, float)


# Test ln function - mathematical consistency
def test_ln_mathematical_consistency():
    """Test ln mathematical properties."""
    # ln(a*b) = ln(a) + ln(b) (natural log)
    a, b = 2.5, 3.7
    assert abs(ln(a * b) - (ln(a) + ln(b))) < 1e-10

    # log_10(a*b) = log_10(a) + log_10(b)
    assert abs(ln(a * b, 10) - (ln(a, 10) + ln(b, 10))) < 1e-10


# Test with edge case values
def test_ln_edge_cases():
    """Test ln with edge case values."""
    # Very small positive numbers
    assert ln(1e-10, 10) == -10.0

    # Numbers close to 1
    assert abs(ln(1.000001) - 0.000001) < 1e-6
