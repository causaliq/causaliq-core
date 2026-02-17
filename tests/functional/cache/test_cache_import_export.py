"""
Functional tests for TokenCache import/export operations.

These tests verify that cache entries can be exported to files and
imported from files.

Migrated from causaliq-knowledge.
"""

import json
from pathlib import Path

import pytest

from causaliq_core.cache import TokenCache
from causaliq_core.cache.compressors import JsonCompressor

# ============================================================================
# Export tests
# ============================================================================


# Test export_entries creates output directory if needed.
def test_export_creates_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "export_test" / "nested"

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())
        cache.put_data("abc123", {"key": "value"})

        cache.export_entries(output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()
        assert (output_dir / "abc123.json").exists()


# Test export_entries exports single entry to correct file.
def test_export_single_entry(tmp_path: Path) -> None:
    output_dir = tmp_path / "export_single"
    output_dir.mkdir(parents=True, exist_ok=True)

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())
        cache.put_data("myhash", {"hello": "world"})

        count = cache.export_entries(output_dir)

        assert count == 1
        expected_file = output_dir / "myhash.json"
        assert expected_file.exists()


# Test export_entries returns correct count.
def test_export_returns_count(tmp_path: Path) -> None:
    output_dir = tmp_path / "export_count"
    output_dir.mkdir(parents=True, exist_ok=True)

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())
        cache.put_data("hash1", {"a": 1})
        cache.put_data("hash2", {"b": 2})
        cache.put_data("hash3", {"c": 3})

        count = cache.export_entries(output_dir)

        assert count == 3


# Test export_entries returns zero for empty cache.
def test_export_empty_cache(tmp_path: Path) -> None:
    output_dir = tmp_path / "export_empty"
    output_dir.mkdir(parents=True, exist_ok=True)

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())

        count = cache.export_entries(output_dir)

        assert count == 0


# Test export_entries uses compressor's default format.
def test_export_uses_default_format(tmp_path: Path) -> None:
    output_dir = tmp_path / "export_default_fmt"
    output_dir.mkdir(parents=True, exist_ok=True)

    with TokenCache(":memory:") as cache:
        compressor = JsonCompressor()
        assert compressor.default_export_format == "json"
        cache.set_compressor(compressor)
        cache.put_data("hashval", {"data": 123})

        cache.export_entries(output_dir)

        assert (output_dir / "hashval.json").exists()


# Test export_entries accepts custom format.
def test_export_custom_format(tmp_path: Path) -> None:
    output_dir = tmp_path / "export_custom_fmt"
    output_dir.mkdir(parents=True, exist_ok=True)

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())
        cache.put_data("myhash", {"key": "value"})

        cache.export_entries(output_dir, fmt="txt")

        assert (output_dir / "myhash.txt").exists()
        assert not (output_dir / "myhash.json").exists()


# Test export_entries file content is valid JSON.
def test_export_content_is_valid_json(tmp_path: Path) -> None:
    output_dir = tmp_path / "export_content"
    output_dir.mkdir(parents=True, exist_ok=True)

    original_data = {"name": "test", "count": 42, "nested": {"a": [1, 2, 3]}}

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())
        cache.put_data("datahash", original_data)

        cache.export_entries(output_dir)

        exported_file = output_dir / "datahash.json"
        with open(exported_file, encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded == original_data


# Test export_entries handles multiple entries.
def test_export_multiple_entries(tmp_path: Path) -> None:
    output_dir = tmp_path / "export_multi"
    output_dir.mkdir(parents=True, exist_ok=True)

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())
        cache.put_data("first", {"order": 1})
        cache.put_data("second", {"order": 2})
        cache.put_data("third", {"order": 3})

        count = cache.export_entries(output_dir)

        assert count == 3
        for name, expected in [
            ("first", {"order": 1}),
            ("second", {"order": 2}),
            ("third", {"order": 3}),
        ]:
            path = output_dir / f"{name}.json"
            assert path.exists()
            with open(path, encoding="utf-8") as f:
                assert json.load(f) == expected


# Test export_entries raises RuntimeError without compressor set.
def test_export_raises_without_compressor(tmp_path: Path) -> None:
    with TokenCache(":memory:") as cache:
        with pytest.raises(RuntimeError):
            cache.export_entries(tmp_path)


# ============================================================================
# Import tests
# ============================================================================


# Test import_entries reads files from directory.
def test_import_from_directory(tmp_path: Path) -> None:
    # Create test files
    (tmp_path / "entry1.json").write_text('{"key": "value1"}')
    (tmp_path / "entry2.json").write_text('{"key": "value2"}')
    (tmp_path / "entry3.json").write_text('{"key": "value3"}')

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())

        count = cache.import_entries(tmp_path)

        assert count == 3


# Test import_entries uses filename stem as hash.
def test_import_uses_filename_as_hash(tmp_path: Path) -> None:
    (tmp_path / "entry1.json").write_text('{"a": 1}')
    (tmp_path / "entry2.json").write_text('{"b": 2}')
    (tmp_path / "entry3.json").write_text('{"c": 3}')

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())

        cache.import_entries(tmp_path)

        assert cache.exists("entry1")
        assert cache.exists("entry2")
        assert cache.exists("entry3")


