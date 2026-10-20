"""
Action provider framework for CausalIQ workflow components.

This module provides the base classes and interfaces for implementing
action providers that expose multiple workflow actions.

The CausalIQActionProvider ABC defines the interface that all action
providers must implement. CoreActionProvider provides standard graphml
and json compression/decompression for workflow caches.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from io import StringIO
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from causaliq_core.cache import TokenCache
from causaliq_core.graph import SDG
from causaliq_core.graph.io import graphml
from causaliq_core.metadata import ActionMetadata

# Type alias for action result tuple: (status, metadata, objects).
# CausalIQ actions return structured metadata holding ``inputs`` and
# ``result``; a legacy flat mapping is accepted from third-party actions.
ActionResult = Tuple[
    str,
    Union[ActionMetadata, Dict[str, Any]],
    List[Dict[str, Any]],
]


class ActionPattern(Enum):
    """Workflow action execution patterns.

    Defines how actions interact with caches and matrix definitions.
    The workflow executor validates and enforces these patterns.

    Attributes:
        CREATE: Writes new cache entries. Requires an output cache and a
            matrix; a cache input is prohibited.
        AGGREGATE: Combines existing cache entries into new entries.
            Requires a cache input, an output cache and a matrix.
    """

    CREATE = "create"
    AGGREGATE = "aggregate"


@dataclass
class ActionInput:
    """Define action input specification.

    Attributes:
        name: Parameter name.
        description: Human-readable description.
        required: Whether the parameter is required.
        default: Default value if not provided.
        type_hint: Type hint string for documentation.
    """

    name: str
    description: str
    required: bool = False
    default: Any = None
    type_hint: str = "Any"


@dataclass
class ActionOutput:
    """Define action output specification.

    Attributes:
        name: Output name.
        description: Human-readable description.
        value: Output value.
    """

    name: str
    description: str
    value: Any


class ActionExecutionError(Exception):
    """Raised when action execution fails."""

    pass


class ActionValidationError(Exception):
    """Raised when action input validation fails."""

    pass


class CausalIQActionProvider(ABC):
    """Base class for action providers that expose multiple workflow actions.

    Action providers group related actions together. Each provider must
    declare which actions it supports via the supported_actions attribute.
    The 'action' input parameter selects which action to execute.

    Providers can also declare supported_types for compress/decompress
    operations. Workflow uses these to build a registry of which provider
    handles compression for each data type.

    Action patterns define how actions interact with workflow caches:
    - CREATE: Writes new entries (output + matrix required, input
              prohibited)
    - AGGREGATE: Combines entries (input + output + matrix required)

    Attributes:
        name: Provider identifier for workflow 'uses' field.
        version: Provider version string.
        description: Human-readable description.
        author: Provider author/maintainer.
        supported_actions: Set of action names this provider supports.
        action_patterns: Mapping of action names to their execution patterns.
        supported_types: Set of data types this provider can compress.
        inputs: Input parameter specifications.
        outputs: Output name to description mapping.
    """

    # Provider metadata
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = "CausalIQ"

    # Actions supported by this provider
    supported_actions: Set[str] = set()

    # Action patterns for workflow validation (action name -> pattern)
    action_patterns: Dict[str, ActionPattern] = {}

    # Data types this provider can compress/expand
    supported_types: Set[str] = set()

    # Input/output specifications
    inputs: Dict[str, ActionInput] = {}
    outputs: Dict[str, str] = {}  # name -> description mapping

    def run(
        self,
        action: str,
        parameters: Dict[str, Any],
        mode: str = "dry-run",
        context: Optional[Any] = None,
        logger: Optional[Any] = None,
    ) -> ActionResult:
        """Template method for action execution.

        This method implements the standard execution flow:
        1. Validate parameters via validate_parameters()
        2. If dry-run mode, return via _dry_run_result()
        3. Otherwise, execute via _execute()

        Subclasses should NOT override this method. Instead override:
        - validate_parameters() for parameter validation
        - _dry_run_result() for custom dry-run responses
        - _execute() for actual execution logic

        Args:
            action: Name of the action to execute (must be in
                supported_actions)
            parameters: Dictionary of parameter values for the action
            mode: Execution mode ('dry-run', 'run', 'force', 'compare')
            context: Workflow context for optimisation and intelligence
            logger: Optional logger for task execution reporting

        Returns:
            Tuple of (status, metadata, objects) where:
            - status: "success", "skipped", or "error"
            - metadata: Dictionary of execution metadata
            - objects: List of object dicts with keys:
                - type: Data type (e.g., "graphml", "json")
                - name: Object name identifier
                - content: String content

        Raises:
            ActionExecutionError: If action execution fails
            ActionValidationError: If validation fails
        """
        self.validate_parameters(action, parameters)
        if mode == "dry-run":
            return self._dry_run_result(action, parameters)
        return self._execute(action, parameters, mode, context, logger)

    def validate_parameters(
        self,
        action: str,
        parameters: Dict[str, Any],
    ) -> None:
        """Validate action name and parameters.

        Override this method to add provider-specific parameter validation.
        Always call super().validate_parameters() first to check the action
        name is supported.

        This method is called by run() before any execution, ensuring all
        validation errors are caught early (during workflow parsing).

        Args:
            action: Name of the action to validate.
            parameters: Dictionary of parameter values to validate.

        Raises:
            ActionValidationError: If action is not supported or
                parameters are invalid.
        """
        if not action:
            raise ActionValidationError("Missing 'action' parameter")
        if self.supported_actions and action not in self.supported_actions:
            raise ActionValidationError(
                f"Provider '{self.name}' does not support action '{action}'"
            )

    def _dry_run_result(
        self,
        action: str,
        parameters: Dict[str, Any],
    ) -> ActionResult:
        """Return result for dry-run mode without execution.

        Override this method to provide action-specific dry-run responses,
        such as estimated execution time or resource requirements.

        Args:
            action: Name of the action.
            parameters: Dictionary of validated parameter values.

        Returns:
            ActionResult tuple with status "skipped" and metadata.
        """
        return ("skipped", {"dry_run": True, "action": action}, [])

    @abstractmethod
    def _execute(
        self,
        action: str,
        parameters: Dict[str, Any],
        mode: str,
        context: Optional[Any],
        logger: Optional[Any],
    ) -> ActionResult:
        """Execute the action (called only when mode != "dry-run").

        Implement actual execution logic here. Parameters have already
        been validated by validate_parameters().

        Args:
            action: Name of the action to execute.
            parameters: Dictionary of validated parameter values.
            mode: Execution mode ('run', 'force', 'compare').
            context: Workflow context for optimisation.
            logger: Optional logger for task execution reporting.

        Returns:
            ActionResult tuple (status, metadata, objects).

        Raises:
            ActionExecutionError: If execution fails.
        """
        pass

    def compress(
        self,
        data_type: str,
        content: str,
        cache: TokenCache,
    ) -> bytes:
        """Compress textual content to compact binary blob for cache storage.

        Converts interchange format strings (e.g., GraphML, JSON) to
        compact binary blobs suitable for SQLite storage. Subclasses
        should override this to support their data types. The data_type
        must be declared in supported_types.

        Compression may use type-specific algorithms. For example, graphml
        compression parses the XML to extract edges as binary, and uses
        TokenCache to tokenise node names.

        Args:
            data_type: Type of data to compress (must be in
                supported_types).
            content: Textual interchange format string.
            cache: TokenCache instance for tokenisation.

        Returns:
            Compact binary blob representation.

        Raises:
            NotImplementedError: If the data type is not supported.
        """
        if data_type not in self.supported_types:
            raise NotImplementedError(
                f"Provider '{self.name}' does not support compressing "
                f"data_type '{data_type}'. Supported: {self.supported_types}"
            )
        raise NotImplementedError(
            f"Provider '{self.name}' has not implemented compress() "
            f"for data_type '{data_type}'"
        )

    def decompress(
        self,
        data_type: str,
        blob: bytes,
        cache: TokenCache,
    ) -> str:
        """Decompress compact binary blob back to textual content.

        Converts compact binary blobs from cache storage back to
        interchange format strings. Subclasses should override this
        to support their data types. The data_type must be declared
        in supported_types.

        Args:
            data_type: Type of data to decompress (must be in
                supported_types).
            blob: Compact binary blob from cache.
            cache: TokenCache instance for detokenisation.

        Returns:
            Textual interchange format string.

        Raises:
            NotImplementedError: If the data type is not supported.
        """
        if data_type not in self.supported_types:
            raise NotImplementedError(
                f"Provider '{self.name}' does not support decompressing "
                f"data_type '{data_type}'. Supported: {self.supported_types}"
            )
        raise NotImplementedError(
            f"Provider '{self.name}' has not implemented decompress() "
            f"for data_type '{data_type}'"
        )


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


# Export ActionProvider for auto-discovery by causaliq-workflow
ActionProvider = CoreActionProvider


def _encode_sdg_edges(result: bytearray, sdg: SDG) -> None:
    """Append the encoded edges of an SDG to a byte buffer.

    Args:
        result: Buffer to append the encoded edges to.
        sdg: Graph whose edges are encoded.
    """
    node_index = {node: i for i, node in enumerate(sdg.nodes)}
    for (source, target), edge_type in sdg.edges.items():
        result.extend(node_index[source].to_bytes(2, "big"))
        result.extend(node_index[target].to_bytes(2, "big"))
        result.extend(edge_type.value[0].to_bytes(1, "big"))


def _decode_uint16(blob: bytes, pos: int) -> Tuple[int, int]:
    """Return the big-endian uint16 at a position and the next position.

    Args:
        blob: Binary data to decode.
        pos: Position of the value.

    Returns:
        Tuple of (value, position after the value).

    Raises:
        ValueError: If the data ends before the value.
    """
    if pos + 2 > len(blob):
        raise ValueError("Compressed graphml data truncated")
    return int.from_bytes(blob[pos : pos + 2], "big"), pos + 2


def _decode_graphml_nodes(
    blob: bytes, cache: TokenCache
) -> Tuple[List[str], int]:
    """Return the tokenised node names of a compressed graphml blob.

    Args:
        blob: Binary data to decode.
        cache: TokenCache for node name detokenisation.

    Returns:
        Tuple of (node names, position after the names).

    Raises:
        ValueError: If the data is truncated or holds an unknown token.
    """
    num_nodes, pos = _decode_uint16(blob, 0)

    nodes = []
    for _ in range(num_nodes):
        token_id, pos = _decode_uint16(blob, pos)
        node = cache.get_token(token_id)
        if node is None:
            raise ValueError(f"Unknown token ID: {token_id}")
        nodes.append(node)

    return nodes, pos


def _decode_graphml_edges(
    blob: bytes, pos: int, num_edges: int, nodes: List[str]
) -> List[Tuple[str, str, str]]:
    """Return the edges of a compressed graphml blob.

    Args:
        blob: Binary data to decode.
        pos: Position of the first edge.
        num_edges: Number of edges to decode.
        nodes: Node names decoded so far.

    Returns:
        List of edge triples.

    Raises:
        ValueError: If the data is truncated or holds an invalid node
            index or edge type.
    """
    from causaliq_core.graph import EdgeType

    edge_type_lookup = {et.value[0]: et for et in EdgeType}

    edges = []
    for _ in range(num_edges):
        if pos + 5 > len(blob):
            raise ValueError("Compressed graphml data truncated")
        source_idx, pos = _decode_uint16(blob, pos)
        target_idx, pos = _decode_uint16(blob, pos)
        edge_type_id = int.from_bytes(blob[pos : pos + 1], "big")
        pos += 1
        edges.append(
            _decode_graphml_edge(
                source_idx, target_idx, edge_type_id, nodes, edge_type_lookup
            )
        )

    return edges


def _decode_graphml_edge(
    source_idx: int,
    target_idx: int,
    edge_type_id: int,
    nodes: List[str],
    edge_type_lookup: Dict[int, Any],
) -> Tuple[str, str, str]:
    """Return one decoded edge triple from a compressed graphml blob.

    Args:
        source_idx: Index of the source node.
        target_idx: Index of the target node.
        edge_type_id: Encoded identifier of the edge type.
        nodes: Node names decoded so far.
        edge_type_lookup: Mapping of encoded identifier to EdgeType.

    Returns:
        Edge triple (source, symbol, target).

    Raises:
        ValueError: If a node index or the edge type is invalid.
    """
    if source_idx >= len(nodes) or target_idx >= len(nodes):
        raise ValueError("Compressed graphml has invalid node index")
    if edge_type_id not in edge_type_lookup:
        raise ValueError("Compressed graphml has invalid edge type")
    edge_type = edge_type_lookup[edge_type_id]
    return nodes[source_idx], edge_type.value[3], nodes[target_idx]
