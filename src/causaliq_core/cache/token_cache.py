"""
TokenCache: SQLite-backed cache with shared token dictionary.

Provides efficient storage for cache entries with:
- Fast indexed key lookup via SQLite
- In-memory mode via :memory:
- Concurrency support via SQLite locking
- Shared token dictionary for cross-entry compression
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:  # pragma: no cover
    from causaliq_core.cache.compressors.base import Compressor


class TokenCache:
    """SQLite-backed cache with shared token dictionary.

    Attributes:
        db_path: Path to SQLite database file, or ":memory:" for in-memory.
        conn: SQLite connection (None until open() called or context entered).

    Example:
        >>> with TokenCache(":memory:") as cache:
        ...     cache.put("abc123", b"hello")
        ...     data = cache.get("abc123")
    """

    # SQL statements for schema creation
    _SCHEMA_SQL = """
        -- Token dictionary (grows dynamically, shared across compressors)
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            frequency INTEGER DEFAULT 1
        );

        -- Generic cache entries with collision handling
        CREATE TABLE IF NOT EXISTS cache_entries (
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

        -- Index for common queries
        CREATE INDEX IF NOT EXISTS idx_created_at
            ON cache_entries(created_at);
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialise TokenCache.

        Args:
            db_path: Path to SQLite database file. Use ":memory:" for
                in-memory database (fast, non-persistent).
        """
        self.db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None
        # In-memory token dictionary for fast lookup
        self._token_to_id: dict[str, int] = {}
        self._id_to_token: dict[int, str] = {}
        # Single compressor for auto-compressing data
        self._compressor: Compressor | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        """Get the database connection, raising if not connected."""
        if self._conn is None:
            raise RuntimeError(
                "TokenCache not connected. Use 'with cache:' or call open()."
            )
        return self._conn

    @property
    def is_open(self) -> bool:
        """Check if the cache connection is open."""
        return self._conn is not None

    @property
    def is_memory(self) -> bool:
        """Check if this is an in-memory database."""
        return self.db_path == ":memory:"

    def open(self) -> TokenCache:
        """Open the database connection and initialise schema.

        Returns:
            self for method chaining.

        Raises:
            RuntimeError: If already connected.
        """
        if self._conn is not None:
            raise RuntimeError("TokenCache already connected.")

        self._conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,  # Allow multi-threaded access
        )
        # Enable foreign keys and WAL mode for better concurrency
        self._conn.execute("PRAGMA foreign_keys = ON")
        if not self.is_memory:  # pragma: no cover
            self._conn.execute("PRAGMA journal_mode = WAL")

        self._init_schema()
        return self

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _init_schema(self) -> None:
        """Create database tables if they don't exist."""
        self.conn.executescript(self._SCHEMA_SQL)
        self.conn.commit()
        self._load_token_dict()

    def _load_token_dict(self) -> None:
        """Load token dictionary from database into memory."""
        cursor = self.conn.execute("SELECT id, token FROM tokens")
        self._token_to_id.clear()
        self._id_to_token.clear()
        for row in cursor:  # pragma: no cover
            token_id, token = row[0], row[1]
            self._token_to_id[token] = token_id
            self._id_to_token[token_id] = token

    def __enter__(self) -> TokenCache:
        """Context manager entry - opens connection."""
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Context manager exit - closes connection."""
        self.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Cursor]:
        """Context manager for a database transaction.

        Commits on success, rolls back on exception.

        Yields:
            SQLite cursor for executing statements.
        """
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cursor.close()

    def _utcnow_iso(self) -> str:
        """Get current UTC time as ISO 8601 string."""
        return datetime.now(timezone.utc).isoformat()

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database.

        Args:
            table_name: Name of the table to check.

        Returns:
            True if table exists, False otherwise.
        """
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master " "WHERE type='table' AND name=?",
            (table_name,),
        )
        return cursor.fetchone() is not None

    def entry_count(self) -> int:
        """Count cache entries.

        Returns:
            Number of entries in the cache.
        """
        cursor = self.conn.execute("SELECT COUNT(*) FROM cache_entries")
        row = cursor.fetchone()
        return int(row[0]) if row else 0

    def token_count(self) -> int:
        """Count tokens in the dictionary.

        Returns:
            Number of tokens.
        """
        cursor = self.conn.execute("SELECT COUNT(*) FROM tokens")
        row = cursor.fetchone()
        return int(row[0]) if row else 0

    def list_entries(self) -> list[dict[str, Any]]:
        """List all cache entries with metadata.

        Returns a list of dictionaries containing entry details including
        hash, key_json, created_at, and metadata blob.

        Returns:
            List of entry dictionaries with keys: hash, key_json,
            created_at, metadata (raw bytes or None).

        Example:
            >>> with TokenCache(":memory:") as cache:
            ...     cache.set_compressor(JsonCompressor())
            ...     cache.put_data("h1", {"test": 1})
            ...     entries = cache.list_entries()
            ...     len(entries)
            1
        """
        cursor = self.conn.execute(
            "SELECT hash, key_json, created_at, metadata "
            "FROM cache_entries ORDER BY created_at"
        )

        entries = []
        for row in cursor:
            entries.append(
                {
                    "hash": row[0],
                    "key_json": row[1],
                    "created_at": row[2],
                    "metadata": row[3],
                }
            )
        return entries

    def total_hits(self) -> int:
        """Get total cache hits across all entries.

        Returns:
            Total hit count.
        """
        cursor = self.conn.execute(
            "SELECT COALESCE(SUM(hit_count), 0) FROM cache_entries"
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0

    def get_or_create_token(self, token: str) -> int:
        """Get token ID, creating a new entry if needed.

        This method is used by compressors to compress strings to integer
        IDs. The token dictionary grows dynamically as new tokens are
        encountered.

        Args:
            token: The string token to look up or create.

        Returns:
            Integer ID for the token (1-65535 range).

        Raises:
            ValueError: If token dictionary exceeds uint16 capacity.
        """
        # Fast path: check in-memory cache
        if token in self._token_to_id:
            return self._token_to_id[token]

        # Slow path: insert into database
        cursor = self.conn.execute(
            "INSERT INTO tokens (token) VALUES (?) RETURNING id",
            (token,),
        )
        token_id: int = cursor.fetchone()[0]
        self.conn.commit()

        # Check uint16 capacity (max 65,535 tokens)
        if token_id > 65535:  # pragma: no cover
            raise ValueError(
                f"Token dictionary exceeded uint16 capacity: {token_id}"
            )

        # Update in-memory cache
        self._token_to_id[token] = token_id
        self._id_to_token[token_id] = token

        return token_id

    def get_token(self, token_id: int) -> str | None:
        """Get token string by ID.

        This method is used by decompressors to expand integer IDs back
        to strings.

        Args:
            token_id: The integer ID to look up.

        Returns:
            The token string, or None if not found.
        """
        return self._id_to_token.get(token_id)

    # ========================================================================
    # Cache entry operations
    # ========================================================================

    def put(
        self,
        hash: str,
        data: bytes,
        metadata: bytes | None = None,
        key_json: str = "",
    ) -> None:
        """Store a cache entry with collision handling.

        If an entry with the same hash exists but different key_json,
        a new entry is created with incremented seq (collision).
        If key_json matches, the existing entry is updated.

        Args:
            hash: Unique identifier for the entry (e.g. SHA-256 truncated).
            data: Binary data to store.
            metadata: Optional binary metadata.
            key_json: Original unhashed key as JSON string for collision
                detection. Empty string if not provided.
        """
        # Check for existing entries with this hash
        cursor = self.conn.execute(
            "SELECT seq, key_json FROM cache_entries "
            "WHERE hash = ? ORDER BY seq",
            (hash,),
        )
        rows = cursor.fetchall()

        if not rows:
            # No existing entry - insert with seq=0
            self.conn.execute(
                "INSERT INTO cache_entries "
                "(hash, seq, key_json, data, created_at, metadata)"
                " VALUES (?, 0, ?, ?, ?, ?)",
                (
                    hash,
                    key_json,
                    data,
                    self._utcnow_iso(),
                    metadata,
                ),
            )
        else:
            # Check if key_json matches any existing entry
            for seq, existing_key_json in rows:
                if existing_key_json == key_json:
                    # Same key - update existing entry
                    self.conn.execute(
                        "UPDATE cache_entries SET data = ?, metadata = ?, "
                        "created_at = ? "
                        "WHERE hash = ? AND seq = ?",
                        (
                            data,
                            metadata,
                            self._utcnow_iso(),
                            hash,
                            seq,
                        ),
                    )
                    self.conn.commit()
                    return

            # Collision: key_json doesn't match any existing - insert new seq
            max_seq = max(row[0] for row in rows)
            self.conn.execute(
                "INSERT INTO cache_entries "
                "(hash, seq, key_json, data, created_at, metadata)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    hash,
                    max_seq + 1,
                    key_json,
                    data,
                    self._utcnow_iso(),
                    metadata,
                ),
            )

        self.conn.commit()

    def get(
        self,
        hash: str,
        key_json: str = "",
    ) -> bytes | None:
        """Retrieve a cache entry and increment hit count.

        If key_json is provided, only returns data if key_json matches.
        This prevents returning wrong data in case of hash collisions.

        Args:
            hash: Unique identifier for the entry.
            key_json: Original unhashed key for collision verification.
                If empty string, returns first matching entry (legacy mode).

        Returns:
            Binary data if found, None otherwise.
        """
        if key_json:
            # Exact match required for collision safety
            cursor = self.conn.execute(
                "SELECT seq, data FROM cache_entries "
                "WHERE hash = ? AND key_json = ?",
                (hash, key_json),
            )
        else:
            # Legacy mode: return first match (seq=0)
            cursor = self.conn.execute(
                "SELECT seq, data FROM cache_entries "
                "WHERE hash = ? ORDER BY seq LIMIT 1",
                (hash,),
            )

        row = cursor.fetchone()
        if row:
            seq, data = row
            # Increment hit count and update last accessed time
            self.conn.execute(
                "UPDATE cache_entries SET hit_count = hit_count + 1, "
                "last_accessed_at = ? "
                "WHERE hash = ? AND seq = ?",
                (self._utcnow_iso(), hash, seq),
            )
            self.conn.commit()
            result: bytes = data
            return result
        return None

    def get_with_metadata(
        self,
        hash: str,
        key_json: str = "",
    ) -> tuple[bytes, bytes | None] | None:
        """Retrieve a cache entry with its metadata.

        Args:
            hash: Unique identifier for the entry.
            key_json: Original unhashed key for collision verification.
                If empty string, returns first matching entry (legacy mode).

        Returns:
            Tuple of (data, metadata) if found, None otherwise.
        """
        if key_json:
            cursor = self.conn.execute(
                "SELECT data, metadata FROM cache_entries "
                "WHERE hash = ? AND key_json = ?",
                (hash, key_json),
            )
        else:
            cursor = self.conn.execute(
                "SELECT data, metadata FROM cache_entries "
                "WHERE hash = ? ORDER BY seq LIMIT 1",
                (hash,),
            )
        row = cursor.fetchone()
        return (row[0], row[1]) if row else None

    def exists(self, hash: str, key_json: str = "") -> bool:
        """Check if a cache entry exists.

        Args:
            hash: Unique identifier for the entry.
            key_json: Original unhashed key for collision verification.
                If empty string, checks for any entry with this hash.

        Returns:
            True if entry exists, False otherwise.
        """
        if key_json:
            cursor = self.conn.execute(
                "SELECT 1 FROM cache_entries "
                "WHERE hash = ? AND key_json = ?",
                (hash, key_json),
            )
        else:
            cursor = self.conn.execute(
                "SELECT 1 FROM cache_entries WHERE hash = ?",
                (hash,),
            )
        return cursor.fetchone() is not None

    def delete(
        self,
        hash: str,
        key_json: str = "",
    ) -> bool:
        """Delete a cache entry.

        Args:
            hash: Unique identifier for the entry.
            key_json: Original unhashed key for collision verification.
                If empty string, deletes all entries with this hash.

        Returns:
            True if entry was deleted, False if it didn't exist.
        """
        if key_json:
            cursor = self.conn.execute(
                "DELETE FROM cache_entries " "WHERE hash = ? AND key_json = ?",
                (hash, key_json),
            )
        else:
            cursor = self.conn.execute(
                "DELETE FROM cache_entries WHERE hash = ?",
                (hash,),
            )
        self.conn.commit()
        return cursor.rowcount > 0

    # ========================================================================
    # Compressor registration and auto-compression operations
    # ========================================================================

    def set_compressor(self, compressor: Compressor) -> None:
        """Set the compressor for automatic data compression.

        Once set, `put_data()` and `get_data()` will automatically
        compress/decompress entries using this compressor.

        Args:
            compressor: Compressor instance for data compression.

        Example:
            >>> from causaliq_core.cache.compressors import JsonCompressor
            >>> with TokenCache(":memory:") as cache:
            ...     cache.set_compressor(JsonCompressor())
            ...     cache.put_data("key1", {"msg": "hello"})
        """
        self._compressor = compressor

    def get_compressor(self) -> Compressor | None:
        """Get the current compressor.

        Returns:
            The registered compressor, or None if not set.
        """
        return self._compressor

    def has_compressor(self) -> bool:
        """Check if a compressor is set.

        Returns:
            True if compressor is set, False otherwise.
        """
        return self._compressor is not None

    def put_data(
        self,
        hash: str,
        data: Any,
        metadata: Any | None = None,
        key_json: str = "",
    ) -> None:
        """Store data using the registered compressor.

        This method automatically compresses the data using the compressor
        set via `set_compressor()`. Use `put()` for raw bytes.

        Args:
            hash: Unique identifier for the entry.
            data: Data to compress and store.
            metadata: Optional metadata to compress and store.
            key_json: Original unhashed key as JSON string for collision
                detection. Empty string if not provided.

        Raises:
            RuntimeError: If no compressor is set.

        Example:
            >>> with TokenCache(":memory:") as cache:
            ...     cache.set_compressor(JsonCompressor())
            ...     cache.put_data("abc", {"key": "value"})
        """
        if self._compressor is None:
            raise RuntimeError("No compressor set. Call set_compressor first.")
        blob = self._compressor.compress(data, self)
        meta_blob = (
            self._compressor.compress(metadata, self)
            if metadata is not None
            else None
        )
        self.put(hash, blob, meta_blob, key_json)

    def get_data(
        self,
        hash: str,
        key_json: str = "",
    ) -> Any | None:
        """Retrieve and decompress data using the registered compressor.

        This method automatically decompresses the data using the compressor
        set via `set_compressor()`. Use `get()` for raw bytes.

        Args:
            hash: Unique identifier for the entry.
            key_json: Original unhashed key for collision verification.
                If empty string, returns first matching entry (legacy mode).

        Returns:
            Decompressed data if found, None otherwise.

        Raises:
            RuntimeError: If no compressor is set.

        Example:
            >>> with TokenCache(":memory:") as cache:
            ...     cache.set_compressor(JsonCompressor())
            ...     cache.put_data("abc", {"key": "value"})
            ...     data = cache.get_data("abc")
        """
        blob = self.get(hash, key_json)
        if blob is None:
            return None
        if self._compressor is None:
            raise RuntimeError("No compressor set. Call set_compressor first.")
        return self._compressor.decompress(blob, self)

    def get_data_with_metadata(
        self,
        hash: str,
        key_json: str = "",
    ) -> tuple[Any, Any | None] | None:
        """Retrieve and decompress data with metadata.

        Args:
            hash: Unique identifier for the entry.
            key_json: Original unhashed key for collision verification.
                If empty string, returns first matching entry (legacy mode).

        Returns:
            Tuple of (decompressed_data, decompressed_metadata) if found,
            None otherwise. metadata may be None if not stored.

        Raises:
            RuntimeError: If no compressor is set.
        """
        result = self.get_with_metadata(hash, key_json)
        if result is None:
            return None
        if self._compressor is None:
            raise RuntimeError("No compressor set. Call set_compressor first.")
        data_blob, meta_blob = result
        decompressed_data = self._compressor.decompress(data_blob, self)
        decompressed_meta = (
            self._compressor.decompress(meta_blob, self) if meta_blob else None
        )
        return (decompressed_data, decompressed_meta)

    # ========================================================================
    # Import/Export operations
    # ========================================================================

    def export_entries(
        self,
        output_dir: Path,
        fmt: str | None = None,
    ) -> int:
        """Export cache entries to human-readable files.

        Each entry is exported to a separate file named `{hash}.{ext}` where
        ext is determined by the format or compressor's default_export_format.

        Args:
            output_dir: Directory to write exported files to. Created if
                it doesn't exist.
            fmt: Export format (e.g. 'json', 'yaml'). If None, uses the
                compressor's default_export_format.

        Returns:
            Number of entries exported.

        Raises:
            RuntimeError: If no compressor is set.

        Example:
            >>> from pathlib import Path
            >>> from causaliq_core.cache import TokenCache
            >>> from causaliq_core.cache.compressors import JsonCompressor
            >>> with TokenCache(":memory:") as cache:
            ...     cache.set_compressor(JsonCompressor())
            ...     cache.put_data("abc123", {"key": "value"})
            ...     count = cache.export_entries(Path("./export"))
            ...     # Creates ./export/abc123.json
        """
        if self._compressor is None:
            raise RuntimeError("No compressor set. Call set_compressor first.")
        ext = fmt or self._compressor.default_export_format

        # Create output directory if needed
        output_dir.mkdir(parents=True, exist_ok=True)

        # Query all entries
        cursor = self.conn.execute("SELECT hash, data FROM cache_entries")

        count = 0
        for hash_val, blob in cursor:
            # Decompress the blob to get original data
            data = self._compressor.decompress(blob, self)
            # Export to file using compressor's export method
            file_path = output_dir / f"{hash_val}.{ext}"
            self._compressor.export(data, file_path)
            count += 1

        return count

    def import_entries(
        self,
        input_dir: Path,
    ) -> int:
        """Import human-readable files into the cache.

        Each file is imported with its stem (filename without extension)
        used as the cache hash. The compressor's import_() method reads the
        file and the data is compressed before storage.

        Args:
            input_dir: Directory containing files to import.

        Returns:
            Number of entries imported.

        Raises:
            RuntimeError: If no compressor is set.
            FileNotFoundError: If input_dir doesn't exist.

        Example:
            >>> from pathlib import Path
            >>> from causaliq_core.cache import TokenCache
            >>> from causaliq_core.cache.compressors import JsonCompressor
            >>> with TokenCache(":memory:") as cache:
            ...     cache.set_compressor(JsonCompressor())
            ...     count = cache.import_entries(Path("./import"))
            ...     # Imports all files from ./import
        """
        if self._compressor is None:
            raise RuntimeError("No compressor set. Call set_compressor first.")

        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")

        count = 0
        for file_path in input_dir.iterdir():
            if file_path.is_file():
                # Use filename (without extension) as hash
                hash_val = file_path.stem
                # Import data using compressor
                data = self._compressor.import_(file_path)
                # Compress and store
                self.put_data(hash_val, data)
                count += 1

        return count
