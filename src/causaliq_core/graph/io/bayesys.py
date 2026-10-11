#
#   Functions to read Bayesys format graph specification files
#

import csv
from typing import List, Optional, Tuple, Union

from causaliq_core.utils import FileFormatError, is_valid_path

from ..dag import DAG
from ..pdag import PDAG


class _BayesysReader:
    """Accumulate the graph described by a Bayesys CSV file.

    The reader consumes CSV rows in turn and records the first problem it
    encounters, matching the validation performed when the file is read.

    Args:
        all_nodes: Optional specification of nodes.

    Attributes:
        all_nodes: Optional specification of the permitted nodes.
        nodes: Nodes found in the file.
        edges: Edge triples found in the file.
        num_lines: Number of rows consumed.
        error: Description of the first problem found, if any.
    """

    def __init__(self, all_nodes: Optional[List[str]]) -> None:
        self.all_nodes = all_nodes
        self.nodes: List[str] = list(all_nodes) if all_nodes else []
        self.edges: List[Tuple[str, str, str]] = []
        self.num_lines = 0
        self.error = ""

    def consume(self, row: List[str], path: str, strict: bool) -> bool:
        """Consume one CSV row, returning whether reading should continue.

        Args:
            row: Values of the CSV row.
            path: Path of the file, used in error messages.
            strict: Whether strict validation should be applied.

        Returns:
            bool: False when the row was invalid and reading stops.
        """
        self.num_lines += 1
        if len(row) != 4:
            self.error = ", line {} has not got 4 values".format(
                self.num_lines
            )
            return False
        if self.num_lines == 1:
            return self._consume_header(row, strict)
        if row[0] != "{}".format(self.num_lines - 1):
            self.error = ", line {} has bad id".format(self.num_lines)
            return False
        return self._consume_edge(row, path)

    def _consume_header(self, row: List[str], strict: bool) -> bool:
        """Consume the header row, returning whether it was valid.

        Args:
            row: Values of the header row, corrected in place if not strict.
            strict: Whether strict validation should be applied.

        Returns:
            bool: Whether the header row is valid.
        """
        if not strict:  # fix some known content problems
            row[0] = row[0].replace("Id", "ID")
            row[1] = row[1].replace("e.1", "e 1")
            row[3] = row[3].replace("e.2", "e 2")
        if row != ["ID", "Variable 1", "Dependency", "Variable 2"]:
            self.error = " has bad header ({})".format(row)
            return False
        return True

    def _consume_edge(self, row: List[str], path: str) -> bool:
        """Consume an edge row, returning whether it was valid.

        Args:
            row: Values of the CSV row.
            path: Path of the file, used in error messages.

        Returns:
            bool: Whether the row was a valid edge specification.
        """
        if self.all_nodes and (
            row[1] not in self.all_nodes or row[3] not in self.all_nodes
        ):
            raise FileFormatError(
                "file {} contains node not in {}".format(path, self.all_nodes)
            )
        if row[1] not in self.nodes:
            self.nodes.append(row[1])
        if row[3] not in self.nodes:
            self.nodes.append(row[3])
        self.edges.append((row[1], row[2], row[3]))
        return True

    def finish(self) -> None:
        """Record an error when the file held no rows."""
        if self.num_lines < 1 and not self.error:
            self.error = " is empty"


def _consume_open_bayesys_file(
    path: str, reader: "_BayesysReader", strict: bool
) -> None:
    """Feed the rows of an open Bayesys CSV file to a reader.

    Args:
        path: Path of the CSV file.
        reader: Reader accumulating the parsed graph.
        strict: Whether strict validation should be applied.
    """
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not reader.consume(row, path, strict):
                break


def _consume_bayesys_file(
    path: str, reader: "_BayesysReader", strict: bool
) -> None:
    """Feed every row of a Bayesys CSV file to a reader.

    Args:
        path: Path of the CSV file.
        reader: Reader accumulating the parsed graph.
        strict: Whether strict validation should be applied.

    Raises:
        FileFormatError: If the file cannot be decoded as CSV text.
    """
    try:
        _consume_open_bayesys_file(path, reader, strict)
    except UnicodeDecodeError:
        raise FileFormatError("file {} not in CSV format".format(path))


def read(
    path: str, all_nodes: Optional[List[str]] = None, strict: bool = True
) -> Union[PDAG, DAG]:
    """Reads in a graph from a Bayesys format graph specification file.

    Args:
        path: Full path name of file.
        all_nodes: Optional specification of nodes.
        strict: Whether strict validation should be applied.

    Returns:
        DAG or PDAG specified in file.

    Raises:
        TypeError: If argument types incorrect.
        FileNotFoundError: If specified files does not exist.
        FileFormatError: If file contents not valid.
    """
    is_valid_path(path)

    reader = _BayesysReader(all_nodes)
    _consume_bayesys_file(path, reader, strict)
    reader.finish()

    if reader.error:
        raise FileFormatError("file {}{}".format(path, reader.error))

    graph = PDAG(reader.nodes, reader.edges)
    return graph if not graph.is_DAG() else DAG(reader.nodes, reader.edges)


def write(pdag: PDAG, path: str) -> None:
    """Writes a PDAG to a Bayesys format graph specification file.

    Only has details of edges, not unconnected nodes or any parameters.

    Args:
        pdag: PDAG to write to file.
        path: Full path name of file.

    Raises:
        TypeError: If bad arg types.
        FileNotFoundError: If path to file does not exist.
    """
    if not isinstance(pdag, PDAG) or not isinstance(path, str):
        raise TypeError("bayesys.write() bad arg type")

    with open(path, "w", encoding="utf-8") as f:
        f.write("ID,Variable 1,Dependency,Variable 2\n")
        num_edges = 0
        for edge, type in pdag.edges.items():
            num_edges += 1
            f.write(
                "{},{},{},{}\n".format(
                    num_edges, edge[0], type.value[3], edge[1]
                )
            )
