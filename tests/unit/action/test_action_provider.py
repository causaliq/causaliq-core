"""Unit tests for causaliq_core.action.provider."""

import pytest

from causaliq_core import (
    ActionResult,
    ActionValidationError,
    CausalIQActionProvider,
    TokenCache,
)

# ---------------------------------------------------------------------------
# CausalIQActionProvider ABC tests
# ---------------------------------------------------------------------------


# Test CausalIQActionProvider is abstract and cannot be instantiated.
def test_causaliq_action_provider_is_abstract() -> None:
    with pytest.raises(TypeError, match="abstract"):
        CausalIQActionProvider()  # type: ignore


# Test validate_parameters raises error for unsupported action.
def test_validate_parameters_raises_for_unsupported_action() -> None:
    class TestProvider(CausalIQActionProvider):
        name = "test-provider"
        supported_actions = {"allowed"}

        def _execute(
            self, action, parameters, mode, context, logger
        ) -> ActionResult:
            return ("success", {}, [])

    provider = TestProvider()
    with pytest.raises(ActionValidationError, match="does not support"):
        provider.validate_parameters("unknown", {})


# Test validate_parameters raises error for missing action.
def test_validate_parameters_raises_for_missing_action() -> None:
    class TestProvider(CausalIQActionProvider):
        name = "test-provider"
        supported_actions = {"allowed"}

        def _execute(
            self, action, parameters, mode, context, logger
        ) -> ActionResult:
            return ("success", {}, [])

    provider = TestProvider()
    with pytest.raises(ActionValidationError, match="Missing 'action'"):
        provider.validate_parameters("", {})
    with pytest.raises(ActionValidationError, match="Missing 'action'"):
        provider.validate_parameters(None, {})


# Test subclass can implement required methods.
def test_provider_subclass_implementation() -> None:
    class TestProvider(CausalIQActionProvider):
        name = "test-provider"
        version = "1.0.0"
        supported_actions = {"test"}
        supported_types = {"json"}

        def _execute(
            self, action, parameters, mode, context, logger
        ) -> ActionResult:
            return ("success", {"action": action}, [])

    provider = TestProvider()
    assert provider.name == "test-provider"
    assert provider.supported_actions == {"test"}
    assert provider.supported_types == {"json"}

    status, metadata, objects = provider.run("test", {}, mode="run")
    assert status == "success"
    assert metadata == {"action": "test"}
    assert objects == []


# Test compress raises NotImplementedError for unsupported type.
def test_compress_unsupported_type() -> None:
    class TestProvider(CausalIQActionProvider):
        supported_types = {"json"}

        def _execute(
            self, action, parameters, mode, context, logger
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

        def _execute(
            self, action, parameters, mode, context, logger
        ) -> ActionResult:
            return ("success", {}, [])

    provider = TestProvider()
    with TokenCache(":memory:") as cache:
        with pytest.raises(NotImplementedError, match="does not support"):
            provider.decompress("xml", b"data", cache)


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
