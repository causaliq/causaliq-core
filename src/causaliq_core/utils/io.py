"""IO-related utilities for file and path handling."""

from csv import QUOTE_MINIMAL
from os.path import isdir, isfile
from typing import Optional

from pandas import DataFrame

from .math import rndsf


class FileFormatError(Exception):
    """Exception raised when a file format is invalid or unsupported."""

    pass


def is_valid_path(path: str, is_file: bool = True) -> bool:
    """Check if path is a string and it exists.

    Args:
        path: Full path name of file or directory.
        is_file: Should path be a file (otherwise a directory).

    Returns:
        True if path is valid and exists.

    Raises:
        TypeError: If arguments have bad types.
        FileNotFoundError: If path is not found.
    """
    if not isinstance(path, str) or not isinstance(is_file, bool):
        raise TypeError("is_valid_path() bad arg types")

    if (is_file and not isfile(path)) or (not is_file and not isdir(path)):
        raise FileNotFoundError(f"path {path} not found")

    return True


def write_dataframe(
    df: DataFrame,
    filename: str,
    compress: bool = False,
    sf: int = 10,
    zero: Optional[float] = None,
    preserve: bool = True,
) -> None:
    """Write DataFrame to CSV with numeric rounding and compression options.

    Args:
        df: DataFrame to write.
        filename: Full path of output file.
        compress: Whether to gzip compress the file.
        sf: Number of significant figures to retain for numeric values.
        zero: Absolute values below this counted as zero.
        preserve: Whether df is left unchanged (True conserves original).

    Raises:
        TypeError: If argument types incorrect.
        ValueError: If sf or zero parameters are invalid.
        FileNotFoundError: If destination folder does not exist.
    """
    if (
        not isinstance(filename, str)
        or not isinstance(compress, bool)
        or not isinstance(sf, int)
        or isinstance(sf, bool)
        or (zero is not None and not isinstance(zero, float))
        or not isinstance(preserve, bool)
    ):
        raise TypeError("Bad argument types for write_dataframe")

    zero = zero if zero is not None else 10 ** (-sf)

    if sf < 2 or sf > 10 or zero < 1e-20 or zero > 0.1:
        raise ValueError("Bad argument values for write_dataframe")

    df_to_write = df.copy() if preserve else df
    for col in df_to_write.columns:
        if df_to_write[col].dtype in ["float32", "float64"]:
            df_to_write[col] = df_to_write[col].apply(
                lambda x: rndsf(x, sf, zero)
            )

    try:
        df_to_write.to_csv(
            filename,
            index=False,
            na_rep="*",
            quoting=QUOTE_MINIMAL,
            escapechar="+",
            compression="gzip" if compress else "infer",
        )
    except OSError:
        raise FileNotFoundError("write_dataframe() failed")
