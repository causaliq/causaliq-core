"""Unit tests for causaliq_core.action module."""

import json
from io import StringIO

import pytest

from causaliq_core import (
    ActionExecutionError,
    ActionInput,
    ActionOutput,
    ActionResult,
    ActionValidationError,
    BaseActionProvider,
    CausalIQActionProvider,
    CoreActionProvider,
    TokenCache,
)
from causaliq_core.graph import SDG
from causaliq_core.graph.io import graphml

# ---------------------------------------------------------------------------
# ActionInput and ActionOutput tests
# ---------------------------------------------------------------------------


# Test ActionInput dataclass has expected fields and defaults.
def test_action_input_defaults() -> None:
    inp = ActionInput(name="test", description="A test input")
    assert inp.name == "test"
    assert inp.description == "A test input"
    assert inp.required is False
    assert inp.default is None
    assert inp.type_hint == "Any"


# Test ActionInput with all fields specified.
def test_action_input_full() -> None:
    inp = ActionInput(
        name="param",
        description="A parameter",
        required=True,
        default="value",
        type_hint="str",
    )
    assert inp.name == "param"
    assert inp.required is True
    assert inp.default == "value"
    assert inp.type_hint == "str"


# Test ActionOutput dataclass has expected fields.
def test_action_output_fields() -> None:
    out = ActionOutput(name="result", description="Output result", value=42)
    assert out.name == "result"
    assert out.description == "Output result"
    assert out.value == 42


# ---------------------------------------------------------------------------
# Exception tests
# ---------------------------------------------------------------------------


# Test ActionExecutionError is proper exception.
def test_action_execution_error() -> None:
    with pytest.raises(ActionExecutionError, match="failed"):
        raise ActionExecutionError("Action failed")


# Test ActionValidationError is proper exception.
def test_action_validation_error() -> None:
    with pytest.raises(ActionValidationError, match="invalid"):
        raise ActionValidationError("Input invalid")


# ---------------------------------------------------------------------------
# CausalIQActionProvider ABC tests
# ---------------------------------------------------------------------------


# Test CausalIQActionProvider is abstract and cannot be instantiated.
def test_causaliq_action_provider_is_abstract() -> None:
    with pytest.raises(TypeError, match="abstract"):
        CausalIQActionProvider()  # type: ignore


# Test BaseActionProvider is alias for CausalIQActionProvider.
def test_base_action_provider_alias() -> None:
    assert BaseActionProvider is CausalIQActionProvider


# Test subclass can implement required methods.
def test_provider_subclass_implementation() -> None:
    class TestProvider(CausalIQActionProvider):
        name = "test-provider"
        version = "1.0.0"
        supported_actions = {"test"}
        supported_types = {"json"}

        def run(
            self, action, parameters, mode="dry-run", context=None, logger=None
        ) -> ActionResult:
            self._execution_metadata = {"action": action}
            return ("success", {"action": action}, [])

    provider = TestProvider()
    assert provider.name == "test-provider"
    assert provider.supported_actions == {"test"}
    assert provider.supported_types == {"json"}

    status, metadata, objects = provider.run("test", {})
    assert status == "success"
    assert metadata == {"action": "test"}
    assert objects == []


# Test validate_parameters raises on unsupported action.
def test_validate_parameters_unsupported_action() -> None:
    class TestProvider(CausalIQActionProvider):
        supported_actions = {"action_a", "action_b"}

        def run(
            self, action, parameters, mode="dry-run", context=None, logger=None
        ) -> ActionResult:
            return ("success", {}, [])

    provider = TestProvider()
    with pytest.raises(ActionValidationError, match="Unsupported action"):
        provider.validate_parameters("unknown_action", {})


# Test validate_parameters accepts supported action.
def test_validate_parameters_supported_action() -> None:
    class TestProvider(CausalIQActionProvider):
        supported_actions = {"action_a"}

        def run(
            self, action, parameters, mode="dry-run", context=None, logger=None
        ) -> ActionResult:
            return ("success", {}, [])

    provider = TestProvider()
    result = provider.validate_parameters("action_a", {})
    assert result is True


