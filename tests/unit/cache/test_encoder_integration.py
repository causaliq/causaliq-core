"""Integration tests for JsonEncoder with TokenCache.

Tests the complete encoding pipeline including compression efficiency
and round-trip correctness with realistic data.

Migrated from causaliq-knowledge.
"""

import json

import pytest

from causaliq_core.cache import TokenCache
from causaliq_core.cache.encoders import JsonEncoder

# --- Compression efficiency tests ---


# Test that tokenised encoding stores data with reasonable overhead.
def test_compression_ratio_llm_request():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        data = {
            "model": "gpt-4-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                {
                    "role": "user",
                    "content": "Explain the relationship between BMI and "
                    "diabetes risk.",
                },
            ],
            "temperature": 0.7,
            "max_tokens": 500,
        }
        json_size = len(json.dumps(data).encode())
        cache.put_data("test", "json", data)
        blob = cache.get("test", "json")
        assert blob is not None
        blob_size = len(blob)
        ratio = blob_size / json_size
        # Single entry has overhead from 2-byte token IDs
        # Compression benefit comes from token reuse across entries
        assert ratio < 2.0, f"Compression ratio {ratio:.2%} too high"


# Test that repeated structure shares tokens (compression improves with reuse).
def test_compression_repeated_content():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        # Store many similar entries
        for i in range(10):
            data = {
                "messages": [
                    {"role": "user", "content": f"Query {i}: What is BMI?"}
                ],
                "model": "gpt-4",
            }
            cache.put_data(f"entry_{i}", "json", data)

        # Count total tokens - should be much less than 10x first entry
        total_tokens = cache.token_count()
        # With reuse, ~15-25 unique tokens even for 10 entries
        # (structural tokens + "model", "gpt-4", etc. reused)
        assert total_tokens < 50, f"Too many tokens: {total_tokens}"


# Test compression across multiple requests shares tokens.
def test_token_sharing_across_requests():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        # First request
        data1 = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        cache.put_data("req1", "json", data1)
        tokens_after_first = cache.token_count()

        # Second similar request
        data2 = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "World"}],
        }
        cache.put_data("req2", "json", data2)
        tokens_after_second = cache.token_count()

        # Should only add a few new tokens for "World"
        new_tokens = tokens_after_second - tokens_after_first
        assert new_tokens < 5, f"Added {new_tokens} tokens for similar request"


# --- Round-trip correctness tests ---


# Test round-trip with realistic LLM request.
def test_roundtrip_llm_request():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        data = {
            "model": "claude-3-opus",
            "messages": [
                {"role": "system", "content": "You analyse causal graphs."},
                {"role": "user", "content": "Is A -> B plausible?"},
            ],
            "temperature": 0.5,
            "max_tokens": 1000,
            "stream": False,
        }
        cache.put_data("test", "json", data)
        retrieved = cache.get_data("test", "json")
        assert retrieved["model"] == data["model"]
        assert retrieved["messages"] == data["messages"]
        assert retrieved["temperature"] == pytest.approx(data["temperature"])
        assert retrieved["max_tokens"] == data["max_tokens"]
        assert retrieved["stream"] == data["stream"]


# Test round-trip with LLM response containing JSON.
def test_roundtrip_llm_response_with_json():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        # LLM response that contains JSON as string content
        json_result = '{"edges": [{"source": "A", "target": "B"}]}'
        data = {
            "id": "chatcmpl-abc123",
            "object": "chat.completion",
            "created": 1699000000,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": json_result},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 30,
                "total_tokens": 80,
            },
        }
        cache.put_data("test", "json", data)
        retrieved = cache.get_data("test", "json")
        # Verify JSON content preserved
        assert retrieved["choices"][0]["message"]["content"] == json_result
        # Verify numeric fields
        assert retrieved["usage"]["total_tokens"] == 80


# Test round-trip with causal graph structure.
def test_roundtrip_causal_graph():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        data = {
            "nodes": ["BMI", "Diabetes", "Age", "Blood_Pressure"],
            "edges": [
                {"source": "BMI", "target": "Diabetes", "weight": 0.85},
                {"source": "Age", "target": "Diabetes", "weight": 0.72},
                {"source": "Age", "target": "Blood_Pressure", "weight": 0.68},
            ],
            "metadata": {
                "algorithm": "PC",
                "confidence": 0.95,
                "samples": 10000,
            },
        }
        cache.put_data("test", "json", data)
        retrieved = cache.get_data("test", "json")
        assert retrieved["nodes"] == data["nodes"]
        assert len(retrieved["edges"]) == 3
        for orig, ret in zip(data["edges"], retrieved["edges"]):
            assert orig["source"] == ret["source"]
            assert orig["target"] == ret["target"]
            assert orig["weight"] == pytest.approx(ret["weight"])


