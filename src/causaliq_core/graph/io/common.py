#
#   Common I/O functions for graph file formats
#

from typing import Union

from ..pdag import PDAG
from ..sdg import SDG
from . import bayesys, graphml, tetrad


def read_graph(path: str) -> Union[SDG, PDAG]:
    """Read a graph from a file, automatically detecting format from suffix.

    Supports:
    - .csv files (Bayesys format)
    - .graphml files (GraphML format)
    - .tetrad files (Tetrad format)

    Args:
        path: Full path name of file to read.

    Returns:
        Graph read from file (SDG, PDAG or DAG).

    Raises:
        TypeError: If path is not a string.
        ValueError: If file suffix is not supported.
        FileNotFoundError: If file is not found.
        FileFormatError: If file format is invalid.
    """
    if not isinstance(path, str):
        raise TypeError("common.read_graph() bad arg type")

    # Extract file suffix
    suffix = path.lower().split(".")[-1]

    if suffix == "csv":
        return bayesys.read(path)
    elif suffix == "graphml":
        return graphml.read(path)
    elif suffix == "tetrad":
        return tetrad.read(path)
    else:
        raise ValueError(
            f"common.read_graph() unsupported file suffix: .{suffix}"
        )


def write_graph(graph: PDAG, path: str) -> None:
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
        raise TypeError("common.write_graph() bad arg types")

    # Extract file suffix
    suffix = path.lower().split(".")[-1]

    if suffix == "csv":
        bayesys.write(graph, path)
    elif suffix == "tetrad":
        tetrad.write(graph, path)
    else:
        raise ValueError(
            f"common.write_graph() unsupported file suffix: .{suffix}"
        )
