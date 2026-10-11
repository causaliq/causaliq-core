#
#   Functions to read Tetrad format graph specification files
#

import re
from typing import List, Optional, Tuple, Union

from causaliq_core.utils import FileFormatError, is_valid_path

from ..dag import DAG
from ..pdag import PDAG

EDGE = re.compile(r"^\d+\.\s(\w+)\s(\-\-[\>\-])\s(\w+)$")


def _is_ignorable_line(line: str) -> bool:
    """Return whether a line carries no structural information.

    Args:
        line: Line of the file with the terminator removed.

    Returns:
        bool: Whether the line can be ignored.
    """
    if line.startswith(("Score: ", "BIC: ")):
        return True
    return line in ["Graph Attributes:", "Graph Node Attributes:"]


def _has_bad_section_header(num_line: int, line: str) -> bool:
    """Return whether a line should be a section header but is not.

    Args:
        num_line: One-based number of the structural line.
        line: Line of the file with the terminator removed.

    Returns:
        bool: Whether the expected section header is missing or malformed.
    """
    if num_line == 1:
        return line != "Graph Nodes:"
    if num_line == 3:
        return line != "Graph Edges:"
    return False


def _parse_edge_line(
    line: str,
) -> Optional[Tuple[Tuple[str, str, str], bool]]:
    """Return the edge described by a Tetrad edge line.

    Args:
        line: Line of the file with the terminator removed.

    Returns:
        Tuple of (edge triple, is undirected), or None when the line is
        not a valid edge.
    """
    match = EDGE.match(line)
    if not match:
        return None
    triple = (
        match.group(1),
        ("->" if match.group(2) == "-->" else "-"),
        match.group(3),
    )
    return (triple, match.group(2) == "---")


class _TetradReader:
    """Accumulate the graph described by a Tetrad file.

    The reader consumes structural lines in turn and records the first
    problem it encounters, matching the validation performed when the
    file is read.

    Attributes:
        nodes: Nodes found in the file.
        edges: Edge triples found in the file.
        is_pdag: Whether any undirected edge was found.
        num_lines: Number of structural lines consumed.
        error: Description of the first problem found, if any.
    """

    def __init__(self) -> None:
        self.nodes: List[str] = []
        self.edges: List[Tuple[str, str, str]] = []
        self.is_pdag = False
        self.num_lines = 0
        self.error = ""

    def consume(self, line: str) -> bool:
        """Consume one line, returning whether parsing should continue.

        Args:
            line: Raw line from the file.

        Returns:
            bool: False when the line was malformed and parsing stops.
        """
        line = line.rstrip("\r\n")
        if not line or _is_ignorable_line(line):
            return True
        self.num_lines += 1
        if _has_bad_section_header(self.num_lines, line):
            self.error = " invalid section header"
            return False
        if self.num_lines == 2:
            self.nodes = line.replace(";", ",").split(",")
        if self.num_lines > 3:
            return self._consume_edge(line)
        return True

    def _consume_edge(self, line: str) -> bool:
        """Consume an edge line, returning whether it was well formed.

        Args:
            line: Structural line from the file.

        Returns:
            bool: False when the line is not a valid edge.
        """
        parsed = _parse_edge_line(line)
        if parsed is None:
            self.error = " invalid edge: " + line
            return False
        self.edges.append(parsed[0])
        self.is_pdag = self.is_pdag or parsed[1]
        return True

    def finish(self) -> None:
        """Record an error when the file held no structural lines."""
        if self.num_lines < 1 and not self.error:
            self.error = " is empty"


def _consume_open_tetrad_file(path: str, reader: "_TetradReader") -> None:
    """Feed the lines of an open Tetrad file to a reader.

    Args:
        path: Path of the Tetrad file.
        reader: Reader accumulating the parsed graph.
    """
    with open(path, newline="", encoding="utf-8") as f:
        for line in f:
            if not reader.consume(line):
                break


def _consume_tetrad_file(path: str, reader: "_TetradReader") -> None:
    """Feed every line of a Tetrad file to a reader.

    Args:
        path: Path of the Tetrad file.
        reader: Reader accumulating the parsed graph.
    """
    try:
        _consume_open_tetrad_file(path, reader)
    except UnicodeDecodeError:
        reader.error = " not text"


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

    reader = _TetradReader()
    _consume_tetrad_file(path, reader)
    reader.finish()

    if reader.error:
        raise FileFormatError("file {}{}".format(path, reader.error))

    if reader.is_pdag:
        return PDAG(reader.nodes, reader.edges)
    return DAG(reader.nodes, reader.edges)


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
