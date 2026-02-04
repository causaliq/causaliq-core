"""Functional tests for graphml module - reading from files."""

from pathlib import Path

import pytest

from causaliq_core.graph import DAG, PDAG, SDG
from causaliq_core.graph.io.graphml import read
from causaliq_core.utils import FileFormatError

# Path to test data.
TEST_DATA_DIR = Path("tests/data/functional/graphs")


# Test read fails on nonexistent file.
def test_graphml_read_filenotfound_error() -> None:
    with pytest.raises(FileNotFoundError):
        read("doesnotexist.graphml")


# Test read fails on invalid XML.
def test_graphml_read_fileformat_error_invalid_xml() -> None:
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "invalid_xml.graphml"))


# Test read fails on wrong root element.
def test_graphml_read_fileformat_error_wrong_root() -> None:
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "wrong_root.graphml"))


# Test read fails on missing graph element.
def test_graphml_read_fileformat_error_no_graph() -> None:
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "no_graph.graphml"))


# Test read fails on graph with no nodes.
def test_graphml_read_fileformat_error_no_nodes() -> None:
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "no_nodes.graphml"))


# Test read fails on duplicate node ids.
def test_graphml_read_fileformat_error_duplicate_node() -> None:
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "duplicate_node.graphml"))


# Test read fails on edge without source.
def test_graphml_read_fileformat_error_edge_no_source() -> None:
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "edge_no_source.graphml"))


# Test reading single node A returns DAG.
def test_graphml_read_a_ok() -> None:
    graph = read(str(TEST_DATA_DIR / "a.graphml"))
    assert graph is not None
    assert isinstance(graph, DAG)
    assert len(graph.nodes) == 1
    assert "A" in graph.nodes


# Test reading A -> B DAG.
def test_graphml_read_ab_ok() -> None:
    graph = read(str(TEST_DATA_DIR / "ab.graphml"))
    assert graph is not None
    assert isinstance(graph, DAG)
    assert len(graph.nodes) == 2
    assert set(graph.nodes) == {"A", "B"}
    assert graph.is_DAG()


# Test reading non-namespaced GraphML.
def test_graphml_read_ab_no_namespace_ok() -> None:
    graph = read(str(TEST_DATA_DIR / "ab_no_namespace.graphml"))
    assert graph is not None
    assert isinstance(graph, DAG)
    assert len(graph.nodes) == 2
    assert set(graph.nodes) == {"A", "B"}


# Test reading A -> B -> C DAG.
def test_graphml_read_abc_ok() -> None:
    graph = read(str(TEST_DATA_DIR / "abc.graphml"))
    assert graph is not None
    assert isinstance(graph, DAG)
    assert len(graph.nodes) == 3
    assert set(graph.nodes) == {"A", "B", "C"}
    assert graph.is_DAG()


# Test reading PDAG with undirected edge (directed=false attribute).
def test_graphml_read_abc_pdag_ok() -> None:
    graph = read(str(TEST_DATA_DIR / "abc_pdag.graphml"))
    assert graph is not None
    assert isinstance(graph, PDAG)
    assert len(graph.nodes) == 3
    assert set(graph.nodes) == {"A", "B", "C"}
    assert not graph.is_DAG()


# Test reading PDAG with sourceEndpoint/targetEndpoint data attributes.
def test_graphml_read_abc_pdag_edgetype_ok() -> None:
    graph = read(str(TEST_DATA_DIR / "abc_pdag_edgetype.graphml"))
    assert graph is not None
    assert isinstance(graph, PDAG)
    assert len(graph.nodes) == 3
    assert set(graph.nodes) == {"A", "B", "C"}


# Test reading PDAG using edgeType symbol attribute (alternative format).
def test_graphml_read_edgetype_symbol_ok() -> None:
    graph = read(str(TEST_DATA_DIR / "abc_edgetype_symbol.graphml"))
    assert graph is not None
    assert isinstance(graph, PDAG)
    assert len(graph.nodes) == 3
    assert set(graph.nodes) == {"A", "B", "C"}


# Test reading PAG with bidirected and semidirected edges.
def test_graphml_read_abc_pag_ok() -> None:
    graph = read(str(TEST_DATA_DIR / "abc_pag.graphml"))
    assert graph is not None
    assert isinstance(graph, SDG)
    assert len(graph.nodes) == 3
    assert set(graph.nodes) == {"A", "B", "C"}


# Test reading Asia network DAG.
def test_graphml_read_asia_ok() -> None:
    graph = read(str(TEST_DATA_DIR / "asia.graphml"))
    assert graph is not None
    assert isinstance(graph, DAG)
    assert len(graph.nodes) == 8
    expected_nodes = {
        "asia",
        "tub",
        "smoke",
        "lung",
        "bronc",
        "either",
        "xray",
        "dysp",
    }
    assert set(graph.nodes) == expected_nodes
    assert graph.is_DAG()


# ============================================================================
# Tests for all 9 edge endpoint combinations (LINE, ARROW, CIRCLE)
# ============================================================================