# Test round-trip with variable specifications.
def test_roundtrip_variable_spec():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        data = {
            "variables": [
                {
                    "name": "BMI",
                    "description": "Body Mass Index",
                    "type": "continuous",
                    "unit": "kg/m^2",
                },
                {
                    "name": "Diabetes",
                    "description": "Diabetes diagnosis",
                    "type": "binary",
                    "values": [0, 1],
                },
            ],
            "domain": "medical",
            "source": "UK Biobank",
        }
        cache.put_data("test", "json", data)
        retrieved = cache.get_data("test", "json")
        assert retrieved == data


# --- Edge cases with realistic data ---


# Test handling of special characters in prompts.
def test_special_chars_in_prompt():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        data = {
            "messages": [
                {
                    "role": "user",
                    "content": "Is A→B or A↔B? Use symbols: ∀x∈X, ∃y∈Y",
                }
            ]
        }
        cache.put_data("test", "json", data)
        retrieved = cache.get_data("test", "json")
        assert retrieved == data


# Test handling of multiline content.
def test_multiline_content():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        content = """This is a multiline prompt.
It contains several lines.
Including empty lines:

And indentation:
    - Item 1
    - Item 2"""
        data = {"messages": [{"role": "user", "content": content}]}
        cache.put_data("test", "json", data)
        retrieved = cache.get_data("test", "json")
        assert retrieved["messages"][0]["content"] == content


# Test handling of empty and null values.
def test_empty_and_null_values():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        data = {
            "empty_string": "",
            "empty_list": [],
            "empty_dict": {},
            "null_value": None,
            "nested": {"also_empty": "", "also_null": None},
        }
        cache.put_data("test", "json", data)
        retrieved = cache.get_data("test", "json")
        assert retrieved == data


# Test large number of keys in dict.
def test_large_dict():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        data = {f"key_{i}": f"value_{i}" for i in range(100)}
        cache.put_data("test", "json", data)
        retrieved = cache.get_data("test", "json")
        assert retrieved == data


# Test deeply nested structure.
def test_deeply_nested():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        # Build deeply nested dict
        data = {"value": "deepest"}
        for i in range(20):
            data = {f"level_{i}": data}
        cache.put_data("test", "json", data)
        retrieved = cache.get_data("test", "json")
        assert retrieved == data


# --- put_data/get_data convenience tests ---


# Test put_data with encoder auto-selects registered encoder.
def test_put_data_uses_encoder():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        data = {"key": "value"}
        cache.put_data("test", "json", data)
        retrieved = cache.get_data("test", "json")
        assert retrieved == data


# Test get_data retrieves using same entry_type.
def test_get_data_with_entry_type():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        data = {"message": "Hello, World!"}
        cache.put_data("test", "json", data)
        # get_data should find it with same entry_type
        retrieved = cache.get_data("test", "json")
        assert retrieved == data


# --- Persistence tests ---


# Test data persists across cache sessions.
def test_persistence_file_based(tmp_path):
    db_path = tmp_path / "test_persist.db"

    # Write data
    with TokenCache(str(db_path)) as cache:
        cache.register_encoder("json", JsonEncoder())
        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Remember this"}],
        }
        cache.put_data("persist", "json", data)

    # Read in new session
    with TokenCache(str(db_path)) as cache:
        cache.register_encoder("json", JsonEncoder())
        retrieved = cache.get_data("persist", "json")
        assert retrieved["messages"][0]["content"] == "Remember this"


# Test tokens persist and are reused across sessions.
def test_token_persistence(tmp_path):
    db_path = tmp_path / "test_tokens.db"

    # Write data - creates tokens
    with TokenCache(str(db_path)) as cache:
        cache.register_encoder("json", JsonEncoder())
        data1 = {"model": "gpt-4", "content": "First message"}
        cache.put_data("req1", "json", data1)
        first_token_count = cache.token_count()

    # Write similar data in new session
    with TokenCache(str(db_path)) as cache:
        cache.register_encoder("json", JsonEncoder())
        data2 = {"model": "gpt-4", "content": "Second message"}
        cache.put_data("req2", "json", data2)
        second_token_count = cache.token_count()

    # Should reuse "model", "gpt-4", "content", structural tokens
    new_tokens = second_token_count - first_token_count
    assert new_tokens < 5, f"Added {new_tokens} tokens in second session"


# --- put_data with None ---


