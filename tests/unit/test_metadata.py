"""Unit tests for the standard metadata envelope."""

import pytest

from causaliq_core.metadata import (
    PROVENANCE_KEYS,
    RESERVED_KEYS,
    SCHEMA_VERSION,
    MetadataError,
    build_metadata,
    is_v2_metadata,
    normalise_metadata,
    split_metadata,
)


# Schema version is the documented value
def test_schema_version_is_two():
    assert SCHEMA_VERSION == 2


# Reserved keys name the four envelope blocks
def test_reserved_keys_cover_envelope_blocks():
    assert RESERVED_KEYS == {
        "provenance",
        "parameters",
        "result",
        "history",
    }


# Provenance uses the standard field names in the documented order
def test_provenance_keys_are_standard():
    assert PROVENANCE_KEYS == (
        "provider",
        "provider_version",
        "workflow_version",
        "action",
        "started",
        "elapsed",
        "environment",
    )


# Build returns all four envelope blocks
def test_build_metadata_returns_envelope_blocks():
    metadata = build_metadata(
        provider="causaliq-discovery",
        action="learn_graph",
        parameters={"algorithm": "hc"},
        result={"status": "ok"},
    )
    assert set(metadata) == RESERVED_KEYS


# Build records provider and action in provenance
def test_build_metadata_records_provider_and_action():
    metadata = build_metadata(
        provider="causaliq-discovery",
        action="learn_graph",
        parameters={},
        result={},
    )
    provenance = metadata["provenance"]
    assert provenance["provider"] == "causaliq-discovery"
    assert provenance["action"] == "learn_graph"


# Build keeps every provenance key, defaulting optional values to None
def test_build_metadata_defaults_optional_provenance():
    metadata = build_metadata(
        provider="provider",
        action="action",
        parameters={},
        result={},
    )
    provenance = metadata["provenance"]
    assert set(provenance) == set(PROVENANCE_KEYS)
    assert provenance["provider_version"] is None
    assert provenance["started"] is None
    assert provenance["elapsed"] is None
    assert provenance["environment"] is None


# Build copies the parameter and result mappings
def test_build_metadata_copies_blocks():
    parameters = {"algorithm": "hc"}
    result = {"status": "ok"}
    metadata = build_metadata("provider", "action", parameters, result)
    parameters["algorithm"] = "pc"
    result["status"] = "error"
    assert metadata["parameters"] == {"algorithm": "hc"}
    assert metadata["result"] == {"status": "ok"}


# Build copies the environment mapping
def test_build_metadata_copies_environment():
    environment = {"python": "3.12.4"}
    metadata = build_metadata(
        "provider",
        "action",
        {},
        {},
        environment=environment,
    )
    environment["python"] = "3.11.0"
    assert metadata["provenance"]["environment"] == {"python": "3.12.4"}


# Build rejects an empty provider name
@pytest.mark.parametrize("provider", ["", "   ", None])
def test_build_metadata_rejects_empty_provider(provider):
    with pytest.raises(MetadataError):
        build_metadata(provider, "action", {}, {})


# Build rejects an empty action name
@pytest.mark.parametrize("action", ["", "   ", None])
def test_build_metadata_rejects_empty_action(action):
    with pytest.raises(MetadataError):
        build_metadata("provider", action, {}, {})


# Build rejects non-mapping parameter and result blocks
@pytest.mark.parametrize("parameters,result", [([], {}), ({}, []), (None, {})])
def test_build_metadata_rejects_non_mapping_blocks(parameters, result):
    with pytest.raises(MetadataError):
        build_metadata("provider", "action", parameters, result)


# Build rejects a non-mapping history block
def test_build_metadata_rejects_non_mapping_history():
    with pytest.raises(MetadataError):
        build_metadata("provider", "action", {}, {}, history=[])


# A built envelope is recognised as version 2
def test_is_v2_metadata_accepts_envelope():
    metadata = build_metadata("provider", "action", {}, {})
    assert is_v2_metadata(metadata) is True


# Legacy provider blocks are not version 2
def test_is_v2_metadata_rejects_legacy():
    assert is_v2_metadata({"provider": {"action": {}}}) is False


# Non-mapping values are not version 2
@pytest.mark.parametrize("value", [None, [], "metadata"])
def test_is_v2_metadata_rejects_non_mapping(value):
    assert is_v2_metadata(value) is False


# Normalising version 2 fills missing blocks and provenance keys
def test_normalise_metadata_completes_v2():
    metadata = normalise_metadata({"provenance": {"provider": "p"}})
    assert metadata["parameters"] == {}
    assert metadata["result"] == {}
    assert metadata["history"] == {}
    assert metadata["provenance"]["action"] is None


