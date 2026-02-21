"""Unit tests for PDG GraphML I/O."""

import tempfile
from io import StringIO
from pathlib import Path

import pytest

from causaliq_core.graph import PDG, EdgeProbabilities
from causaliq_core.graph.io.graphml import read_pdg, write_pdg
from causaliq_core.utils import FileFormatError

# --- write_pdg tests ---


# Test write_pdg produces valid GraphML.
def test_write_pdg_basic() -> None:
    """write_pdg produces valid GraphML with probability attributes."""
    pdg = PDG(
        ["A", "B"],
        {("A", "B"): EdgeProbabilities(forward=0.8, none=0.2)},
    )
    buffer = StringIO()
    write_pdg(pdg, buffer)

    xml = buffer.getvalue()
    assert '<?xml version="1.0"' in xml
    assert "graphml" in xml
    assert 'edgedefault="undirected"' in xml
    assert 'node id="A"' in xml
    assert 'node id="B"' in xml
    assert "p_forward" in xml
    assert "0.8" in xml


# Test write_pdg omits edges with p_none=1.0.
def test_write_pdg_omits_no_edge() -> None:
    """write_pdg omits edges where p_exist = 0."""
    pdg = PDG(
        ["A", "B", "C"],
        {
            ("A", "B"): EdgeProbabilities(forward=0.5, none=0.5),
            ("A", "C"): EdgeProbabilities(none=1.0),  # Should be omitted
        },
    )
    buffer = StringIO()
    write_pdg(pdg, buffer)

    xml = buffer.getvalue()
    assert 'source="A" target="B"' in xml
    assert 'source="A" target="C"' not in xml


# Test write_pdg uses 4 significant figures.
def test_write_pdg_precision() -> None:
    """write_pdg outputs 4 significant figures."""
    pdg = PDG(
        ["A", "B"],
        {("A", "B"): EdgeProbabilities(forward=0.123456789, none=0.876543211)},
    )
    buffer = StringIO()
    write_pdg(pdg, buffer)

    xml = buffer.getvalue()
    # Should be rounded to 4 s.f.: 0.1235
    assert "0.1235" in xml
    assert "0.8765" in xml


# Test write_pdg validates pdg type.
def test_write_pdg_invalid_type() -> None:
    """write_pdg raises for non-PDG argument."""
    buffer = StringIO()
    with pytest.raises(TypeError, match="must be PDG"):
        write_pdg("not a PDG", buffer)  # type: ignore[arg-type]


# Test write_pdg validates file type.
def test_write_pdg_invalid_file_type() -> None:
    """write_pdg raises for invalid file type."""
    pdg = PDG(["A", "B"])
    with pytest.raises(TypeError, match="must be str, Path"):
        write_pdg(pdg, 123)  # type: ignore[arg-type]


# Test write_pdg validates file suffix.
def test_write_pdg_invalid_suffix() -> None:
    """write_pdg raises for non-.graphml suffix."""
    pdg = PDG(["A", "B"])
    with pytest.raises(ValueError, match="bad file suffix"):
        write_pdg(pdg, "test.xml")


# --- read_pdg tests ---


# Test read_pdg parses valid GraphML.
def test_read_pdg_basic() -> None:
    """read_pdg parses valid PDG GraphML."""
    xml = """<?xml version="1.0"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="p_forward" for="edge" attr.type="double"/>
  <key id="p_backward" for="edge" attr.type="double"/>
  <key id="p_undirected" for="edge" attr.type="double"/>
  <key id="p_none" for="edge" attr.type="double"/>
  <graph edgedefault="undirected">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B">
      <data key="p_forward">0.7</data>
      <data key="p_backward">0.2</data>
      <data key="p_undirected">0.05</data>
      <data key="p_none">0.05</data>
    </edge>
  </graph>
</graphml>"""

    pdg = read_pdg(StringIO(xml))
    assert pdg.nodes == ["A", "B"]
    probs = pdg.get_probabilities("A", "B")
    assert probs.forward == 0.7
    assert probs.backward == 0.2
    assert probs.undirected == 0.05
    assert probs.none == 0.05


# Test read_pdg canonicalises edge order.
def test_read_pdg_canonical_order() -> None:
    """read_pdg canonicalises edges where source > target."""
    xml = """<?xml version="1.0"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph edgedefault="undirected">
    <node id="A"/>
    <node id="B"/>
    <edge source="B" target="A">
      <data key="p_forward">0.7</data>
      <data key="p_backward">0.2</data>
      <data key="p_undirected">0.05</data>
      <data key="p_none">0.05</data>
    </edge>
  </graph>
</graphml>"""

    pdg = read_pdg(StringIO(xml))
    # Edge should be stored as (A, B) with swapped forward/backward
    probs = pdg.get_probabilities("A", "B")
    assert probs.forward == 0.2  # Was p_backward in file (B->A)
    assert probs.backward == 0.7  # Was p_forward in file (B->A)