# Test put_data with None.
def test_put_get_data_none():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        cache.put_data("hash1", "json", None)
        assert cache.get_data("hash1", "json") is None


# --- put_data/get_data with metadata ---


# Test put_data with metadata.
def test_put_get_data_with_metadata():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        data = {"response": "Hello"}
        metadata = {"latency_ms": 150, "model": "gpt-4"}
        cache.put_data("hash1", "json", data, metadata=metadata)
        result = cache.get_data_with_metadata("hash1", "json")
        assert result is not None
        decoded_data, decoded_meta = result
        assert decoded_data == data
        assert decoded_meta["latency_ms"] == 150
        assert decoded_meta["model"] == "gpt-4"


# Test get_data_with_metadata when no metadata stored.
def test_get_data_with_metadata_no_metadata():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        cache.put_data("hash1", "json", {"data": "value"})
        result = cache.get_data_with_metadata("hash1", "json")
        assert result is not None
        decoded_data, decoded_meta = result
        assert decoded_data == {"data": "value"}
        assert decoded_meta is None


# Test get_data_with_metadata for missing entry.
def test_get_data_with_metadata_missing():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        assert cache.get_data_with_metadata("nonexistent", "json") is None


# Test get_data returns None for missing entry.
def test_get_data_missing():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        assert cache.get_data("nonexistent", "json") is None


# --- Error handling ---


# Test put_data raises KeyError for unregistered encoder.
def test_put_data_unregistered_encoder():
    with TokenCache(":memory:") as cache:
        with pytest.raises(KeyError):
            cache.put_data("hash1", "unknown", {"data": "value"})


# Test get_data raises KeyError for unregistered encoder.
def test_get_data_unregistered_encoder():
    with TokenCache(":memory:") as cache:
        # First store raw data
        cache.put("hash1", "unknown", b"raw data")
        with pytest.raises(KeyError):
            cache.get_data("hash1", "unknown")


# Test get_data_with_metadata raises KeyError for unregistered encoder.
def test_get_data_with_metadata_unregistered_encoder():
    with TokenCache(":memory:") as cache:
        cache.put("hash1", "unknown", b"raw data")
        with pytest.raises(KeyError):
            cache.get_data_with_metadata("hash1", "unknown")


# --- Token reuse across entries ---


# Test that tokens are shared across multiple entries.
def test_token_reuse_across_entries():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        # Store multiple entries with common terms
        cache.put_data("hash1", "json", {"role": "user", "content": "Hello"})
        cache.put_data("hash2", "json", {"role": "assistant", "content": "Hi"})
        cache.put_data("hash3", "json", {"role": "user", "content": "Bye"})
        # "role", "user", "content" should be shared
        # Token count should be less than if each was unique
        token_count = cache.token_count()
        # With sharing: ", {, }, :, ,, role, user, assistant, content,
        #               Hello, Hi, Bye, [ and ] if any
        # Should be < 20 tokens for this data
        assert token_count < 20


# --- Overwrite behavior ---


# Test that put_data overwrites existing entry.
def test_put_data_overwrites():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        cache.put_data("hash1", "json", {"version": 1})
        cache.put_data("hash1", "json", {"version": 2})
        result = cache.get_data("hash1", "json")
        assert result == {"version": 2}
        assert cache.entry_count() == 1


# --- Different entry types ---


# Test multiple entry types with same hash.
def test_different_entry_types_same_hash():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        cache.register_encoder("data", JsonEncoder())
        cache.put_data("hash1", "json", {"type": "json"})
        cache.put_data("hash1", "data", {"type": "data"})
        assert cache.get_data("hash1", "json") == {"type": "json"}
        assert cache.get_data("hash1", "data") == {"type": "data"}
        assert cache.entry_count() == 2


# --- Integration with raw put/get ---


# Test that put_data entries can be read with raw get.
def test_put_data_read_raw():
    with TokenCache(":memory:") as cache:
        cache.register_encoder("json", JsonEncoder())
        cache.put_data("hash1", "json", {"key": "value"})
        raw = cache.get("hash1", "json")
        # Raw should be bytes (encoded)
        assert isinstance(raw, bytes)
        assert len(raw) > 0


# Test that raw put can be decoded with get_data.
def test_raw_put_read_with_get_data():
    with TokenCache(":memory:") as cache:
        encoder = JsonEncoder()
        cache.register_encoder("json", encoder)
        # Manually encode and store
        data = {"key": "value"}
        blob = encoder.encode(data, cache)
        cache.put("hash1", "json", blob)
        # Should be able to read with get_data
        result = cache.get_data("hash1", "json")
        assert result == data
