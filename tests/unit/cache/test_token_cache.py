"""Unit tests for TokenCache core functionality.

Tests use in-memory SQLite only (no filesystem access).
"""

import pytest

from causaliq_core.cache import TokenCache

# ============================================================================
# Schema and initialisation tests
# ============================================================================


# Test that TokenCache creates required tables on open.
def test_token_cache_creates_schema() -> None:
    with TokenCache(":memory:") as cache:
        assert cache.table_exists("tokens")
        assert cache.table_exists("cache_entries")


# Test that schema includes expected columns in tokens table.
def test_tokens_table_has_correct_columns() -> None:
    with TokenCache(":memory:") as cache:
        cursor = cache.conn.execute("PRAGMA table_info(tokens)")
        columns = {row[1] for row in cursor.fetchall()}
        assert columns == {"id", "token", "frequency"}


# Test that schema includes expected columns in cache_entries table.
def test_cache_entries_table_has_correct_columns() -> None:
    with TokenCache(":memory:") as cache:
        cursor = cache.conn.execute("PRAGMA table_info(cache_entries)")
        columns = {row[1] for row in cursor.fetchall()}
        expected = {
            "hash",
            "seq",
            "key_json",
            "data",
            "created_at",
            "metadata",
            "hit_count",
            "last_accessed_at",
        }
        assert columns == expected


# ============================================================================
# Connection management tests
# ============================================================================


# Test context manager opens and closes connection.
def test_context_manager_opens_and_closes() -> None:
    cache = TokenCache(":memory:")
    assert not cache.is_open
    with cache:
        assert cache.is_open
    assert not cache.is_open


# Test explicit open() and close() methods.
def test_explicit_open_close() -> None:
    cache = TokenCache(":memory:")
    assert not cache.is_open
    cache.open()
    assert cache.is_open
    cache.close()
    assert not cache.is_open


# Test that accessing conn before open raises RuntimeError.
def test_conn_before_open_raises() -> None:
    cache = TokenCache(":memory:")
    with pytest.raises(RuntimeError, match="not connected"):
        _ = cache.conn


# Test that opening twice raises RuntimeError.
def test_double_open_raises() -> None:
    cache = TokenCache(":memory:")
    cache.open()
    try:
        with pytest.raises(RuntimeError, match="already connected"):
            cache.open()
    finally:
        cache.close()


# Test that close() is idempotent.
def test_close_is_idempotent() -> None:
    cache = TokenCache(":memory:")
    cache.open()
    cache.close()
    cache.close()  # Should not raise
    assert not cache.is_open


# ============================================================================
# In-memory mode tests
# ============================================================================


# Test in-memory mode detection.
def test_is_memory_property() -> None:
    memory_cache = TokenCache(":memory:")
    assert memory_cache.is_memory
    file_cache = TokenCache("some/path/test.db")
    assert not file_cache.is_memory


# Test in-memory mode works with context manager.
def test_in_memory_mode_works() -> None:
    with TokenCache(":memory:") as cache:
        assert cache.is_open
        assert cache.entry_count() == 0
        assert cache.token_count() == 0


# ============================================================================
# Token dictionary tests
# ============================================================================


# Test get_or_create_token creates new token.
def test_get_or_create_token_new() -> None:
    with TokenCache(":memory:") as cache:
        id1 = cache.get_or_create_token("hello")
        id2 = cache.get_or_create_token("world")
        assert id1 == 1
        assert id2 == 2
        assert cache.token_count() == 2


# Test get_or_create_token returns existing ID.
def test_get_or_create_token_existing() -> None:
    with TokenCache(":memory:") as cache:
        id1 = cache.get_or_create_token("hello")
        id2 = cache.get_or_create_token("hello")
        assert id1 == id2
        assert cache.token_count() == 1


# Test get_token returns token string by ID.
def test_get_token_returns_string() -> None:
    with TokenCache(":memory:") as cache:
        token_id = cache.get_or_create_token("test_token")
        result = cache.get_token(token_id)
        assert result == "test_token"


# Test get_token returns None for invalid ID.
def test_get_token_returns_none_for_invalid() -> None:
    with TokenCache(":memory:") as cache:
        result = cache.get_token(9999)
        assert result is None


# ============================================================================
# Entry operations tests (raw bytes)
# ============================================================================


# Test put and get with raw bytes.
def test_put_get_raw_bytes() -> None:
    with TokenCache(":memory:") as cache:
        cache.put("hash1", b"test data")
        result = cache.get("hash1")
        assert result == b"test data"


# Test get returns None for non-existent entry.
def test_get_returns_none_for_missing() -> None:
    with TokenCache(":memory:") as cache:
        result = cache.get("nonexistent")
        assert result is None


