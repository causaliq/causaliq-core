#
#   Common I/O functions for graph file formats
#

from typing import Union

from ..pdag import PDAG
from . import bayesys, tetrad


def read(path: str) -> Union[PDAG]:
    """Read a graph from a file, automatically detecting format from suffix.

    Supports:
    - .csv files (Bayesys format)
    - .tetrad files (Tetrad format)

    Args:
        path: Full path name of file to read.

    Returns:
        Graph read from file (PDAG or DAG).

    Raises:
        TypeError: If path is not a string.
        ValueError: If file suffix is not supported.
        FileNotFoundError: If file is not found.
        FileFormatError: If file format is invalid.
    """
    if not isinstance(path, str):
        raise TypeError("common.read() bad arg type")

    # Extract file suffix
    suffix = path.lower().split(".")[-1]

    if suffix == "csv":
        return bayesys.read(path)
    elif suffix == "tetrad":
        return tetrad.read(path)
    else:
        raise ValueError(f"common.read() unsupported file suffix: .{suffix}")


def write(graph: PDAG, path: str) -> None:
    """Write a graph to a file, automatically detecting format from suffix.

    Supports:
    - .csv files (Bayesys format)
    - .tetrad files (Tetrad format)

    Args:
        graph: Graph to write to file.
        path: Full path name of file to write.

    Raises:
        TypeError: If bad arg types.
        ValueError: If file suffix is not supported.
        FileNotFoundError: If path to file does not exist.
    """
    if not isinstance(graph, PDAG) or not isinstance(path, str):
        raise TypeError("common.write() bad arg types")

    # Extract file suffix
    suffix = path.lower().split(".")[-1]

    if suffix == "csv":
        bayesys.write(graph, path)
    elif suffix == "tetrad":
        tetrad.write(graph, path)
    else:
        raise ValueError(f"common.write() unsupported file suffix: .{suffix}")