# Test get_action_metadata returns base metadata.
def test_get_action_metadata_returns_base() -> None:
    class TestProvider(CausalIQActionProvider):
        name = "test"
        version = "2.0.0"

        def run(
            self, action, parameters, mode="dry-run", context=None, logger=None
        ) -> ActionResult:
            return ("success", {}, [])

    provider = TestProvider()
    metadata = provider.get_action_metadata()
    assert metadata["action_name"] == "test"
    assert metadata["action_version"] == "2.0.0"


# Test get_action_metadata includes execution metadata.
def test_get_action_metadata_includes_execution() -> None:
    class TestProvider(CausalIQActionProvider):
        name = "test"
        version = "1.0.0"

        def run(
            self, action, parameters, mode="dry-run", context=None, logger=None
        ) -> ActionResult:
            self._execution_metadata = {"custom": "value", "count": 42}
            return ("success", {}, [])

    provider = TestProvider()
    provider.run("action", {})
    metadata = provider.get_action_metadata()
    assert metadata["action_name"] == "test"
    assert metadata["custom"] == "value"
    assert metadata["count"] == 42


# Test compress raises NotImplementedError for unsupported type.
def test_compress_unsupported_type() -> None:
    class TestProvider(CausalIQActionProvider):
        supported_types = {"json"}

        def run(
            self, action, parameters, mode="dry-run", context=None, logger=None
        ) -> ActionResult:
            return ("success", {}, [])

    provider = TestProvider()
    with TokenCache(":memory:") as cache:
        with pytest.raises(NotImplementedError, match="does not support"):
            provider.compress("xml", "<data/>", cache)


# Test decompress raises NotImplementedError for unsupported type.
def test_decompress_unsupported_type() -> None:
    class TestProvider(CausalIQActionProvider):
        supported_types = {"json"}

        def run(
            self, action, parameters, mode="dry-run", context=None, logger=None
        ) -> ActionResult:
            return ("success", {}, [])

    provider = TestProvider()
    with TokenCache(":memory:") as cache:
        with pytest.raises(NotImplementedError, match="does not support"):
            provider.decompress("xml", b"data", cache)


# ---------------------------------------------------------------------------
# CoreActionProvider tests
# ---------------------------------------------------------------------------


# Test CoreActionProvider has correct metadata.
def test_core_provider_metadata() -> None:
    provider = CoreActionProvider()
    assert provider.name == "causaliq-core"
    assert provider.version == "1.0.0"
    assert provider.supported_types == {"graphml", "json"}
    assert provider.supported_actions == set()


# Test CoreActionProvider run returns skipped status.
def test_core_provider_run_returns_skipped() -> None:
    provider = CoreActionProvider()
    status, metadata, objects = provider.run("any", {})
    assert status == "skipped"
    assert metadata == {}
    assert objects == []


# Test CoreActionProvider compresses graphml to compact bytes.
def test_core_provider_compress_graphml() -> None:
    provider = CoreActionProvider()
    graph = SDG(nodes=["A", "B"], edges=[("A", "->", "B")])
    buffer = StringIO()
    graphml.write(graph, buffer)
    graphml_content = buffer.getvalue()

    with TokenCache(":memory:") as cache:
        blob = provider.compress("graphml", graphml_content, cache)
        assert isinstance(blob, bytes)
        assert len(blob) < len(graphml_content)  # Should be compressed


# Test CoreActionProvider decompresses graphml from bytes.
def test_core_provider_decompress_graphml() -> None:
    provider = CoreActionProvider()
    graph = SDG(nodes=["X", "Y"], edges=[("X", "->", "Y")])
    buffer = StringIO()
    graphml.write(graph, buffer)
    original = buffer.getvalue()

    with TokenCache(":memory:") as cache:
        blob = provider.compress("graphml", original, cache)
        restored = provider.decompress("graphml", blob, cache)

    # Parse restored graphml to verify structure
    restored_graph = graphml.read(StringIO(restored))
    assert list(restored_graph.nodes) == ["X", "Y"]
    assert len(restored_graph.edges) == 1


