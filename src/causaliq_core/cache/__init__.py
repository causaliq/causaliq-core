"""
Core caching infrastructure for CausalIQ.

This module provides a generic caching system with:
- SQLite-backed storage with concurrency support
- Pluggable compressors for data compression
- Shared token dictionary for cross-entry compression
- Import/export for human-readable formats
"""

from causaliq_core.cache.token_cache import TokenCache

__all__ = [
    "TokenCache",
]