# Test import_entries correctly parses JSON content.
def test_import_parses_json_content(tmp_path: Path) -> None:
    (tmp_path / "entry1.json").write_text('{"key": "value", "count": 42}')
    (tmp_path / "entry2.json").write_text(
        '{"name": "test entry", "nested": {"a": 1, "b": 2}}'
    )
    (tmp_path / "entry3.json").write_text(
        '{"items": [1, 2, 3, 4, 5], "active": true, "score": 3.14}'
    )

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())

        cache.import_entries(tmp_path)

        # Verify entry1
        data1 = cache.get_data("entry1")
        assert data1 == {"key": "value", "count": 42}

        # Verify entry2 with nested object
        data2 = cache.get_data("entry2")
        assert data2 == {"name": "test entry", "nested": {"a": 1, "b": 2}}

        # Verify entry3 with list and mixed types
        data3 = cache.get_data("entry3")
        assert data3["items"] == [1, 2, 3, 4, 5]
        assert data3["active"] is True
        assert data3["score"] == pytest.approx(3.14)


# Test import_entries returns zero for empty directory.
def test_import_empty_directory(tmp_path: Path) -> None:
    empty_dir = tmp_path / "import_empty"
    empty_dir.mkdir(parents=True, exist_ok=True)

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())

        count = cache.import_entries(empty_dir)

        assert count == 0


# Test import_entries skips subdirectories.
def test_import_skips_subdirectories(tmp_path: Path) -> None:
    # Create a subdirectory
    (tmp_path / "subdir").mkdir(exist_ok=True)
    # Create a file
    (tmp_path / "valid.json").write_text('{"key": "value"}')

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())

        count = cache.import_entries(tmp_path)

        # Should only count the file, not the subdirectory
        assert count == 1
        assert cache.exists("valid")


# Test import_entries raises FileNotFoundError for missing directory.
def test_import_raises_for_missing_directory(tmp_path: Path) -> None:
    nonexistent = tmp_path / "does_not_exist"

    with TokenCache(":memory:") as cache:
        cache.set_compressor(JsonCompressor())

        with pytest.raises(FileNotFoundError):
            cache.import_entries(nonexistent)


# Test import_entries raises RuntimeError without compressor set.
def test_import_raises_without_compressor(tmp_path: Path) -> None:
    (tmp_path / "test.json").write_text('{"key": "value"}')

    with TokenCache(":memory:") as cache:
        with pytest.raises(RuntimeError):
            cache.import_entries(tmp_path)


# ============================================================================
# Round-trip tests
# ============================================================================


# Test export then import round-trip preserves data.
def test_export_import_round_trip(tmp_path: Path) -> None:
    export_dir = tmp_path / "round_trip"
    export_dir.mkdir(parents=True, exist_ok=True)

    original_data = {
        "complex": {
            "nested": {"deep": {"value": 42}},
            "list": [1, 2, 3],
        },
        "string": "hello world",
        "number": 3.14159,
        "bool": True,
        "null_val": None,
    }

    # Export from first cache
    with TokenCache(":memory:") as cache1:
        cache1.set_compressor(JsonCompressor())
        cache1.put_data("testkey", original_data)

        cache1.export_entries(export_dir)

    # Import into second cache
    with TokenCache(":memory:") as cache2:
        cache2.set_compressor(JsonCompressor())
        cache2.import_entries(export_dir)

        restored_data = cache2.get_data("testkey")

        assert restored_data == original_data


# Test round-trip with multiple entries.
def test_round_trip_multiple_entries(tmp_path: Path) -> None:
    export_dir = tmp_path / "round_trip_multi"
    export_dir.mkdir(parents=True, exist_ok=True)

    entries = {
        "alpha": {"name": "first", "value": 1},
        "beta": {"name": "second", "value": 2},
        "gamma": {"name": "third", "value": 3},
    }

    # Export from first cache
    with TokenCache(":memory:") as cache1:
        cache1.set_compressor(JsonCompressor())
        for key, data in entries.items():
            cache1.put_data(key, data)

        count = cache1.export_entries(export_dir)
        assert count == 3

    # Import into second cache
    with TokenCache(":memory:") as cache2:
        cache2.set_compressor(JsonCompressor())
        count = cache2.import_entries(export_dir)
        assert count == 3

        for key, expected in entries.items():
            assert cache2.get_data(key) == expected


# Test round-trip with Unicode and special characters.
def test_round_trip_unicode(tmp_path: Path) -> None:
    export_dir = tmp_path / "round_trip_unicode"
    export_dir.mkdir(parents=True, exist_ok=True)

    original_data = {
        "chinese": "你好世界",
        "japanese": "こんにちは",
        "russian": "Привет мир",
        "arabic": "مرحبا بالعالم",
        "emoji": "🌍🎉🚀",
        "special": "© ® ™ € £ ¥ • → ←",
    }

    # Export from first cache
    with TokenCache(":memory:") as cache1:
        cache1.set_compressor(JsonCompressor())
        cache1.put_data("unicode_test", original_data)
        cache1.export_entries(export_dir)

    # Import into second cache
    with TokenCache(":memory:") as cache2:
        cache2.set_compressor(JsonCompressor())
        cache2.import_entries(export_dir)
        restored_data = cache2.get_data("unicode_test")
        assert restored_data == original_data
