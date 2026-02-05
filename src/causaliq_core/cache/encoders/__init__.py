"""
Cache entry encoders for CausalIQ.

Provides pluggable encoders for type-specific compression:
- EntryEncoder: Abstract base class for encoders
- JsonEncoder: Tokenised JSON compression (50-70% reduction)

Migrated from causaliq-knowledge for shared use across the ecosystem.
"""

from causaliq_core.cache.encoders.base import EntryEncoder
from causaliq_core.cache.encoders.json_encoder import JsonEncoder

__all__ = [
    "EntryEncoder",
    "JsonEncoder",
]