# Test read_pdg handles missing probability attributes.
def test_read_pdg_missing_probs() -> None:
    """read_pdg raises for missing probability attributes."""
    xml = """<?xml version="1.0"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph edgedefault="undirected">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B">
      <!-- Missing probability data -->
    </edge>
  </graph>
</graphml>"""

    with pytest.raises(FileFormatError, match="missing probability"):
        read_pdg(StringIO(xml))


# Test read_pdg validates probability sum.
def test_read_pdg_invalid_sum() -> None:
    """read_pdg raises for probabilities not summing to 1.0."""
    xml = """<?xml version="1.0"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph edgedefault="undirected">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B">
      <data key="p_forward">0.5</data>
      <data key="p_backward">0.5</data>
      <data key="p_undirected">0.5</data>
      <data key="p_none">0.0</data>
    </edge>
  </graph>
</graphml>"""

    with pytest.raises(FileFormatError, match="sum to 1.0"):
        read_pdg(StringIO(xml))


# Test read_pdg validates probability value format.
def test_read_pdg_invalid_value() -> None:
    """read_pdg raises for invalid probability values."""
    xml = """<?xml version="1.0"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph edgedefault="undirected">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B">
      <data key="p_forward">not_a_number</data>
      <data key="p_backward">0.0</data>
      <data key="p_undirected">0.0</data>
      <data key="p_none">1.0</data>
    </edge>
  </graph>
</graphml>"""

    with pytest.raises(FileFormatError, match="invalid probability"):
        read_pdg(StringIO(xml))


# Test read_pdg validates file type.
def test_read_pdg_invalid_file_type() -> None:
    """read_pdg raises for invalid file type."""
    with pytest.raises(TypeError, match="must be str, Path"):
        read_pdg(123)  # type: ignore[arg-type]


# Test read_pdg validates file suffix.
def test_read_pdg_invalid_suffix() -> None:
    """read_pdg raises for non-.graphml suffix."""
    with pytest.raises(ValueError, match="bad file suffix"):
        read_pdg("test.xml")


# Test read_pdg handles non-namespaced GraphML.
def test_read_pdg_no_namespace() -> None:
    """read_pdg handles GraphML without namespace."""
    xml = """<?xml version="1.0"?>
<graphml>
  <graph edgedefault="undirected">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B">
      <data key="p_forward">0.6</data>
      <data key="p_backward">0.0</data>
      <data key="p_undirected">0.0</data>
      <data key="p_none">0.4</data>
    </edge>
  </graph>
</graphml>"""

    pdg = read_pdg(StringIO(xml))
    assert pdg.nodes == ["A", "B"]


# Test read_pdg raises for invalid XML.
def test_read_pdg_invalid_xml() -> None:
    """read_pdg raises for invalid XML."""
    with pytest.raises(FileFormatError, match="invalid XML"):
        read_pdg(StringIO("<not valid xml"))


# Test read_pdg raises for non-GraphML root.
def test_read_pdg_not_graphml() -> None:
    """read_pdg raises for non-GraphML root element."""
    xml = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
</svg>"""

    with pytest.raises(FileFormatError, match="not a GraphML file"):
        read_pdg(StringIO(xml))


# Test read_pdg raises for missing graph element.
def test_read_pdg_no_graph() -> None:
    """read_pdg raises for missing graph element."""
    xml = """<?xml version="1.0"?>
<graphml>
</graphml>"""

    with pytest.raises(FileFormatError, match="no graph element"):
        read_pdg(StringIO(xml))


# Test read_pdg raises for no nodes.
def test_read_pdg_no_nodes() -> None:
    """read_pdg raises for graph with no nodes."""
    xml = """<?xml version="1.0"?>
<graphml>
  <graph edgedefault="undirected">
  </graph>
