"""IO-related utilities for file and path handling."""

from os.path import isdir, isfile


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
