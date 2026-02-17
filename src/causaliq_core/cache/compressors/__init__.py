"""
Cache entry compressors for CausalIQ.

Provides pluggable compressors for data compression:
- Compressor: Abstract base class for compressors
- JsonCompressor: Tokenised JSON compression (50-70% reduction)
"""

from causaliq_core.cache.compressors.base import Compressor
from causaliq_core.cache.compressors.json_compressor import JsonCompressor

__all__ = [
    "Compressor",
    "JsonCompressor",
]