# Test CoreActionProvider compresses json to tokenised bytes.
def test_core_provider_compress_json() -> None:
    provider = CoreActionProvider()
    data = {"key": "value", "number": 42}
    json_content = json.dumps(data)

    with TokenCache(":memory:") as cache:
        blob = provider.compress("json", json_content, cache)
        assert isinstance(blob, bytes)


# Test CoreActionProvider decompresses json from bytes.
def test_core_provider_decompress_json() -> None:
    provider = CoreActionProvider()
    data = {"nested": {"a": 1, "b": 2}, "list": [1, 2, 3]}
    original = json.dumps(data)

    with TokenCache(":memory:") as cache:
        blob = provider.compress("json", original, cache)
        restored = provider.decompress("json", blob, cache)

    parsed = json.loads(restored)
    assert parsed == data


# Test CoreActionProvider roundtrip preserves json list.
def test_core_provider_json_list_roundtrip() -> None:
    provider = CoreActionProvider()
    data = [1, 2, 3, "four"]
    original = json.dumps(data)

    with TokenCache(":memory:") as cache:
        blob = provider.compress("json", original, cache)
        restored = provider.decompress("json", blob, cache)

    parsed = json.loads(restored)
    assert parsed == data


# Test CoreActionProvider raises NotImplementedError for unsupported type.
def test_core_provider_compress_unsupported() -> None:
    provider = CoreActionProvider()
    with TokenCache(":memory:") as cache:
        with pytest.raises(NotImplementedError, match="does not support"):
            provider.compress("xml", "<data/>", cache)


# Test CoreActionProvider raises NotImplementedError for unsupported type.
def test_core_provider_decompress_unsupported() -> None:
    provider = CoreActionProvider()
    with TokenCache(":memory:") as cache:
        with pytest.raises(NotImplementedError, match="does not support"):
            provider.decompress("csv", b"a,b,c", cache)


# Test compress raises ValueError for too many nodes.
def test_core_provider_compress_graphml_too_many_nodes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import MagicMock

    provider = CoreActionProvider()

    # Create mock SDG with >65535 nodes
    mock_sdg = MagicMock()
    mock_sdg.nodes = [f"n{i}" for i in range(65536)]
    mock_sdg.edges = {}

    monkeypatch.setattr(graphml, "read", lambda _: mock_sdg)

    with TokenCache(":memory:") as cache:
        with pytest.raises(ValueError, match="too many nodes"):
            provider.compress("graphml", "<graphml/>", cache)


# Test compress raises ValueError for too many edges.
def test_core_provider_compress_graphml_too_many_edges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from unittest.mock import MagicMock

    from causaliq_core.graph import EdgeType

    provider = CoreActionProvider()

    # Create mock SDG with >65535 edges
    mock_sdg = MagicMock()
    mock_sdg.nodes = ["A", "B"]
    # Create edges dict with >65535 entries (fake keys)
    mock_sdg.edges = {(f"A{i}", "B"): EdgeType.DIRECTED for i in range(65536)}

    monkeypatch.setattr(graphml, "read", lambda _: mock_sdg)

    with TokenCache(":memory:") as cache:
        with pytest.raises(ValueError, match="too many edges"):
            provider.compress("graphml", "<graphml/>", cache)


# Test decompress raises ValueError for short data.
def test_core_provider_decompress_graphml_short_data() -> None:
    provider = CoreActionProvider()
    with TokenCache(":memory:") as cache:
        with pytest.raises(ValueError, match="too short"):
            provider.decompress("graphml", b"\x00", cache)


# Test decompress raises ValueError for truncated node data.
def test_core_provider_decompress_graphml_truncated_nodes() -> None:
    provider = CoreActionProvider()
    with TokenCache(":memory:") as cache:
        # 2 nodes but only 1 byte of token ID (need 4 bytes for 2 tokens)
        blob = b"\x00\x02\x00"  # num_nodes=2, only partial token
        with pytest.raises(ValueError, match="truncated"):
            provider.decompress("graphml", blob, cache)