</graphml>"""

    with pytest.raises(FileFormatError, match="no nodes"):
        read_pdg(StringIO(xml))


# --- Round-trip tests ---


# Test write then read produces equivalent PDG.
def test_pdg_graphml_roundtrip() -> None:
    """write_pdg then read_pdg produces equivalent PDG."""
    original = PDG(
        ["A", "B", "C"],
        {
            ("A", "B"): EdgeProbabilities(
                forward=0.6, backward=0.2, undirected=0.1, none=0.1
            ),
            ("B", "C"): EdgeProbabilities(undirected=0.9, none=0.1),
        },
    )

    buffer = StringIO()
    write_pdg(original, buffer)
    buffer.seek(0)
    restored = read_pdg(buffer)

    assert restored.nodes == original.nodes

    for source, target in original.node_pairs():
        orig_probs = original.get_probabilities(source, target)
        rest_probs = restored.get_probabilities(source, target)

        # Allow for 4 s.f. rounding
        assert abs(orig_probs.forward - rest_probs.forward) < 0.001
        assert abs(orig_probs.backward - rest_probs.backward) < 0.001
        assert abs(orig_probs.undirected - rest_probs.undirected) < 0.001
        assert abs(orig_probs.none - rest_probs.none) < 0.001


# Test roundtrip with many nodes.
def test_pdg_graphml_roundtrip_large() -> None:
    """Round-trip with larger graph."""
    nodes = [f"V{i}" for i in range(10)]
    edges = {}

    # Create some edges with various probability patterns
    edges[("V0", "V1")] = EdgeProbabilities(forward=1.0, none=0.0)
    edges[("V2", "V3")] = EdgeProbabilities(backward=0.5, none=0.5)
    edges[("V4", "V5")] = EdgeProbabilities(undirected=0.8, none=0.2)
    edges[("V6", "V7")] = EdgeProbabilities(
        forward=0.25, backward=0.25, undirected=0.25, none=0.25
    )

    original = PDG(nodes, edges)

    buffer = StringIO()
    write_pdg(original, buffer)
    buffer.seek(0)
    restored = read_pdg(buffer)

    assert restored.nodes == original.nodes
    assert len(restored.edges) == len(original.edges)


# --- File path tests ---


# Test read_pdg from file path.
def test_read_pdg_from_file_path() -> None:
    """read_pdg reads from file path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".graphml", delete=False
    ) as f:
        f.write(
            """<?xml version="1.0"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph edgedefault="undirected">
    <node id="A"/>
    <node id="B"/>
    <edge source="A" target="B">
      <data key="p_forward">0.6</data>
      <data key="p_backward">0.2</data>
      <data key="p_undirected">0.1</data>
      <data key="p_none">0.1</data>
    </edge>
  </graph>
</graphml>"""
        )
        path = f.name

    try:
        pdg = read_pdg(path)
        assert pdg.nodes == ["A", "B"]
        probs = pdg.get_probabilities("A", "B")
        assert probs.forward == 0.6
    finally:
        Path(path).unlink()


# Test write_pdg to file path.
def test_write_pdg_to_file_path() -> None:
    """write_pdg writes to file path."""
    pdg = PDG(
        ["A", "B"],
        {("A", "B"): EdgeProbabilities(forward=0.7, none=0.3)},
    )

    with tempfile.NamedTemporaryFile(suffix=".graphml", delete=False) as f:
        path = f.name

    try:
        write_pdg(pdg, path)

        # Read back and verify
        restored = read_pdg(path)
        assert restored.nodes == ["A", "B"]
        probs = restored.get_probabilities("A", "B")
        assert probs.forward == 0.7
    finally:
        Path(path).unlink()


# Test read_pdg raises for edge without source attribute.
def test_read_pdg_edge_missing_source() -> None:
    """read_pdg raises for edge without source attribute."""
    xml = """<?xml version="1.0"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph edgedefault="undirected">
    <node id="A"/>
    <node id="B"/>
    <edge target="B">
      <data key="p_forward">0.5</data>
      <data key="p_backward">0.0</data>
      <data key="p_undirected">0.0</data>
      <data key="p_none">0.5</data>
    </edge>
  </graph>
</graphml>"""

    with pytest.raises(FileFormatError, match="without source or target"):
        read_pdg(StringIO(xml))


# Test read_pdg raises for edge without target attribute.
def test_read_pdg_edge_missing_target() -> None:
    """read_pdg raises for edge without target attribute."""
    xml = """<?xml version="1.0"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph edgedefault="undirected">
    <node id="A"/>
    <node id="B"/>
    <edge source="A">
      <data key="p_forward">0.5</data>
      <data key="p_backward">0.0</data>
      <data key="p_undirected">0.0</data>
      <data key="p_none">0.5</data>
    </edge>
  </graph>
</graphml>"""

    with pytest.raises(FileFormatError, match="without source or target"):
        read_pdg(StringIO(xml))