# Test put with metadata.
def test_put_with_metadata() -> None:
    with TokenCache(":memory:") as cache:
        cache.put("hash1", b"data", metadata=b"meta")
        result = cache.get_with_metadata("hash1")
        assert result is not None
        data, meta = result
        assert data == b"data"
        assert meta == b"meta"


# Test exists returns True for existing entry.
def test_exists_true_for_existing() -> None:
    with TokenCache(":memory:") as cache:
        cache.put("hash1", b"data")
        assert cache.exists("hash1")


# Test exists returns False for missing entry.
def test_exists_false_for_missing() -> None:
    with TokenCache(":memory:") as cache:
        assert not cache.exists("nonexistent")


# Test delete removes entry.
def test_delete_removes_entry() -> None:
    with TokenCache(":memory:") as cache:
        cache.put("hash1", b"data")
        assert cache.exists("hash1")
        result = cache.delete("hash1")
        assert result is True
        assert not cache.exists("hash1")


# Test delete returns False for missing entry.
def test_delete_returns_false_for_missing() -> None:
    with TokenCache(":memory:") as cache:
        result = cache.delete("nonexistent")
        assert result is False


# Test entry_count.
def test_entry_count() -> None:
    with TokenCache(":memory:") as cache:
        assert cache.entry_count() == 0
        cache.put("h1", b"d1")
        assert cache.entry_count() == 1
        cache.put("h2", b"d2")
        assert cache.entry_count() == 2


# Test list_entries.
def test_list_entries() -> None:
    with TokenCache(":memory:") as cache:
        cache.put("h1", b"d1", key_json='{"a":1}')
        cache.put("h2", b"d2", key_json='{"b":2}')
        entries = cache.list_entries()
        assert len(entries) == 2
        assert entries[0]["hash"] == "h1"
        assert entries[0]["key_json"] == '{"a":1}'


# ============================================================================
# Collision handling tests
# ============================================================================


# Test collision handling with key_json.
def test_collision_handling_with_key_json() -> None:
    with TokenCache(":memory:") as cache:
        # Same hash, different key_json -> collision
        cache.put("same_hash", b"data1", key_json='{"k":1}')
        cache.put("same_hash", b"data2", key_json='{"k":2}')

        # Without key_json, returns first
        result = cache.get("same_hash")
        assert result == b"data1"

        # With key_json, returns specific entry
        result = cache.get("same_hash", key_json='{"k":2}')
        assert result == b"data2"


# ============================================================================
# Compressor tests
# ============================================================================


# Test set_compressor and has_compressor.
def test_compressor_registration() -> None:
    from causaliq_core.cache.compressors import JsonCompressor

    with TokenCache(":memory:") as cache:
        assert not cache.has_compressor()
        cache.set_compressor(JsonCompressor())
        assert cache.has_compressor()
        assert cache.get_compressor() is not None


# Test put_data and get_data with compressor.
def test_put_get_data_with_compressor() -> None:
    from causaliq_core.cache.compressors import JsonCompressor

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())
        data = {"message": "hello", "count": 42}
        cache.put_data("h1", data)
        result = cache.get_data("h1")
        assert result == data


# Test put_data raises without compressor.
def test_put_data_raises_without_compressor() -> None:
    with TokenCache(":memory:") as cache:
        with pytest.raises(RuntimeError, match="No compressor set"):
            cache.put_data("h1", {"data": 1})


# Test get_data raises without compressor.
def test_get_data_raises_without_compressor() -> None:
    with TokenCache(":memory:") as cache:
        cache.put("h1", b"data")
        with pytest.raises(RuntimeError, match="No compressor set"):
            cache.get_data("h1")


# Test get_data_with_metadata.
def test_get_data_with_metadata() -> None:
    from causaliq_core.cache.compressors import JsonCompressor

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())
        data = {"key": "value"}
        meta = {"info": "test"}
        cache.put_data("h1", data, metadata=meta)
        result = cache.get_data_with_metadata("h1")
        assert result is not None
        d, m = result
        assert d == data
        assert m == meta


# ============================================================================
# Transaction tests
# ============================================================================


# Test transaction commits on success.
def test_transaction_commits_on_success() -> None:
    with TokenCache(":memory:") as cache:
        with cache.transaction() as cursor:
            cursor.execute(
                "INSERT INTO tokens (token) VALUES (?)", ("test_token",)
            )
        assert cache.token_count() == 1


# Test transaction rolls back on exception.
def test_transaction_rolls_back_on_exception() -> None:
    with TokenCache(":memory:") as cache:
        try:
            with cache.transaction() as cursor:
                cursor.execute(
                    "INSERT INTO tokens (token) VALUES (?)", ("rollback",)
                )
                raise ValueError("Simulated error")
        except ValueError:
            pass
        assert cache.token_count() == 0


