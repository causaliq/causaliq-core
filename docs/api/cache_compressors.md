# Cache Compressors

Pluggable compressors for type-specific cache entry compression.

## Overview

Compressors transform data to/from compact binary representations,
using a shared token dictionary for cross-entry compression.

| Compressor | Description |
|------------|-------------|
| [Compressor](#compressor) | Abstract base class for all compressors |
| [JsonCompressor](#jsoncompressor) | Tokenised compression for JSON data |

## Compressor

The `Compressor` abstract base class defines the interface for pluggable
cache compressors.

### Creating a Custom Compressor

```python
from pathlib import Path
from causaliq_core.cache import TokenCache
from causaliq_core.cache.compressors import Compressor


class MyCompressor(Compressor):
    """Example compressor for custom data types."""

    @property
    def default_export_format(self) -> str:
        """File extension for exports."""
        return "txt"

    def compress(self, data: dict, token_cache: TokenCache) -> bytes:
        """Convert data to bytes for storage."""
        # Use token_cache.get_or_create_token() for string compression
        return b"compressed"

    def decompress(self, blob: bytes, token_cache: TokenCache) -> dict:
        """Convert bytes back to original data."""
        # Use token_cache.get_token() to restore strings
        return {"decompressed": True}

    def export(self, data: dict, path: Path) -> None:
        """Export to human-readable file."""
        path.write_text(str(data))

    def import_(self, path: Path) -> dict:
        """Import from human-readable file."""
        return eval(path.read_text())
```

### Compressor Interface

::: causaliq_core.cache.compressors.Compressor
    options:
      show_root_heading: true
      show_source: false
      members:
        - compress
        - decompress
        - export
        - import_
        - default_export_format

---

## JsonCompressor

The `JsonCompressor` provides tokenised compression for JSON-serialisable
data, achieving compression through shared token dictionary usage.

### Supported Types

JsonCompressor handles any JSON-serialisable Python data structure:

- Dictionaries
- Lists
- Strings
- Integers and floats
- Booleans
- None

### Usage

#### Direct Compression

```python
from causaliq_core.cache import TokenCache
from causaliq_core.cache.compressors import JsonCompressor

with TokenCache(":memory:") as cache:
    compressor = JsonCompressor()
    
    # Compress any JSON-serialisable data
    data = {
        "messages": [
            {"role": "user", "content": "What is BMI?"},
        ],
        "temperature": 0.7,
        "max_tokens": 100,
    }
    
    # Compress to compact binary format
    blob = compressor.compress(data, cache)
    
    # Decompress back to original structure
    decompressed = compressor.decompress(blob, cache)
    assert decompressed == data
```

#### With TokenCache Auto-Compression

```python
from causaliq_core.cache import TokenCache
from causaliq_core.cache.compressors import JsonCompressor

with TokenCache(":memory:") as cache:
    # Set compressor for auto-compression
    cache.set_compressor(JsonCompressor())
    
    # Store and retrieve with automatic compression
    cache.put_data("hash1", {"key": "value"})
    data = cache.get_data("hash1")
```

#### Export/Import for Human-Readable Files

```python
from pathlib import Path
from causaliq_core.cache.compressors import JsonCompressor

compressor = JsonCompressor()

# Export to JSON file
data = {"messages": [{"role": "user", "content": "Hello"}]}
compressor.export(data, Path("data.json"))

# Import from JSON file
imported = compressor.import_(Path("data.json"))
```

### Compression Format

The compressor uses three type markers for compact binary representation:

| Marker | Value | Description |
|--------|-------|-------------|
| TOKEN_REF | 0x00 | Token ID reference (uint16) |
| LITERAL_INT | 0x01 | 64-bit signed integer |
| LITERAL_FLOAT | 0x02 | 64-bit double float |

#### What Gets Tokenised

| Element | Tokenised | Rationale |
|---------|-----------|-----------|
| JSON structural chars (`{`, `}`, `[`, `]`, `:`, `,`) | Yes | Very frequent |
| String quotes (`"`) | Yes | Frequent |
| String content (words) | Yes | High repetition across entries |
| `null`, `true`, `false` | Yes | Fixed vocabulary |
| Integers | No | Stored as 8-byte literals |
| Floats | No | Stored as 8-byte literals |

#### Compression Example

```
Original: {"role": "user", "content": "Hello world"}
Tokens:   { " role " : " user " , " content " : " Hello   world " }
          ↓   ↓     ↓ ↓   ↓    ↓ ↓     ↓      ↓ ↓   ↓       ↓    ↓
          T1  T2   T3 T2 T4   T5 T2 T6  T7    T8 T2 T4     T9   T10 T2 T11

Each token ID: 3 bytes (0x00 marker + uint16)
```

### Token Reuse

Tokens are shared across all entries in a cache, providing cumulative
compression benefits:

```python
with TokenCache(":memory:") as cache:
    cache.set_compressor(JsonCompressor())
    
    # Common terms like "role", "content", "user" are tokenised once
    cache.put_data("h1", {"role": "user", "content": "Hello"})
    cache.put_data("h2", {"role": "assistant", "content": "Hi"})
    cache.put_data("h3", {"role": "user", "content": "Bye"})
    
    # "role", "content", "user" reuse same token IDs across all entries
    print(f"Total tokens: {cache.token_count()}")  # Much less than unique words
```

### API Reference

::: causaliq_core.cache.compressors.JsonCompressor
    options:
      show_root_heading: true
      show_source: false
      members:
        - compress
        - decompress
        - export
        - import_
        - default_export_format
