# Cache Module

SQLite-backed caching infrastructure with shared token dictionary for
efficient storage.

## Overview

The cache module provides:

- **TokenCache** - SQLite-backed cache with connection management
- **Compressor** - Abstract base class for pluggable type-specific compressors
- **JsonCompressor** - Tokenised compressor for JSON-serialisable data

## Design Philosophy

The cache uses SQLite for storage, providing:

- Fast indexed key lookup
- Built-in concurrency via SQLite locking
- In-memory mode via `:memory:` for testing
- Incremental updates without rewriting

See [Caching Architecture](../architecture/caching.md) for full design details.

## Usage

### Basic In-Memory Cache

```python
from causaliq_core.cache import TokenCache

# In-memory cache (fast, non-persistent)
with TokenCache(":memory:") as cache:
    assert cache.table_exists("tokens")
    assert cache.table_exists("cache_entries")
```

### File-Based Persistent Cache

```python
from causaliq_core.cache import TokenCache

# File-based cache (persistent)
with TokenCache("my_cache.db") as cache:
    # Data persists across sessions
    print(f"Entries: {cache.entry_count()}")
    print(f"Tokens: {cache.token_count()}")
```

### Transaction Support

```python
from causaliq_core.cache import TokenCache

with TokenCache(":memory:") as cache:
    # Transactions auto-commit on success, rollback on exception
    with cache.transaction() as cursor:
        cursor.execute("INSERT INTO tokens (token) VALUES (?)", ("example",))
```

### Token Dictionary

The cache maintains a shared token dictionary for cross-entry compression.
Compressors use this to convert strings to compact integer IDs:

```python
from causaliq_core.cache import TokenCache

with TokenCache(":memory:") as cache:
    # Get or create token IDs (used by compressors)
    id1 = cache.get_or_create_token("hello")  # Returns 1
    id2 = cache.get_or_create_token("world")  # Returns 2
    id1_again = cache.get_or_create_token("hello")  # Returns 1 (cached)

    # Look up token by ID (used for decompression)
    token = cache.get_token(1)  # Returns "hello"
```

### Storing and Retrieving Entries

Cache entries are stored as binary blobs with a hash key:

```python
from causaliq_core.cache import TokenCache

with TokenCache(":memory:") as cache:
    # Store an entry
    cache.put("abc123", b"response data")
    
    # Check if entry exists
    if cache.exists("abc123"):
        # Retrieve entry
        data = cache.get("abc123")  # Returns b"response data"
    
    # Store with metadata
    cache.put("def456", b"data", metadata=b"extra info")
    result = cache.get_with_metadata("def456")
    # result = (b"data", b"extra info")
    
    # Delete entry
    cache.delete("abc123")
```

### Auto-Compression with Registered Compressor

Set a compressor to automatically compress/decompress entries:

```python
from causaliq_core.cache import TokenCache
from causaliq_core.cache.compressors import JsonCompressor

with TokenCache(":memory:") as cache:
    # Set compressor for automatic compression
    cache.set_compressor(JsonCompressor())
    
    # Store data (auto-compressed)
    cache.put_data("hash1", {"role": "user", "content": "Hello"})
    
    # Retrieve data (auto-decompressed)
    data = cache.get_data("hash1")
    # data = {"role": "user", "content": "Hello"}
    
    # Store with metadata
    cache.put_data("hash2",
                   {"response": "Hi!"},
                   metadata={"latency_ms": 150})
    result = cache.get_data_with_metadata("hash2")
    # result = ({"response": "Hi!"}, {"latency_ms": 150})
```

### Hash Collision Handling

Use `key_json` parameter to prevent returning incorrect data when
different keys produce the same truncated hash:

```python
from causaliq_core.cache import TokenCache
from causaliq_core.cache.compressors import JsonCompressor

with TokenCache(":memory:") as cache:
    cache.set_compressor(JsonCompressor())
    
    # Store with original key for collision safety
    key_json = '{"model": "gpt-4", "prompt": "Hello"}'
    cache.put_data("abc123", {"response": "Hi!"}, key_json=key_json)
    
    # Retrieve with key_json verification
    data = cache.get_data("abc123", key_json=key_json)
```

### Exporting and Importing Entries

Export cache entries to files for backup, migration, or sharing.
Import entries from files into a cache:

```python
from pathlib import Path
from causaliq_core.cache import TokenCache
from causaliq_core.cache.compressors import JsonCompressor

# Export entries to directory
with TokenCache("my_cache.db") as cache:
    cache.set_compressor(JsonCompressor())
    
    # Export all entries to directory
    # Creates one file per entry: {hash}.json
    count = cache.export_entries(Path("./export"))
    print(f"Exported {count} entries")

# Import entries from directory
with TokenCache("new_cache.db") as cache:
    cache.set_compressor(JsonCompressor())
    
    # Import all .json files from directory
    # Uses filename (without extension) as hash key
    count = cache.import_entries(Path("./export"))
    print(f"Imported {count} entries")
```

**Export behaviour:**

- Creates output directory if it doesn't exist
- Writes each entry to `{hash}.{ext}` (e.g., `abc123.json`)
- Uses compressor's `export()` method for human-readable format
- Returns count of exported entries

**Import behaviour:**

- Reads all files in directory (skips subdirectories)
- Uses filename stem as hash key (e.g., `abc123.json` → key `abc123`)
- Uses compressor's `import_()` method to parse content
- Returns count of imported entries

## API Reference

::: causaliq_core.cache.TokenCache
    options:
      show_root_heading: true
      show_source: false
      members:
        - __init__
        - open
        - close
        - is_open
        - is_memory
        - conn
        - transaction
        - table_exists
        - entry_count
        - token_count
        - list_entries
        - total_hits
        - get_or_create_token
        - get_token
        - set_compressor
        - get_compressor
        - has_compressor
        - put
        - get
        - get_with_metadata
        - exists
        - delete
        - put_data
        - get_data
        - get_data_with_metadata
        - export_entries
        - import_entries
