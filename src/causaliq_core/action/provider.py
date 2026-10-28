"""
Base class for CausalIQ action providers.

The :class:`CausalIQActionProvider` ABC defines the template method that
runs an action, the validation hook that runs before execution and the
compression hooks used by the workflow cache.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from causaliq_core.action.errors import ActionValidationError
from causaliq_core.action.parameters import _check_input_specs
from causaliq_core.action.spec import ActionInput, ActionPattern
from causaliq_core.cache import TokenCache
from causaliq_core.metadata import ActionMetadata

# Type alias for action result tuple: (status, metadata, objects).
# CausalIQ actions return structured metadata holding ``inputs`` and
# ``result``; a legacy flat mapping is accepted from third-party actions.
ActionResult = Tuple[
    str,
    Union[ActionMetadata, Dict[str, Any]],
    List[Dict[str, Any]],
]


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

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Check the input specification contract for a new provider.

        Every declared default must be a value the user could supply, a
        required input must not declare one, and a null default is
        rejected. This runs when the provider class is defined, so an
        inconsistent provider fails at load time and is reported by the
        workflow registry as a discovery error.

        Args:
            **kwargs: Class keyword arguments passed to the base class.

        Raises:
            ActionValidationError: If an input specification is
                inconsistent.
        """
        super().__init_subclass__(**kwargs)
        _check_input_specs(cls.name or cls.__name__, cls.inputs)

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
