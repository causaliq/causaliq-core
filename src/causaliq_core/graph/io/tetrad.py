#
#   Functions to read Tetrad format graph specification files
#

import re
from typing import Union

from causaliq_core.utils import FileFormatError, is_valid_path

from ..dag import DAG
from ..pdag import PDAG

EDGE = re.compile(r"^\d+\.\s(\w+)\s(\-\-[\>\-])\s(\w+)$")


def read(path: str) -> Union[DAG, PDAG]:
    """Reads in a graph from a Tetrad format graph specification file.

    Args:
        path: Full path name of file.

    Returns:
        DAG or PDAG specified in file.

    Raises:
        TypeError: If argument types incorrect.
        ValueError: If file suffix not '.tetrad'.
        FileNotFoundError: If specified files does not exist.
        FileFormatError: If file contents not valid.
    """
    if not isinstance(path, str):
        raise TypeError("tetrad.read() bad arg type")

    if path.lower().split(".")[-1] != "tetrad":
        raise ValueError("tetrad.read() bad file suffix")

    is_valid_path(path)

    pdag = False
    try:
        with open(path, newline="", encoding="utf-8") as f:
            num_line = 0
            error = ""
            edges = []
            for line in f:
                line = line.rstrip("\r\n")
                if not line:  # ignore blank lines
                    continue
                num_line += 1

                # ignore these non-structural elements of the file

                if (
                    line in ["Graph Attributes:", "Graph Node Attributes:"]
                    or line.startswith("Score: ")
                    or line.startswith("BIC: ")
                ):
                    continue

                if (num_line == 1 and line != "Graph Nodes:") or (
                    num_line == 3 and line != "Graph Edges:"
                ):
                    error = " invalid section header"
                    break

                if num_line == 2:
                    nodes = line.replace(";", ",").split(",")

                if num_line > 3:
                    match = EDGE.match(line)
                    if not match:
                        error = " invalid edge: " + line
                        break
                    edges.append(
                        (
                            match.group(1),
                            ("->" if match.group(2) == "-->" else "-"),
                            match.group(3),
                        )
                    )
                    if match.group(2) == "---":
                        pdag = True

        if num_line < 1:
            error = " is empty"

    except UnicodeDecodeError:
        error = " not text"

    if error:
        raise FileFormatError("file {}{}".format(path, error))

    return PDAG(nodes, edges) if pdag else DAG(nodes, edges)


def write(pdag: PDAG, path: str) -> None:
    """Writes a PDAG to a Tetrad format graph specification file.

    No scores are included in the output file.

    Args:
        pdag: PDAG to write to file.
        path: Full path name of file.

    Raises:
        TypeError: If bad arg types.
        FileNotFoundError: If path to file does not exist.
    """
    if not isinstance(pdag, PDAG) or not isinstance(path, str):
        raise TypeError("tetrad.write() bad arg type")

    with open(path, "w", encoding="utf-8") as f:
        f.write("Graph Nodes:\n")
        f.write("{}\n".format(";".join(pdag.nodes)))
        f.write("\nGraph Edges:\n")
        num_edges = 0
        for edge, type in pdag.edges.items():
            num_edges += 1
            edge_symbol = type.value[3]
            tetrad_symbol = "-->" if edge_symbol == "->" else "---"
            f.write(
                "{}. {} {} {}\n".format(
                    num_edges,
                    edge[0],
                    tetrad_symbol,
                    edge[1],
                )
            )
