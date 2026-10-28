"""
Core action provider for GraphML, JSON and PDG compression.

Provides compress/decompress for the standard interchange formats used
by the workflow cache, in compact binary form.
"""

from __future__ import annotations

import json
from io import StringIO
from typing import Any, Dict, Optional, Set

from causaliq_core.action.graphml_codec import (
    _decode_graphml_edges,
    _decode_graphml_nodes,
    _decode_uint16,
    _encode_sdg_edges,
)
from causaliq_core.action.provider import (
    ActionResult,
    CausalIQActionProvider,
)
from causaliq_core.cache import TokenCache
from causaliq_core.graph import SDG
from causaliq_core.graph.io import graphml


class CoreActionProvider(CausalIQActionProvider):
    """Core action provider for graphml, json, and pdg compression.

    Provides compress/decompress for standard interchange formats.
    Used by workflow cache for compact binary storage.

    GraphML compression uses tokenised node names (2 bytes per node via
    TokenCache) plus compact binary edge list (5 bytes per edge).

    JSON compression uses tokenised JSON encoding via JsonCompressor.

    PDG compression uses compact binary format with 4 s.f. probability
    encoding (13 bytes per edge pair).

    It has no supported actions (run() returns skipped).

    Attributes:
        supported_types: {"graphml", "json", "pdg"}
    """

    name = "causaliq-core"
    version = "1.0.0"
    description = "Core compression provider for graphml, json, and pdg"
    author = "CausalIQ"

    supported_actions: Set[str] = set()
    supported_types: Set[str] = {"graphml", "json", "pdg"}

    def _execute(
        self,
        action: str,
        parameters: Dict[str, Any],
        mode: str,
        context: Optional[Any],
        logger: Optional[Any],
    ) -> ActionResult:
        """No-op execute - CoreActionProvider has no actions."""
        return ("skipped", {}, [])

    def compress(
        self,
        data_type: str,
        content: str,
        cache: TokenCache,
    ) -> bytes:
        """Compress textual content to compact binary blob.

        Args:
            data_type: "graphml" or "json".
            content: Textual interchange format string.
            cache: TokenCache for tokenisation.

        Returns:
            Compact binary blob.
        """
        if data_type not in self.supported_types:
            raise NotImplementedError(
                f"Provider '{self.name}' does not support compressing "
                f"data_type '{data_type}'. Supported: {self.supported_types}"
            )

        if data_type == "graphml":
            return self._compress_graphml(content, cache)
        elif data_type == "json":
            return self._compress_json(content, cache)
        else:  # pdg
            return self._compress_pdg(content, cache)

    def _compress_graphml(self, content: str, cache: TokenCache) -> bytes:
        """Compress GraphML to tokenised binary format.

        Format:
        - 2 bytes: number of nodes (uint16, big-endian)
        - For each node: 2 bytes token ID (uint16, big-endian)
        - 2 bytes: number of edges (uint16, big-endian)
        - For each edge: 2 bytes source idx + 2 bytes target idx +
          1 byte edge type

        Args:
            content: GraphML XML string.
            cache: TokenCache for node name tokenisation.

        Returns:
            Compact binary blob with tokenised node names.
        """
        # Parse GraphML to SDG
        sdg = graphml.read(StringIO(content))

        if len(sdg.nodes) > 65535:
            raise ValueError("Graph has too many nodes for compression")
        if len(sdg.edges) > 65535:
            raise ValueError("Graph has too many edges for compression")

        result = bytearray()

        # Encode number of nodes
        result.extend(len(sdg.nodes).to_bytes(2, "big"))

        # Encode each node as token ID (2 bytes each)
        for node in sdg.nodes:
            token_id = cache.get_or_create_token(node)
            result.extend(token_id.to_bytes(2, "big"))

        # Encode number of edges
        result.extend(len(sdg.edges).to_bytes(2, "big"))

        # Encode each edge (source idx, target idx, edge type)
        _encode_sdg_edges(result, sdg)

        return bytes(result)

    def _compress_json(self, content: str, cache: TokenCache) -> bytes:
        """Compress JSON to tokenised binary format."""
        from causaliq_core.cache.compressors import JsonCompressor

        data = json.loads(content)
        return JsonCompressor().compress(data, cache)

    def decompress(
        self,
        data_type: str,
        blob: bytes,
        cache: TokenCache,
    ) -> str:
        """Decompress binary blob back to textual content.

        Args:
            data_type: "graphml" or "json".
            blob: Compact binary blob from cache.
            cache: TokenCache for detokenisation.

        Returns:
            Textual interchange format string.
        """
        if data_type not in self.supported_types:
            raise NotImplementedError(
                f"Provider '{self.name}' does not support decompressing "
                f"data_type '{data_type}'. Supported: {self.supported_types}"
            )

        if data_type == "graphml":
            return self._decompress_graphml(blob, cache)
        elif data_type == "json":
            return self._decompress_json(blob, cache)
        else:  # pdg
            return self._decompress_pdg(blob, cache)

    def _decompress_graphml(self, blob: bytes, cache: TokenCache) -> str:
        """Decompress tokenised binary to GraphML string.

        Args:
            blob: Binary data from _compress_graphml.
            cache: TokenCache for node name detokenisation.

        Returns:
            GraphML XML string.
        """
        if len(blob) < 2:
            raise ValueError("Compressed graphml data too short")

        nodes, pos = _decode_graphml_nodes(blob, cache)
        num_edges, pos = _decode_uint16(blob, pos)
        edges = _decode_graphml_edges(blob, pos, num_edges, nodes)

        # Reconstruct SDG and write to GraphML
        sdg = SDG(nodes, edges)
        buffer = StringIO()
        graphml.write(sdg, buffer)
        return buffer.getvalue()

    def _decompress_json(self, blob: bytes, cache: TokenCache) -> str:
        """Decompress tokenised binary to JSON string."""
        from causaliq_core.cache.compressors import JsonCompressor

        data = JsonCompressor().decompress(blob, cache)
        return json.dumps(data, indent=2)

    def _compress_pdg(self, content: str, cache: TokenCache) -> bytes:
        """Compress PDG GraphML to compact binary format.

        The content is expected to be a GraphML representation of a PDG
        with edge probability attributes (p_forward, p_backward,
        p_undirected, p_none).

        Args:
            content: GraphML string representation of PDG.
            cache: TokenCache (unused, PDG uses self-contained compression).

        Returns:
            Compact binary blob from PDG.compress().
        """
        pdg = graphml.read_pdg(StringIO(content))
        return pdg.compress()

    def _decompress_pdg(self, blob: bytes, cache: TokenCache) -> str:
        """Decompress compact binary to PDG GraphML string.

        Args:
            blob: Binary data from PDG.compress().
            cache: TokenCache (unused, PDG uses self-contained compression).

        Returns:
            GraphML string representation of PDG.
        """
        from causaliq_core.graph.pdg import PDG

        pdg = PDG.decompress(blob)
        buffer = StringIO()
        graphml.write_pdg(pdg, buffer)
        return buffer.getvalue()
