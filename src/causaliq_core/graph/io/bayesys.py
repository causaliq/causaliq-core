#
#   Functions to read Bayesys format graph specification files
#

import csv
from typing import List, Optional, Union

from causaliq_core.utils import FileFormatError, is_valid_path

from ..dag import DAG
from ..pdag import PDAG


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

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        num_line = 0
        error = ""
        nodes = list(all_nodes) if all_nodes else []
        edges = []
        try:
            for row in reader:
                num_line += 1
                if len(row) != 4:
                    error = ", line {} has not got 4 values".format(num_line)
                    break
                if num_line == 1:
                    if not strict:  # fix some known content problems
                        row[0] = row[0].replace("Id", "ID")
                        row[1] = row[1].replace("e.1", "e 1")
                        row[3] = row[3].replace("e.2", "e 2")
                    if row != ["ID", "Variable 1", "Dependency", "Variable 2"]:
                        error = " has bad header ({})".format(row)
                        break
                    continue
                if num_line > 1 and row[0] != "{}".format(num_line - 1):
                    error = ", line {} has bad id".format(num_line)
                    break

                if all_nodes and (
                    row[1] not in all_nodes or row[3] not in all_nodes
                ):
                    raise FileFormatError(
                        "file {} contains node not in {}".format(
                            path, all_nodes
                        )
                    )
                if row[1] not in nodes:
                    nodes.append(row[1])
                if row[3] not in nodes:
                    nodes.append(row[3])
                edges.append((row[1], row[2], row[3]))

        except UnicodeDecodeError:
            raise FileFormatError("file {} not in CSV format".format(path))

        if num_line < 1:
            error = " is empty"

        if error:
            raise FileFormatError("file {}{}".format(path, error))
        else:
            graph = PDAG(nodes, edges)
            return graph if not graph.is_DAG() else DAG(nodes, edges)


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
