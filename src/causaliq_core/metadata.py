"""Standard metadata envelope for CausalIQ workflow results.

Defines schema version 2 of the metadata stored with cached workflow
entries and exported as ``_meta.json``. The envelope separates:

- ``provenance``: who produced the entry, when, and in what environment;
- ``inputs``: the effective parameters used by the action;
- ``result``: what the action produced;
- ``history``: metadata inherited from earlier actions.

Actions return an :class:`ActionMetadata` mapping holding ``inputs`` and
``result``. The framework adds the provenance and history blocks, so the
envelope is constructed in one place.

See ``docs/architecture/metadata_structure.md`` in ``causaliq-workflow``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, TypedDict

__all__ = [
    "ActionMetadata",
    "MetadataError",
    "MetadataParts",
    "PROVENANCE_KEYS",
    "RESERVED_KEYS",
    "SCHEMA_VERSION",
    "build_metadata",
    "is_v2_metadata",
    "normalise_metadata",
    "split_metadata",
]

SCHEMA_VERSION = 2
"""Version of the metadata envelope written by this package."""

RESERVED_KEYS = frozenset({"provenance", "inputs", "result", "history"})
"""Keys reserved at the top level of the metadata envelope."""

PROVENANCE_KEYS = (
    "provider",
    "provider_version",
    "workflow_version",
    "action",
    "started_at",
    "finished_at",
    "duration_seconds",
    "environment",
)
"""Provenance fields, always present in a version 2 envelope."""


class MetadataError(ValueError):
    """Raised when metadata does not match the envelope contract."""

    pass


class ActionMetadata(TypedDict):
    """Metadata returned by an action: effective inputs and results."""

    inputs: Dict[str, Any]
    result: Dict[str, Any]


@dataclass(frozen=True)
class MetadataParts:
    """The four blocks of a version 2 metadata envelope.

    Attributes:
        provenance: Who produced the entry, when and in what environment.
        inputs: Effective parameters used by the action.
        result: Values produced by the action.
        history: Metadata inherited from earlier actions.
    """

    provenance: Dict[str, Any]
    inputs: Dict[str, Any]
    result: Dict[str, Any]
    history: Dict[str, Any]


def build_metadata(
    provider: str,
    action: str,
    inputs: Dict[str, Any],
    result: Dict[str, Any],
    *,
    provider_version: Optional[str] = None,
    workflow_version: Optional[str] = None,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    environment: Optional[Dict[str, Any]] = None,
    history: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a version 2 metadata envelope.

    Args:
        provider: Provider name that owns the action.
        action: Action name that produced the entry.
        inputs: Effective parameters used by the action.
        result: Values produced by the action.
        provider_version: Version of the provider package, if known.
        workflow_version: Version of the workflow package, if known.
        started_at: ISO 8601 UTC time at which the action started.
        finished_at: ISO 8601 UTC time at which the action finished.
        duration_seconds: Monotonic wall-clock duration of the action.
        environment: Environment information from
            :func:`causaliq_core.utils.environment`.
        history: Metadata inherited from earlier actions.

    Returns:
        Metadata envelope with ``provenance``, ``inputs``, ``result`` and
        ``history`` blocks.

    Raises:
        MetadataError: If a required name is empty or a block is not a
            mapping.
    """
    _require_name(provider, "provider")
    _require_name(action, "action")
    _require_block(inputs, "inputs")
    _require_block(result, "result")
    _require_block(history, "history", optional=True)
    return {
        "provenance": _build_provenance(
            provider=provider,
            action=action,
            provider_version=provider_version,
            workflow_version=workflow_version,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration_seconds,
            environment=environment,
        ),
        "inputs": dict(inputs),
        "result": dict(result),
        "history": dict(history or {}),
    }


def _require_name(value: str, name: str) -> None:
    """Raise when a required name is not a non-empty string.

    Args:
        value: Value to validate.
        name: Field name used in the error message.

    Raises:
        MetadataError: If the value is not a non-empty string.
    """
    if not isinstance(value, str) or not value.strip():
        raise MetadataError(f"'{name}' must be a non-empty string")


def _require_block(
    value: Optional[Dict[str, Any]],
    name: str,
    optional: bool = False,
) -> None:
    """Raise when a metadata block is not a mapping.

    Args:
        value: Block to validate.
        name: Block name used in the error message.
        optional: Whether ``None`` is an acceptable value.

    Raises:
        MetadataError: If the block is not a dictionary.
    """
    if value is None and optional:
        return
    if not isinstance(value, dict):
        raise MetadataError(f"'{name}' must be a dictionary")


