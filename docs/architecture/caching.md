# Caching Architecture

## Overview

CausalIQ Core provides shared caching infrastructure used by multiple
packages in the ecosystem. The design prioritises efficient storage,
fast access, and flexibility for domain-specific compression.

## Design Principles

- **SQLite-backed** - Provides fast indexed lookups, built-in concurrency,
  and in-memory mode for testing
- **Pluggable compressors** - Type-specific compressors achieve optimal
  compression for different data structures
- **Shared token dictionary** - Cross-entry compression via tokenisation
  of repeated strings
- **Import/Export** - Human-readable formats for test fixtures and archival

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application                              │
│  (causaliq-knowledge LLM cache, causaliq-workflow cache, etc.)  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        TokenCache                                │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  Token Dictionary │  │   Compressor     │  │ SQLite Storage │  │
│  │  (shared strings) │  │  (json, custom)  │  │  (entries)     │  │
│  └─────────────────┘  └──────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
    ┌────────────────┐ ┌────────────┐  ┌────────────────┐
    │ JsonCompressor │ │ Custom     │  │ LLMCompressor  │
    │ (causaliq-     │ │ Compressor │  │ (causaliq-     │
    │  core)         │ │            │  │  knowledge)    │
    └────────────────┘ └────────────┘  └────────────────┘
```

## SQLite Schema

```sql
-- Token dictionary (grows dynamically, shared across compressors)
CREATE TABLE tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    frequency INTEGER DEFAULT 1
);

-- Generic cache entries with collision handling
CREATE TABLE cache_entries (
    hash TEXT NOT NULL,
    seq INTEGER DEFAULT 0,
    key_json TEXT NOT NULL,
    data BLOB NOT NULL,
    created_at TEXT NOT NULL,
    metadata BLOB,
    hit_count INTEGER DEFAULT 0,
    last_accessed_at TEXT,
    PRIMARY KEY (hash, seq)
);

CREATE INDEX idx_created_at ON cache_entries(created_at);
```

## Token Dictionary

The token dictionary provides cross-entry compression by replacing
repeated strings with compact integer IDs:

```
String: "role"     → Token ID: 1  (3 bytes: 0x00 + uint16)
String: "content"  → Token ID: 2
String: "user"     → Token ID: 3
```

Benefits accumulate as more entries share common tokens:

| Entries | Unique Tokens | Compression |
|---------|---------------|-------------|
| 1       | 15            | ~1.2x (overhead) |
| 10      | 25            | ~0.8x |
| 100     | 50            | ~0.5x |
| 1000    | 100           | ~0.3x |

## Compressor Interface

Each compressor implements the `Compressor` abstract base class:

```python
class Compressor(ABC):
    @property
    def default_export_format(self) -> str:
        """File extension for exports (e.g., 'json')."""
        return "json"

    @abstractmethod
    def compress(self, data: Any, token_cache: TokenCache) -> bytes:
        """Convert data to compact binary format."""
        ...

    @abstractmethod
    def decompress(self, blob: bytes, token_cache: TokenCache) -> Any:
        """Restore data from binary format."""
        ...

    @abstractmethod
    def export(self, data: Any, path: Path) -> None:
        """Write data to human-readable file."""
        ...

    @abstractmethod
    def import_(self, path: Path) -> Any:
        """Read data from human-readable file."""
        ...
```

## JsonCompressor Format

The built-in `JsonCompressor` uses three type markers:

| Marker | Hex | Description |
|--------|-----|-------------|
| TOKEN_REF | 0x00 | Token ID reference (uint16) |
| LITERAL_INT | 0x01 | 64-bit signed integer |
| LITERAL_FLOAT | 0x02 | 64-bit double float |

Example encoding:

```
JSON:     {"count": 42}
Binary:   [T:"{"] [T:"count"] [T:":"] [INT:42] [T:"}"]
Bytes:    00 01 00  00 02 00   00 03 00  01 2A...  00 04 00
```

## Usage Patterns

### Application-Specific Caches

Each application defines:

1. **Cache scope** - What entries share a cache (e.g., per-dataset)
2. **Compressor** - What compression to use (e.g., JsonCompressor, custom)
3. **Key construction** - How to hash request parameters

### LLM Caching (causaliq-knowledge)

```python
from causaliq_core.cache import TokenCache
from causaliq_knowledge.cache import LLMCompressor

# Cache scoped to dataset
with TokenCache(f"datasets/{dataset_name}/llm_cache.db") as cache:
    cache.set_compressor(LLMCompressor())

    # Build cache key from request parameters
    key_data = {"model": model, "messages": messages, "temperature": temp}
    key_json = json.dumps(key_data, sort_keys=True)
    cache_key = hashlib.sha256(key_json.encode()).hexdigest()[:16]

    # Check cache before API call
    cached = cache.get_data(cache_key, key_json=key_json)
    if cached:
        return cached
```

### Workflow Caching (causaliq-workflow)

```python
from causaliq_core.cache import TokenCache
from causaliq_core.cache.compressors import JsonCompressor

# Cache scoped to workflow run
with TokenCache(f"workflows/{run_id}/cache.db") as cache:
    cache.set_compressor(JsonCompressor())

    # Cache step results
    cache.put_data(step_hash, result, key_json=step_key)
```

## Hash Collision Handling

The cache implements collision handling via the `key_json` and `seq` fields:

1. **Primary key**: `(hash, seq)` where `seq` starts at 0
2. **Collision detection**: When storing, if `hash` exists but `key_json`
   differs, `seq` is incremented
3. **Retrieval safety**: When `key_json` is provided to `get_data()`,
   only entries with matching `key_json` are returned

This prevents incorrect data retrieval when different keys produce
the same truncated hash.

## Concurrency

SQLite provides built-in concurrency handling:

- **WAL mode** (Write-Ahead Logging) for file-based caches
- Multiple readers, single writer
- Automatic retry on lock contention

For in-memory caches (`:memory:`), concurrency is handled by the
Python process (typically single-threaded usage).

## Import/Export

The import/export capability bridges different lifecycle phases:

| Phase | Format | Use |
|-------|--------|-----|
| Testing | JSON files | Human-readable fixtures |
| Production | SQLite + blobs | Fast, concurrent access |
| Archival | JSON/GraphML | Long-term preservation |

```python
from pathlib import Path
from causaliq_core.cache import TokenCache
from causaliq_core.cache.compressors import JsonCompressor

with TokenCache("./cache.db") as cache:
    cache.set_compressor(JsonCompressor())

    # Export for archival
    cache.export_entries(Path("./archive"))

    # Import from archive
    cache.import_entries(Path("./archive"))
```
