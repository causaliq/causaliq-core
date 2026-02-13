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
from io import StringIO
from typing import Any, Dict, List, Optional, Set, Tuple

from causaliq_core.cache import TokenCache
from causaliq_core.graph import SDG
from causaliq_core.graph.io import graphml

# Type alias for action result tuple: (status, metadata, objects)
ActionResult = Tuple[str, Dict[str, Any], List[Dict[str, Any]]]


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

    Providers can also declare supported_types for compress/expand
    operations. Workflow uses these to build a registry of which provider
    handles compression for each data type.

    Providers can capture execution metadata during run() which can be
    retrieved via get_action_metadata() after execution completes.
    This supports workflow caching and auditing use cases.

    Attributes:
        name: Provider identifier for workflow 'uses' field.
        version: Provider version string.
        description: Human-readable description.
        author: Provider author/maintainer.
        supported_actions: Set of action names this provider supports.
        supported_types: Set of data types this provider can compress/expand.
        inputs: Input parameter specifications.
        outputs: Output name to description mapping.
        _execution_metadata: Internal storage for execution metadata.
    """

    # Provider metadata
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = "CausalIQ"

    # Actions supported by this provider
    supported_actions: Set[str] = set()

    # Data types this provider can compress/expand
    supported_types: Set[str] = set()

    # Input/output specifications
    inputs: Dict[str, ActionInput] = {}
    outputs: Dict[str, str] = {}  # name -> description mapping

    def __init__(self) -> None:
        """Initialise provider with empty execution metadata."""
        self._execution_metadata: Dict[str, Any] = {}

    @abstractmethod
    def run(
        self,
        action: str,
        parameters: Dict[str, Any],
        mode: str = "dry-run",
        context: Optional[Any] = None,
        logger: Optional[Any] = None,
    ) -> ActionResult:
        """Execute the specified action with validated parameters.

        The action parameter specifies which action to execute.
        Implementations should validate that action is in supported_actions.

        Implementations should populate self._execution_metadata with
        relevant metadata during execution for later retrieval via
        get_action_metadata().

        Args:
            action: Name of the action to execute (must be in
                supported_actions)
            parameters: Dictionary of parameter values for the action
            mode: Execution mode ('dry-run', 'run', 'compare')
            context: Workflow context for optimisation and intelligence
            logger: Optional logger for task execution reporting

        Returns:
            Tuple of (status, metadata, objects) where:
            - status: "success", "skipped", or "error"
            - metadata: Dictionary of execution metadata
            - objects: List of serialised object dicts with keys:
                - type: Data type (e.g., "graphml", "json")
                - name: Object name identifier
                - content: Serialised string content

        Raises:
            ActionExecutionError: If action execution fails
            ActionValidationError: If action is not supported
        """
        pass

    def validate_parameters(
        self, action: str, parameters: Dict[str, Any]
    ) -> bool:
        """Validate action and parameters against specifications.

        Validates that:
        1. The action is in supported_actions (if specified)
        2. All required parameters are provided

        Args:
            action: Name of the action to validate
            parameters: Dictionary of parameter values to validate

        Returns:
            True if action and parameters are valid

        Raises:
            ActionValidationError: If validation fails
        """
        # Validate action is supported if supported_actions is defined
        if self.supported_actions:
            if action not in self.supported_actions:
                raise ActionValidationError(
                    f"Unsupported action '{action}'. "
                    f"Supported: {self.supported_actions}"
                )
        return True  # Default: accept all parameters

    def get_action_metadata(self) -> Dict[str, Any]:
        """Return metadata about the provider execution.

        Called after run() completes to retrieve execution metadata
        for workflow caching and auditing purposes. Subclasses should
        populate self._execution_metadata during run() execution.

        The base implementation returns _execution_metadata with
        standard fields (action_name, action_version) added.

        Returns:
            Dictionary of metadata relevant to this provider.
            Always includes 'action_name' and 'action_version'.
        """
        base_metadata = {
            "action_name": self.name,
            "action_version": self.version,
        }
        return {**base_metadata, **self._execution_metadata}

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
    """Core action provider for graphml and json compression.

    Provides compress/decompress for standard interchange formats.
    Used by workflow cache for compact binary storage.

    GraphML compression uses tokenised node names (2 bytes per node via
    TokenCache) plus compact binary edge list (5 bytes per edge).

    JSON compression uses tokenised JSON encoding via JsonEncoder.

    It has no supported actions (run() returns skipped).

    Attributes:
        supported_types: {"graphml", "json"}
    """

    name = "causaliq-core"
    version = "1.0.0"
    description = "Core compression provider for graphml and json"
    author = "CausalIQ"

    supported_actions: Set[str] = set()
    supported_types: Set[str] = {"graphml", "json"}

    def run(
        self,
        action: str,
        parameters: Dict[str, Any],
        mode: str = "dry-run",
        context: Optional[Any] = None,
        logger: Optional[Any] = None,
    ) -> ActionResult:
        """No-op run method - CoreActionProvider has no actions."""
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
        else:  # json
            return self._compress_json(content, cache)

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

        # Build node index for edge encoding
        node_index = {node: i for i, node in enumerate(sdg.nodes)}

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
        for (source, target), edge_type in sdg.edges.items():
            result.extend(node_index[source].to_bytes(2, "big"))
            result.extend(node_index[target].to_bytes(2, "big"))
            result.extend(edge_type.value[0].to_bytes(1, "big"))

        return bytes(result)

    def _compress_json(self, content: str, cache: TokenCache) -> bytes:
        """Compress JSON to tokenised binary format."""
        from causaliq_core.cache.encoders.json_encoder import JsonEncoder

        data = json.loads(content)
        return JsonEncoder().encode(data, cache)

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
        else:  # json
            return self._decompress_json(blob, cache)

    def _decompress_graphml(self, blob: bytes, cache: TokenCache) -> str:
        """Decompress tokenised binary to GraphML string.

        Args:
            blob: Binary data from _compress_graphml.
            cache: TokenCache for node name detokenisation.

        Returns:
            GraphML XML string.
        """
        from causaliq_core.graph import EdgeType

        if len(blob) < 2:
            raise ValueError("Compressed graphml data too short")

        pos = 0

        # Decode number of nodes
        num_nodes = int.from_bytes(blob[pos : pos + 2], "big")
        pos += 2

        # Decode node names from token IDs
        nodes = []
        for _ in range(num_nodes):
            if pos + 2 > len(blob):
                raise ValueError("Compressed graphml data truncated")
            token_id = int.from_bytes(blob[pos : pos + 2], "big")
            pos += 2
            node = cache.get_token(token_id)
            if node is None:
                raise ValueError(f"Unknown token ID: {token_id}")
            nodes.append(node)

        # Decode number of edges
        if pos + 2 > len(blob):
            raise ValueError("Compressed graphml data truncated")
        num_edges = int.from_bytes(blob[pos : pos + 2], "big")
        pos += 2

        # Build edge type lookup
        edge_type_lookup = {et.value[0]: et for et in EdgeType}

        # Decode edges
        edges = []
        for _ in range(num_edges):
            if pos + 5 > len(blob):
                raise ValueError("Compressed graphml data truncated")
            source_idx = int.from_bytes(blob[pos : pos + 2], "big")
            pos += 2
            target_idx = int.from_bytes(blob[pos : pos + 2], "big")
            pos += 2
            edge_type_id = int.from_bytes(blob[pos : pos + 1], "big")
            pos += 1

            if source_idx >= len(nodes) or target_idx >= len(nodes):
                raise ValueError("Compressed graphml has invalid node index")
            if edge_type_id not in edge_type_lookup:
                raise ValueError("Compressed graphml has invalid edge type")

            edge_type = edge_type_lookup[edge_type_id]
            edges.append(
                (nodes[source_idx], edge_type.value[3], nodes[target_idx])
            )

        # Reconstruct SDG and write to GraphML
        sdg = SDG(nodes, edges)
        buffer = StringIO()
        graphml.write(sdg, buffer)
        return buffer.getvalue()

    def _decompress_json(self, blob: bytes, cache: TokenCache) -> str:
        """Decompress tokenised binary to JSON string."""
        from causaliq_core.cache.encoders.json_encoder import JsonEncoder

        data = JsonEncoder().decode(blob, cache)
        return json.dumps(data, indent=2)


# Convenience alias for backward compatibility
BaseActionProvider = CausalIQActionProvider

# Export ActionProvider for auto-discovery by causaliq-workflow
ActionProvider = CoreActionProvider