# Normalising version 2 accepts an empty provenance block
def test_normalise_metadata_accepts_empty_provenance():
    metadata = normalise_metadata({"provenance": {}})
    assert set(metadata["provenance"]) == set(PROVENANCE_KEYS)
    assert metadata["provenance"]["provider"] is None


# Normalising version 2 drops obsolete provenance keys
def test_normalise_metadata_drops_obsolete_provenance():
    metadata = normalise_metadata(
        {
            "provenance": {
                "provider": "p",
                "started_at": "2026-01-01T00:00:00+00:00",
                "finished_at": "2026-01-01T00:00:01+00:00",
                "duration_seconds": 1.0,
            }
        }
    )
    assert set(metadata["provenance"]) == set(PROVENANCE_KEYS)
    assert metadata["provenance"]["started"] is None
    assert metadata["provenance"]["elapsed"] is None


# Normalising a single legacy block moves its fields to result
def test_normalise_metadata_converts_single_legacy_block():
    metadata = normalise_metadata(
        {"causaliq-discovery": {"learn_graph": {"status": "ok"}}}
    )
    assert metadata["provenance"]["provider"] == "causaliq-discovery"
    assert metadata["provenance"]["action"] == "learn_graph"
    assert metadata["parameters"] == {}
    assert metadata["result"] == {"status": "ok"}
    assert metadata["history"] == {}


# Normalising multiple legacy blocks keeps earlier blocks as history
def test_normalise_metadata_converts_multiple_legacy_blocks():
    metadata = normalise_metadata(
        {
            "causaliq-discovery": {"learn_graph": {"status": "ok"}},
            "causaliq-analysis": {"evaluate_graph": {"f1": 0.9}},
        }
    )
    assert metadata["provenance"]["provider"] == "causaliq-analysis"
    assert metadata["result"] == {"f1": 0.9}
    assert metadata["history"] == {
        "causaliq-discovery.learn_graph": {
            "parameters": {},
            "result": {"status": "ok"},
        }
    }


# Normalising ignores reserved keys alongside legacy provider blocks.
def test_normalise_metadata_skips_reserved_keys():
    metadata = normalise_metadata(
        {"history": {}, "provider": {"action": {"status": "ok"}}}
    )
    assert metadata["provenance"]["provider"] == "provider"
    assert metadata["result"] == {"status": "ok"}


# Normalising empty metadata returns an empty envelope
def test_normalise_metadata_handles_empty_mapping():
    metadata = normalise_metadata({})
    assert metadata["provenance"]["provider"] is None
    assert metadata["parameters"] == {}
    assert metadata["result"] == {}
    assert metadata["history"] == {}


# Normalising rejects a non-mapping value
def test_normalise_metadata_rejects_non_mapping():
    with pytest.raises(MetadataError):
        normalise_metadata([])


# Normalising a flat mapping places it in the result block.
def test_normalise_metadata_treats_flat_mapping_as_result():
    metadata = normalise_metadata({"seed": 0, "status": "ok"})
    assert metadata["result"] == {"seed": 0, "status": "ok"}
    assert metadata["provenance"]["provider"] is None


# Normalising treats a scalar provider value as a flat result field.
def test_normalise_metadata_treats_scalar_provider_as_result():
    metadata = normalise_metadata({"causaliq-discovery": "not-a-dict"})
    assert metadata["result"] == {"causaliq-discovery": "not-a-dict"}


# Normalising treats a scalar action value as a flat result field.
def test_normalise_metadata_treats_scalar_action_as_result():
    metadata = normalise_metadata(
        {"causaliq-discovery": {"learn_graph": "bad"}}
    )
    assert metadata["result"] == {"causaliq-discovery": {"learn_graph": "bad"}}


# Splitting returns the four blocks
def test_split_metadata_returns_parts():
    metadata = build_metadata(
        "provider",
        "action",
        {"algorithm": "hc"},
        {"status": "ok"},
    )
    parts = split_metadata(metadata)
    assert parts.parameters == {"algorithm": "hc"}
    assert parts.result == {"status": "ok"}
    assert parts.history == {}
    assert parts.provenance["provider"] == "provider"


# Splitting normalises legacy metadata
def test_split_metadata_normalises_legacy():
    parts = split_metadata({"provider": {"action": {"status": "ok"}}})
    assert parts.result == {"status": "ok"}
    assert parts.provenance["action"] == "action"
