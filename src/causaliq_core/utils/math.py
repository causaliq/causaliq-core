"""Mathematical utility functions."""

from math import floor
from typing import Optional, Union

import numpy as np


def rndsf(x: Union[int, float], sf: int, zero: Optional[float] = None) -> str:
    """Round number to specified significant figures.

    Args:
        x: Number to round.
        sf: Number of significant figures (2-10).
        zero: Optional zero threshold (default: 10^-sf).

    Returns:
        Formatted string representation with specified significant figures.

    Raises:
        TypeError: If arguments have invalid types.
        ValueError: If arguments have invalid values.

    Examples:
        >>> rndsf(1.234567, 3)
        '1.23'
        >>> rndsf(0.001234, 3)
        '0.00123'
        >>> rndsf(1234567, 3)
        '1230000'
    """
    if (
        not isinstance(x, (float, int))
        or isinstance(x, bool)
        or not isinstance(sf, int)
        or isinstance(sf, bool)
        or (zero is not None and not isinstance(zero, float))
    ):
        raise TypeError("rndsf bad arg types")

    zero = zero if zero is not None else 10 ** (-sf)
    if sf < 2 or sf > 10 or zero < 10**-20 or zero > 0.1:
        raise ValueError("rndsf bad arg values")
    if -zero < x < zero:
        return "0.0"

    exp = int(floor(np.log10(abs(x))))
    x_rounded = round(x, sf - exp - 1)
    result_str = "{:.{}f}".format(x_rounded, max(1, sf - exp - 1))
    result_str = (
        result_str if result_str.endswith(".0") else result_str.rstrip("0")
    )
    result_str = result_str + "0" if result_str.endswith(".") else result_str
    return result_str


def ln(x: float, base: Union[int, str] = "e") -> float:
    """Return logarithm to specified base.

    Args:
        x: Number to obtain logarithm of.
        base: Base to use - 2, 10, or 'e' for natural logarithm.

    Returns:
        Logarithm of x to the specified base.

    Raises:
        TypeError: If arguments have invalid types.
        ValueError: If arguments have invalid values.

    Example:
        >>> ln(10, 10)
        1.0
        >>> ln(8, 2)
        3.0
        >>> ln(2.718281828459045)  # e
        1.0
    """
    if (
        not isinstance(base, (str, int))
        or isinstance(base, bool)
        or not isinstance(x, (float, int))
        or isinstance(x, bool)
    ):
        raise TypeError("ln bad argument type")

    if base not in [2, 10, "e"]:
        raise ValueError("ln bad argument value")

    if base == 2:
        return float(np.log2(x))
    elif base == 10:
        return float(np.log10(x))
    else:  # base == 'e'
        return float(np.log(x))