# ============================================================================
# Hit count tests
# ============================================================================


# Test total_hits starts at zero.
def test_total_hits_starts_zero() -> None:
    with TokenCache(":memory:") as cache:
        assert cache.total_hits() == 0


# Test hit count increments on get.
def test_hit_count_increments_on_get() -> None:
    with TokenCache(":memory:") as cache:
        cache.put("h1", b"data")
        cache.get("h1")
        cache.get("h1")
        assert cache.total_hits() == 2


# ============================================================================
# Additional collision and key_json tests
# ============================================================================


# Test put updates existing entry when key_json matches.
def test_put_updates_existing_entry_when_key_json_matches() -> None:
    with TokenCache(":memory:") as cache:
        cache.put("hash1", b"original", key_json='{"k":1}')
        cache.put("hash1", b"updated", key_json='{"k":1}')

        # Should still be just one entry
        assert cache.entry_count() == 1

        # Should get updated data
        result = cache.get("hash1", key_json='{"k":1}')
        assert result == b"updated"


# Test exists with key_json parameter.
def test_exists_with_key_json() -> None:
    with TokenCache(":memory:") as cache:
        cache.put("hash1", b"data1", key_json='{"k":1}')
        cache.put("hash1", b"data2", key_json='{"k":2}')

        # Both entries exist with their specific key_json
        assert cache.exists("hash1", key_json='{"k":1}')
        assert cache.exists("hash1", key_json='{"k":2}')

        # Non-existent key_json doesn't exist
        assert not cache.exists("hash1", key_json='{"k":3}')


# Test delete with key_json parameter.
def test_delete_with_key_json() -> None:
    with TokenCache(":memory:") as cache:
        cache.put("hash1", b"data1", key_json='{"k":1}')
        cache.put("hash1", b"data2", key_json='{"k":2}')

        assert cache.entry_count() == 2

        # Delete only one collision entry
        result = cache.delete("hash1", key_json='{"k":1}')
        assert result is True
        assert cache.entry_count() == 1

        # Remaining entry still exists
        assert cache.exists("hash1", key_json='{"k":2}')
        assert not cache.exists("hash1", key_json='{"k":1}')


# Test get returns None when key_json doesn't match.
def test_get_returns_none_when_key_json_mismatch() -> None:
    with TokenCache(":memory:") as cache:
        cache.put("hash1", b"data", key_json='{"k":1}')

        # Get with wrong key_json returns None
        result = cache.get("hash1", key_json='{"k":2}')
        assert result is None


# Test get_with_metadata with key_json parameter.
def test_get_with_metadata_and_key_json() -> None:
    with TokenCache(":memory:") as cache:
        cache.put("hash1", b"data1", metadata=b"meta1", key_json='{"k":1}')
        cache.put("hash1", b"data2", metadata=b"meta2", key_json='{"k":2}')

        result = cache.get_with_metadata("hash1", key_json='{"k":2}')
        assert result is not None
        data, meta = result
        assert data == b"data2"
        assert meta == b"meta2"


# Test get_with_metadata returns None for missing entry.
def test_get_with_metadata_returns_none_for_missing() -> None:
    with TokenCache(":memory:") as cache:
        result = cache.get_with_metadata("nonexistent")
        assert result is None


# Test get_data returns None for missing entry.
def test_get_data_returns_none_for_missing() -> None:
    from causaliq_core.cache.compressors import JsonCompressor

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())
        result = cache.get_data("nonexistent")
        assert result is None


# Test get_data_with_metadata returns None for missing entry.
def test_get_data_with_metadata_returns_none_for_missing() -> None:
    from causaliq_core.cache.compressors import JsonCompressor

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())
        result = cache.get_data_with_metadata("nonexistent")
        assert result is None


# Test put_data with key_json and collision.
def test_put_data_with_key_json_collision() -> None:
    from causaliq_core.cache.compressors import JsonCompressor

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())
        cache.put_data("hash1", {"a": 1}, key_json='{"k":1}')
        cache.put_data("hash1", {"b": 2}, key_json='{"k":2}')

        assert cache.entry_count() == 2

        result1 = cache.get_data("hash1", key_json='{"k":1}')
        result2 = cache.get_data("hash1", key_json='{"k":2}')
        assert result1 == {"a": 1}
        assert result2 == {"b": 2}


# Test get_data_with_metadata raises without compressor on existing entry.
def test_get_data_with_metadata_raises_without_compressor() -> None:
    with TokenCache(":memory:") as cache:
        # Put raw bytes without compressor
        cache.put("h1", b"raw data")
        # get_data_with_metadata should raise without compressor
        with pytest.raises(RuntimeError, match="No compressor set"):
            cache.get_data_with_metadata("h1")
