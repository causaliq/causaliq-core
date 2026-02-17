"""
Abstract base class for cache entry compressors.

Compressors transform data to/from compact binary representations,
optionally using a shared token dictionary for compression.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from causaliq_core.cache.token_cache import TokenCache


class Compressor(ABC):
    """Abstract base class for cache entry compressors.

    Compressors handle:
    - Compressing data to compact binary format for storage
    - Decompressing binary data back to original structure
    - Exporting to human-readable formats (JSON, GraphML, etc.)
    - Importing from human-readable formats

    Compressors may use the shared token dictionary in TokenCache
    for cross-entry compression of repeated strings.

    Example:
        >>> class MyCompressor(Compressor):
        ...     def compress(self, data, token_cache):
        ...         return json.dumps(data).encode()
        ...     def decompress(self, blob, token_cache):
        ...         return json.loads(blob.decode())
        ...     # ... export/import methods
    """

    @property
    def default_export_format(self) -> str:  # pragma: no cover
        """Default file extension for exports (e.g. 'json', 'graphml')."""
        return "json"

    @abstractmethod
    def compress(self, data: Any, token_cache: TokenCache) -> bytes:
        """Compress data to binary format.

        Args:
            data: The data to compress (type depends on compressor).
            token_cache: Cache instance for shared token dictionary.

        Returns:
            Compact binary representation.
        """
        ...

    @abstractmethod
    def decompress(self, blob: bytes, token_cache: TokenCache) -> Any:
        """Decompress binary data back to original structure.

        Args:
            blob: Binary data from cache.
            token_cache: Cache instance for shared token dictionary.

        Returns:
            Decompressed data in original format.
        """
        ...

    @abstractmethod
    def export(self, data: Any, path: Path) -> None:
        """Export data to human-readable file format.

        Args:
            data: The data to export (decompressed format).
            path: Destination file path.
        """
        ...

    @abstractmethod
    def import_(self, path: Path) -> Any:
        """Import data from human-readable file format.

        Args:
            path: Source file path.

        Returns:
            Imported data ready for compression.
        """
        ...