def _build_provenance(
    *,
    provider: str,
    action: str,
    provider_version: Optional[str],
    workflow_version: Optional[str],
    started_at: Optional[str],
    finished_at: Optional[str],
    duration_seconds: Optional[float],
    environment: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build the provenance block, defaulting unknown values to None.

    Args:
        provider: Provider name that owns the action.
        action: Action name that produced the entry.
        provider_version: Version of the provider package, if known.
        workflow_version: Version of the workflow package, if known.
        started_at: ISO 8601 UTC time at which the action started.
        finished_at: ISO 8601 UTC time at which the action finished.
        duration_seconds: Monotonic wall-clock duration of the action.
        environment: Environment information, if available.

    Returns:
        Provenance mapping with every key present.
    """
    return {
        "provider": provider,
        "provider_version": provider_version,
        "workflow_version": workflow_version,
        "action": action,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
        "environment": dict(environment) if environment is not None else None,
    }


def is_v2_metadata(metadata: Any) -> bool:
    """Return True when metadata already uses the version 2 envelope.

    Args:
        metadata: Metadata value to inspect.

    Returns:
        True when a provenance mapping is present.
    """
    if not isinstance(metadata, dict):
        return False
    return isinstance(metadata.get("provenance"), dict)


def normalise_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Return a version 2 envelope for version 1, flat or version 2 data.

    Version 1 metadata is the legacy ``provider -> action -> fields``
    structure. The last action block is treated as the entry's producer and
    earlier blocks are moved to ``history``. A flat mapping (for example a
    third-party action result) is placed in ``result`` with unknown
    provenance.

    Args:
        metadata: Metadata stored with an entry.

    Returns:
        Version 2 metadata envelope.

    Raises:
        MetadataError: If the metadata is not a dictionary.
    """
    if not isinstance(metadata, dict):
        raise MetadataError("Metadata must be a dictionary")
    if is_v2_metadata(metadata):
        return _normalise_v2(metadata)
    if _is_legacy_metadata(metadata):
        return _normalise_legacy(metadata)
    return _normalise_flat(metadata)


def _is_legacy_metadata(metadata: Dict[str, Any]) -> bool:
    """Return True when metadata uses the legacy provider/action shape.

    Args:
        metadata: Metadata mapping to inspect.

    Returns:
        True when every non-reserved value is a non-empty mapping whose
        values are mappings.
    """
    blocks = [
        value for key, value in metadata.items() if key not in RESERVED_KEYS
    ]
    if not blocks:
        return False
    return all(_is_legacy_block(block) for block in blocks)


def _is_legacy_block(actions: Any) -> bool:
    """Return True when one provider value looks like a legacy block."""
    if not isinstance(actions, dict) or not actions:
        return False
    return all(isinstance(fields, dict) for fields in actions.values())


def _normalise_flat(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Place a flat metadata mapping in the result block.

    Args:
        metadata: Flat metadata mapping.

    Returns:
        Version 2 metadata envelope with unknown provenance.
    """
    envelope = _empty_envelope()
    envelope["result"] = dict(metadata)
    return envelope


def _normalise_v2(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Return a complete version 2 envelope with every block present.

    Args:
        metadata: Version 2 metadata, potentially missing optional blocks.

    Returns:
        Metadata with all four blocks and every provenance key present.
    """
    provenance = dict(metadata.get("provenance") or {})
    for key in PROVENANCE_KEYS:
        provenance.setdefault(key, None)
    return {
        "provenance": provenance,
        "inputs": dict(metadata.get("inputs") or {}),
        "result": dict(metadata.get("result") or {}),
        "history": dict(metadata.get("history") or {}),
    }


def _normalise_legacy(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Convert the legacy provider -> action -> fields shape to version 2.

    Args:
        metadata: Legacy metadata mapping.

    Returns:
        Version 2 metadata envelope.
    """
    blocks = _legacy_blocks(metadata)
    provider, action, fields = blocks[-1]
    history = {
        f"{block_provider}.{block_action}": {
            "inputs": {},
            "result": dict(block_fields),
        }
        for block_provider, block_action, block_fields in blocks[:-1]
    }
    return build_metadata(
        provider=provider,
        action=action,
        inputs={},
        result=dict(fields),
        history=history,
    )


def _legacy_blocks(
    metadata: Dict[str, Any],
) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Return the legacy provider/action/field blocks in insertion order.

    Args:
        metadata: Legacy metadata mapping.

    Returns:
        List of (provider, action, fields) tuples.
    """
    blocks: List[Tuple[str, str, Dict[str, Any]]] = []
    for provider, actions in metadata.items():
        if provider in RESERVED_KEYS:
            continue
        for action, fields in actions.items():
            blocks.append((str(provider), str(action), fields))
    return blocks


def _empty_envelope() -> Dict[str, Any]:
    """Return an empty version 2 envelope.

    Returns:
        Metadata envelope with empty blocks and unknown provenance.
    """
    provenance = {key: None for key in PROVENANCE_KEYS}
    return {
        "provenance": provenance,
        "inputs": {},
        "result": {},
        "history": {},
    }


def split_metadata(metadata: Dict[str, Any]) -> MetadataParts:
    """Return the four blocks of an envelope, normalising legacy data.

    Args:
        metadata: Metadata stored with an entry.

    Returns:
        Parsed metadata blocks.

    Raises:
        MetadataError: If the metadata cannot be interpreted.
    """
    envelope = normalise_metadata(metadata)
    return MetadataParts(
        provenance=envelope["provenance"],
        inputs=envelope["inputs"],
        result=envelope["result"],
        history=envelope["history"],
    )