# Test decompress raises ValueError for unknown token ID.
def test_core_provider_decompress_graphml_unknown_token() -> None:
    provider = CoreActionProvider()
    with TokenCache(":memory:") as cache:
        # 1 node with token ID 9999 (doesn't exist)
        blob = b"\x00\x01\x27\x0f\x00\x00"  # num_nodes=1, token=9999, edges=0
        with pytest.raises(ValueError, match="Unknown token"):
            provider.decompress("graphml", blob, cache)


# Test decompress raises ValueError for truncated edge count.
def test_core_provider_decompress_graphml_truncated_edge_count() -> None:
    provider = CoreActionProvider()
    with TokenCache(":memory:") as cache:
        # Create a token first
        token_id = cache.get_or_create_token("A")
        # 1 node with valid token but no edge count
        blob = b"\x00\x01" + token_id.to_bytes(2, "big")  # Missing edge count
        with pytest.raises(ValueError, match="truncated"):
            provider.decompress("graphml", blob, cache)


# Test decompress raises ValueError for truncated edge data.
def test_core_provider_decompress_graphml_truncated_edges() -> None:
    provider = CoreActionProvider()
    with TokenCache(":memory:") as cache:
        # Create tokens
        t1 = cache.get_or_create_token("A")
        t2 = cache.get_or_create_token("B")
        # 2 nodes, 1 edge but edge data truncated
        blob = (
            b"\x00\x02"
            + t1.to_bytes(2, "big")
            + t2.to_bytes(2, "big")
            + b"\x00\x01"  # 1 edge
            + b"\x00\x00"  # Only source idx, missing target and type
        )
        with pytest.raises(ValueError, match="truncated"):
            provider.decompress("graphml", blob, cache)


# Test decompress raises ValueError for invalid node index.
def test_core_provider_decompress_graphml_invalid_node_index() -> None:
    provider = CoreActionProvider()
    with TokenCache(":memory:") as cache:
        t1 = cache.get_or_create_token("A")
        # 1 node, 1 edge with invalid source index (99)
        blob = (
            b"\x00\x01"
            + t1.to_bytes(2, "big")
            + b"\x00\x01"  # 1 edge
            + b"\x00\x63"  # source idx=99 (invalid)
            + b"\x00\x00"  # target idx=0
            + b"\x01"  # edge type=1
        )
        with pytest.raises(ValueError, match="invalid node index"):
            provider.decompress("graphml", blob, cache)


# Test decompress raises ValueError for invalid edge type.
def test_core_provider_decompress_graphml_invalid_edge_type() -> None:
    provider = CoreActionProvider()
    with TokenCache(":memory:") as cache:
        t1 = cache.get_or_create_token("A")
        t2 = cache.get_or_create_token("B")
        # 2 nodes, 1 edge with invalid edge type (99)
        blob = (
            b"\x00\x02"
            + t1.to_bytes(2, "big")
            + t2.to_bytes(2, "big")
            + b"\x00\x01"  # 1 edge
            + b"\x00\x00"  # source idx=0
            + b"\x00\x01"  # target idx=1
            + b"\x63"  # edge type=99 (invalid)
        )
        with pytest.raises(ValueError, match="invalid edge type"):
            provider.decompress("graphml", blob, cache)


# ---------------------------------------------------------------------------
# ActionResult type alias test
# ---------------------------------------------------------------------------


# Test ActionResult is correct tuple type alias.
def test_action_result_type_alias() -> None:
    # ActionResult should be Tuple[str, Dict[str, Any], List[Dict[str, Any]]]
    result: ActionResult = ("success", {"key": "val"}, [{"type": "json"}])
    status, metadata, objects = result
    assert status == "success"
    assert metadata == {"key": "val"}
    assert objects == [{"type": "json"}]
