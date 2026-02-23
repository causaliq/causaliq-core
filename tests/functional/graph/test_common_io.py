"""Functional tests for common module - reading and writing files."""

from pathlib import Path
from unittest.mock import patch

import pytest

from causaliq_core.graph.dag import DAG
from causaliq_core.graph.io.common import (
    read_graph,
    read_pdg,
    write_graph,
    write_pdg,
)
from causaliq_core.graph.pdag import PDAG
from causaliq_core.graph.pdg import PDG, EdgeProbabilities

# Path to test data
TEST_DATA_DIR = Path("tests/data/functional/graphs")
TMP_DIR = TEST_DATA_DIR / "tmp"


@pytest.fixture
def tmp_dir():
    """Fixture to create and clean up temporary directory."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    yield TMP_DIR
    # Cleanup
    for file in TMP_DIR.glob("*.csv"):
        file.unlink()
    for file in TMP_DIR.glob("*.tetrad"):
        file.unlink()
    for file in TMP_DIR.glob("*.graphml"):
        file.unlink()


# Test read CSV file calls bayesys.read
def test_common_read_csv_calls_bayesys():
    with patch(
        "causaliq_core.graph.io.common.bayesys.read"
    ) as mock_bayesys_read:
        mock_bayesys_read.return_value = DAG(["A", "B"], [("A", "->", "B")])
        result = read_graph(str(TEST_DATA_DIR / "test.csv"))
        mock_bayesys_read.assert_called_once_with(
            str(TEST_DATA_DIR / "test.csv")
        )
        assert result is not None


# Test read TETRAD file calls tetrad.read
def test_common_read_tetrad_calls_tetrad():
    with patch(
        "causaliq_core.graph.io.common.tetrad.read"
    ) as mock_tetrad_read:
        mock_tetrad_read.return_value = DAG(["A", "B"], [("A", "->", "B")])
        result = read_graph(str(TEST_DATA_DIR / "test.tetrad"))
        mock_tetrad_read.assert_called_once_with(
            str(TEST_DATA_DIR / "test.tetrad")
        )
        assert result is not None


# Test read actual CSV file
def test_common_read_csv_actual_file():
    graph = read_graph(str(TEST_DATA_DIR / "abc.csv"))
    assert graph is not None
    assert len(graph.nodes) == 3
    assert set(graph.nodes) == {"A", "B", "C"}


# Test read actual TETRAD file
def test_common_read_tetrad_actual_file():
    graph = read_graph(str(TEST_DATA_DIR / "abc.tetrad"))
    assert graph is not None
    assert len(graph.nodes) == 3
    assert set(graph.nodes) == {"A", "B", "C"}


# Test read GraphML file calls graphml.read
def test_common_read_graphml_calls_graphml():
    with patch(
        "causaliq_core.graph.io.common.graphml.read"
    ) as mock_graphml_read:
        mock_graphml_read.return_value = DAG(["A", "B"], [("A", "->", "B")])
        result = read_graph(str(TEST_DATA_DIR / "test.graphml"))
        mock_graphml_read.assert_called_once_with(
            str(TEST_DATA_DIR / "test.graphml")
        )
        assert result is not None


# Test read actual GraphML file
def test_common_read_graphml_actual_file():
    graph = read_graph(str(TEST_DATA_DIR / "abc.graphml"))
    assert graph is not None
    assert len(graph.nodes) == 3
    assert set(graph.nodes) == {"A", "B", "C"}


# Test write CSV file calls bayesys.write
def test_common_write_csv_calls_bayesys(tmp_dir):
    dag = DAG(["A", "B"], [("A", "->", "B")])
    test_file = tmp_dir / "test_output.csv"

    with patch(
        "causaliq_core.graph.io.common.bayesys.write"
    ) as mock_bayesys_write:
        write_graph(dag, str(test_file))
        mock_bayesys_write.assert_called_once_with(dag, str(test_file))


# Test write TETRAD file calls tetrad.write
def test_common_write_tetrad_calls_tetrad(tmp_dir):
    dag = DAG(["A", "B"], [("A", "->", "B")])
    test_file = tmp_dir / "test_output.tetrad"

    with patch(
        "causaliq_core.graph.io.common.tetrad.write"
    ) as mock_tetrad_write:
        write_graph(dag, str(test_file))
        mock_tetrad_write.assert_called_once_with(dag, str(test_file))


# Test round-trip CSV write and read
def test_common_roundtrip_csv(tmp_dir):
    # Create a simple DAG
    original_dag = DAG(["A", "B", "C"], [("A", "->", "B"), ("B", "->", "C")])
    test_file = tmp_dir / "test_roundtrip.csv"

    # Write using common interface
    write_graph(original_dag, str(test_file))

    # Read back using common interface
    read_dag = read_graph(str(test_file))

    # Compare
    assert set(original_dag.nodes) == set(read_dag.nodes)
    assert original_dag.is_DAG() == read_dag.is_DAG()


# Test round-trip TETRAD write and read
def test_common_roundtrip_tetrad(tmp_dir):
    # Create a simple DAG
    original_dag = DAG(["A", "B", "C"], [("A", "->", "B"), ("B", "->", "C")])
    test_file = tmp_dir / "test_roundtrip.tetrad"

    # Write using common interface
    write_graph(original_dag, str(test_file))

    # Read back using common interface
    read_dag = read_graph(str(test_file))

    # Compare
    assert set(original_dag.nodes) == set(read_dag.nodes)
    assert original_dag.is_DAG() == read_dag.is_DAG()


# Test round-trip PDAG CSV
def test_common_roundtrip_pdag_csv(tmp_dir):
    # Create a simple PDAG
    original_pdag = PDAG(["A", "B", "C"], [("A", "-", "B"), ("B", "->", "C")])
    test_file = tmp_dir / "test_pdag_roundtrip.csv"

    # Write using common interface
    write_graph(original_pdag, str(test_file))

    # Read back using common interface
    read_pdag = read_graph(str(test_file))

    # Compare
    assert set(original_pdag.nodes) == set(read_pdag.nodes)
    assert original_pdag.is_DAG() == read_pdag.is_DAG()


# Test round-trip PDAG TETRAD
def test_common_roundtrip_pdag_tetrad(tmp_dir):
    # Create a simple PDAG
    original_pdag = PDAG(["A", "B", "C"], [("A", "-", "B"), ("B", "->", "C")])
    test_file = tmp_dir / "test_pdag_roundtrip.tetrad"

    # Write using common interface
    write_graph(original_pdag, str(test_file))

    # Read back using common interface
    read_pdag = read_graph(str(test_file))

    # Compare
    assert set(original_pdag.nodes) == set(read_pdag.nodes)
    assert original_pdag.is_DAG() == read_pdag.is_DAG()


# Test write GraphML file calls graphml.write.
def test_common_write_graphml_calls_graphml(tmp_dir):
    dag = DAG(["A", "B"], [("A", "->", "B")])
    test_file = tmp_dir / "test_output.graphml"

    with patch(
        "causaliq_core.graph.io.common.graphml.write"
    ) as mock_graphml_write:
        write_graph(dag, str(test_file))
        mock_graphml_write.assert_called_once_with(dag, str(test_file))


# Test read_pdg calls graphml.read_pdg.
def test_common_read_pdg_calls_graphml():
    with patch(
        "causaliq_core.graph.io.common.graphml.read_pdg"
    ) as mock_read_pdg:
        mock_read_pdg.return_value = PDG(
            ["A", "B"],
            {
                ("A", "B"): EdgeProbabilities(
                    forward=0.8, backward=0.1, none=0.1
                )
            },
        )
        result = read_pdg(str(TEST_DATA_DIR / "test.graphml"))
        mock_read_pdg.assert_called_once_with(
            str(TEST_DATA_DIR / "test.graphml")
        )
        assert result is not None


# Test write_pdg calls graphml.write_pdg.
def test_common_write_pdg_calls_graphml(tmp_dir):
    pdg = PDG(
        ["A", "B"],
        {("A", "B"): EdgeProbabilities(forward=0.8, backward=0.1, none=0.1)},
    )
    test_file = tmp_dir / "test_output.graphml"

    with patch(
        "causaliq_core.graph.io.common.graphml.write_pdg"
    ) as mock_write_pdg:
        write_pdg(pdg, str(test_file))
        mock_write_pdg.assert_called_once_with(pdg, str(test_file))
