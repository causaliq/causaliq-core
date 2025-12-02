#
# Functions for comparing values, dictionaries, and distributions
# with specified precision (significant figures)

from math import floor, isnan, log10
from typing import Any, Dict, Union

from pandas import DataFrame


def values_same(
    value1: Union[int, float, bool],
    value2: Union[int, float, bool],
    sf: int = 3,
) -> bool:
    """Test whether two numeric values are the same to specified
    significant figures.

    Args:
        value1: First value in comparison.
        value2: Second value in comparison.
        sf: Number of significant figures used in comparison.

    Returns:
        bool: Whether two values are the same to specified number of s.f.

    Raises:
        TypeError: If any arg not of required type. Since this function
                   must be very efficient we rely on the Python
                   standard functions to signal TypeErrors rather than
                   explicitly testing the argument types.
    """
    # Handle zero and NaNs explicitly - all zeros are considered the same,
    # but unlike standard Python, two NaNs compare as True

    if value1 == 0 or value2 == 0:
        return value1 == value2
    isnan_1 = isnan(value1)
    isnan_2 = isnan(value2)
    if isnan_1 or isnan_2:
        return isnan_1 == isnan_2

    # Quick pre-check: quickly determine if values differ by more than a factor
    # of bound_m which is an upper bound on the ratio of numbers at a specific
    # sf value.

    abs_value1 = abs(value1)
    abs_value2 = abs(value2)
    bound_m = 1.0 + 10 ** (1 - sf)
    if abs_value1 > bound_m * abs_value2 or abs_value2 > bound_m * abs_value1:
        return False

    # Compute the scaled values for comparison

    scale1 = round(value1, -int(floor(log10(abs_value1)) - (sf - 1)))
    scale2 = round(value2, -int(floor(log10(abs_value2)) - (sf - 1)))

    return scale1 == scale2


def dicts_same(
    dict1: Dict[str, Any],
    dict2: Dict[str, Any],
    sf: int = 10,
    strict: bool = True,
) -> bool:
    """Return whether two dicts have same values to specified
    significant digits.

    Args:
        dict1: First dictionary of values.
        dict2: Second dictionary of values.
        sf: Number of significant figures used in comparisons.
        strict: Whether two dicts must contain same keys.

    Returns:
        bool: Whether two dicts are same.

    Raises:
        TypeError: If any arg not of required type.
    """
    if (
        not isinstance(dict1, dict)
        or not isinstance(dict2, dict)
        or not isinstance(sf, int)
        or isinstance(sf, bool)
        or not isinstance(strict, bool)
    ):
        raise TypeError("Bad arg types for dicts_same")

    if strict and dict1.keys() != dict2.keys():
        raise TypeError("Two dicts have different keys and strict is True")

    same = True
    for key, value in dict1.items():
        if key not in dict2 or (dict1[key] is None and dict2[key] is None):
            continue
        if (
            (dict1[key] is None and dict2[key] is not None)
            or (dict1[key] is not None and dict2[key] is None)
            or not values_same(dict1[key], dict2[key], sf=sf)
        ):
            same = False
            break

    return same


def dists_same(df1: DataFrame, df2: DataFrame, sf: int = 10) -> bool:
    """Test whether two distributions are the same with specified precision.

    Tests if their probabilities agree to a specified number of significant
    digits.

    Args:
        df1: First distribution.
        df2: Second distribution.
        sf: Number of sig. figures used in probability comparisons.

    Returns:
        bool: Whether the two distributions are same to the specified
              number of significant figures.

    Raises:
        TypeError: If any arg not of required type.
    """
    if not isinstance(df1, DataFrame) or not isinstance(df2, DataFrame):
        raise TypeError("dists_same() bad arg types")

    if (
        sorted(list(df1.index)) != sorted(list(df2.index))
        or df1.index.name != df2.index.name
    ):
        print("\ndists_same: different primary variable/values")
        return False

    if list(df1.columns.names) != list(df2.columns.names):
        print("\ndists_same: different secondary variables")
        return False

    dict1 = df1.to_dict()
    dict2 = df2.to_dict()

    if dict1.keys() != dict2.keys():
        print("\ndists_same: different secondary values")
        return False

    for values, pmf in dict1.items():
        if not dicts_same(pmf, dict2[values], sf):
            print("\ndists_same: different probabilities")
            return False

    return True