# Test LINE -> LINE endpoint produces undirected edge (-).
def test_graphml_read_edge_line_line() -> None:
    graph = read(str(TEST_DATA_DIR / "edge_line_line.graphml"))
    assert graph is not None
    assert isinstance(graph, PDAG)
    # Check edge is undirected
    from causaliq_core.graph import EdgeType

    assert graph.edges[("A", "B")] == EdgeType.UNDIRECTED


# Test LINE -> ARROW endpoint produces directed edge (->).
def test_graphml_read_edge_line_arrow() -> None:
    graph = read(str(TEST_DATA_DIR / "edge_line_arrow.graphml"))
    assert graph is not None
    assert isinstance(graph, DAG)
    from causaliq_core.graph import EdgeType

    assert graph.edges[("A", "B")] == EdgeType.DIRECTED


# Test LINE -> CIRCLE endpoint produces semiundirected (o-) with reversal.
def test_graphml_read_edge_line_circle() -> None:
    graph = read(str(TEST_DATA_DIR / "edge_line_circle.graphml"))
    assert graph is not None
    assert isinstance(graph, SDG)
    from causaliq_core.graph import EdgeType

    # LINE->CIRCLE reverses to CIRCLE->LINE which is SEMIUNDIRECTED (o-)
    assert graph.edges[("A", "B")] == EdgeType.SEMIUNDIRECTED


# Test ARROW -> ARROW endpoint produces bidirected edge (<->).
def test_graphml_read_edge_arrow_arrow() -> None:
    graph = read(str(TEST_DATA_DIR / "edge_arrow_arrow.graphml"))
    assert graph is not None
    assert isinstance(graph, SDG)
    from causaliq_core.graph import EdgeType

    assert graph.edges[("A", "B")] == EdgeType.BIDIRECTED


# Test ARROW -> LINE endpoint produces directed edge with reversal.
def test_graphml_read_edge_arrow_line() -> None:
    graph = read(str(TEST_DATA_DIR / "edge_arrow_line.graphml"))
    assert graph is not None
    # ARROW->LINE reverses to LINE->ARROW which is DIRECTED
    from causaliq_core.graph import EdgeType

    # The edge exists and should be directed type
    assert ("A", "B") in graph.edges
    assert graph.edges[("A", "B")] == EdgeType.DIRECTED


# Test ARROW -> CIRCLE endpoint produces semidirected (o->) with reversal.
def test_graphml_read_edge_arrow_circle() -> None:
    graph = read(str(TEST_DATA_DIR / "edge_arrow_circle.graphml"))
    assert graph is not None
    assert isinstance(graph, SDG)
    from causaliq_core.graph import EdgeType

    # ARROW->CIRCLE reverses to CIRCLE->ARROW which is SEMIDIRECTED (o->)
    assert graph.edges[("A", "B")] == EdgeType.SEMIDIRECTED


# Test CIRCLE -> ARROW endpoint produces semidirected edge (o->).
def test_graphml_read_edge_circle_arrow() -> None:
    graph = read(str(TEST_DATA_DIR / "edge_circle_arrow.graphml"))
    assert graph is not None
    assert isinstance(graph, SDG)
    from causaliq_core.graph import EdgeType

    assert graph.edges[("A", "B")] == EdgeType.SEMIDIRECTED


# Test CIRCLE -> LINE endpoint produces semiundirected edge (o-).
def test_graphml_read_edge_circle_line() -> None:
    graph = read(str(TEST_DATA_DIR / "edge_circle_line.graphml"))
    assert graph is not None
    assert isinstance(graph, SDG)
    from causaliq_core.graph import EdgeType

    assert graph.edges[("A", "B")] == EdgeType.SEMIUNDIRECTED


# Test CIRCLE -> CIRCLE endpoint produces nondirected edge (o-o).
def test_graphml_read_edge_circle_circle() -> None:
    graph = read(str(TEST_DATA_DIR / "edge_circle_circle.graphml"))
    assert graph is not None
    assert isinstance(graph, SDG)
    from causaliq_core.graph import EdgeType

    assert graph.edges[("A", "B")] == EdgeType.NONDIRECTED


# Test file with all 9 edge endpoint combinations.
def test_graphml_read_all_edge_endpoints() -> None:
    graph = read(str(TEST_DATA_DIR / "all_edge_endpoints.graphml"))
    assert graph is not None
    assert isinstance(graph, SDG)
    assert len(graph.nodes) == 10
    assert len(graph.edges) == 9


# =============================================================================
# Tests for error cases and edge coverage
# =============================================================================


# Test read fails on node without id attribute (line 155).
def test_graphml_read_fileformat_error_node_no_id() -> None:
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "node_no_id.graphml"))


# Test read fails on invalid edge type symbol (line 303).
def test_graphml_read_fileformat_error_invalid_edge_symbol() -> None:
    with pytest.raises(FileFormatError):
        read(str(TEST_DATA_DIR / "invalid_edge_symbol.graphml"))


# Test PAG with edgeType symbols triggers has_non_pdag (line 225).
def test_graphml_read_pag_edgetype_symbol_ok() -> None:
    graph = read(str(TEST_DATA_DIR / "pag_edgetype_symbol.graphml"))
    assert graph is not None
    assert isinstance(graph, SDG)
    assert len(graph.nodes) == 3
