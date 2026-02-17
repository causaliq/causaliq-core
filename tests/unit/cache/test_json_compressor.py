"""Unit tests for JsonCompressor.

Tests compression and decompression without filesystem access.
"""

import json

import pytest

from causaliq_core.cache import TokenCache
from causaliq_core.cache.compressors import JsonCompressor


@pytest.fixture
def cache_and_compressor() -> tuple[TokenCache, JsonCompressor]:
    """Create in-memory cache and compressor for testing."""
    cache = TokenCache(":memory:")
    cache.open()
    compressor = JsonCompressor()
    yield cache, compressor
    cache.close()


# ============================================================================
# Basic compression tests
# ============================================================================


# Test compress returns bytes.
def test_compress_returns_bytes(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    data = {"key": "value"}
    result = compressor.compress(data, cache)
    assert isinstance(result, bytes)


# Test decompress reconstructs original data.
def test_decompress_reconstructs_data(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = {"key": "value", "number": 42}
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# Test roundtrip with nested dicts.
def test_roundtrip_nested_dict(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = {"level1": {"level2": {"level3": "deep value"}}}
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# Test roundtrip with list.
def test_roundtrip_list(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = [1, 2, 3, "a", "b", "c"]
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# Test roundtrip with mixed types.
def test_roundtrip_mixed_types(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = {
        "string": "hello",
        "int": 42,
        "float": 3.14,
        "bool": True,
        "null": None,
        "list": [1, 2, 3],
        "nested": {"a": 1},
    }
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# ============================================================================
# Tokenisation tests
# ============================================================================


# Test repeated strings are tokenised.
def test_repeated_strings_tokenised(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    # Repeated keys should benefit from tokenisation
    data = {
        "repeated_key_name": "value1",
        "another_key": {"repeated_key_name": "value2"},
    }
    compressor.compress(data, cache)
    assert cache.token_count() >= 1


# Test token dictionary grows with new strings.
def test_token_dictionary_grows(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    assert cache.token_count() == 0
    compressor.compress({"key1": "value1"}, cache)
    count1 = cache.token_count()
    compressor.compress({"key2": "value2"}, cache)
    count2 = cache.token_count()
    # Should have more tokens after second compress
    assert count2 > count1


# Test token IDs are reused for same strings.
def test_token_reuse(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    data = {"key": "value"}
    compressor.compress(data, cache)
    count1 = cache.token_count()
    # Compress same data again
    compressor.compress(data, cache)
    count2 = cache.token_count()
    # Token count should not increase
    assert count2 == count1


# ============================================================================
# File format tests
# ============================================================================


# Test default export format property.
def test_default_export_format() -> None:
    compressor = JsonCompressor()
    assert compressor.default_export_format == "json"


# ============================================================================
# Empty data tests
# ============================================================================


# Test empty dict.
def test_empty_dict(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original: dict[str, str] = {}
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# Test empty list.
def test_empty_list(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original: list[str] = []
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# ============================================================================
# Edge case tests
# ============================================================================


# Test very long string.
def test_very_long_string(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = {"long": "x" * 10000}
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# Test unicode strings.
def test_unicode_strings(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = {"emoji": "🎉", "chinese": "中文", "arabic": "العربية"}
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# Test numeric keys (as strings in JSON).
def test_numeric_string_keys(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = {"1": "one", "2": "two"}
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# Test special characters in strings.
def test_special_characters(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = {
        "tab": "hello\tworld",
        "newline": "hello\nworld",
        "quote": 'hello"world',
    }
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# ============================================================================
# Compression efficiency tests
# ============================================================================


# Test compression reduces size for repetitive data.
def test_compression_reduces_size_for_repetitive(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    # Data with lots of repetition
    original = {
        f"item_{i}": {
            "name": "repeated_name_value",
            "description": "repeated_description_value",
            "category": "repeated_category_value",
        }
        for i in range(100)
    }
    uncompressed_size = len(json.dumps(original).encode("utf-8"))
    compressed = compressor.compress(original, cache)
    compressed_size = len(compressed)
    # Should achieve some compression
    assert compressed_size < uncompressed_size


# ============================================================================
# Additional type coverage tests
# ============================================================================


# Test False boolean value is preserved.
def test_false_boolean_value(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = {"active": False, "enabled": True}
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original
    assert result["active"] is False
    assert result["enabled"] is True


# Test empty string is preserved.
def test_empty_string(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = {"empty": "", "not_empty": "value"}
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original
    assert result["empty"] == ""


# Test list at top level.
def test_list_at_top_level(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = ["a", 1, True, None, {"key": "value"}]
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# Test negative integer.
def test_negative_integer(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = {"negative": -42, "zero": 0, "positive": 42}
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# Test negative and scientific notation floats.
def test_special_floats(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = {"negative": -3.14, "small": 1e-10, "large": 1e10}
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result["negative"] == pytest.approx(-3.14)
    assert result["small"] == pytest.approx(1e-10)
    assert result["large"] == pytest.approx(1e10)


# Test nested lists.
def test_nested_lists(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = [[1, 2], [3, [4, 5]], []]
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# Test string with only punctuation and spaces.
def test_string_punctuation_spaces(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor
    original = {"punc": "!!??", "space": "   ", "mixed": "  !  ?  "}
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    assert result == original


# Test fallback for non-JSON types (converts to string).
def test_unknown_type_fallback(
    cache_and_compressor: tuple[TokenCache, JsonCompressor],
) -> None:
    cache, compressor = cache_and_compressor

    class CustomClass:
        def __str__(self) -> str:
            return "custom_value"

    # Compress a dict containing a custom object
    original = {"custom": CustomClass()}
    compressed = compressor.compress(original, cache)
    result = compressor.decompress(compressed, cache)
    # The custom object gets converted to its string representation
    assert result == {"custom": "custom_value"}
