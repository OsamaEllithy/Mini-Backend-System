"""
Metadata deep-merge utility for JSONB fields.

During bulk import, existing asset metadata must be intelligently merged
with incoming metadata: new keys are added, existing scalars are overwritten,
nested dicts are recursively merged, and lists are union-merged.
"""

from typing import Any


def deep_merge_metadata(
    existing: dict[str, Any] | None,
    incoming: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Recursively merge incoming metadata into existing metadata.

    Rules:
    - If either is None/empty, return the other (or empty dict).
    - New keys from incoming are added.
    - Existing scalar values are overwritten by incoming.
    - Nested dicts are recursively merged.
    - Lists are union-merged (preserving order, deduplicating).

    Args:
        existing: Current metadata dict from the database.
        incoming: New metadata dict from the import payload.

    Returns:
        Merged metadata dict.
    """
    if not existing:
        return incoming or {}
    if not incoming:
        return existing or {}

    merged = existing.copy()

    for key, incoming_value in incoming.items():
        if key not in merged:
            # New key — simply add it
            merged[key] = incoming_value
        else:
            existing_value = merged[key]

            if isinstance(existing_value, dict) and isinstance(incoming_value, dict):
                # Both are dicts — recurse
                merged[key] = deep_merge_metadata(existing_value, incoming_value)
            elif isinstance(existing_value, list) and isinstance(incoming_value, list):
                # Both are lists — union merge preserving order
                merged[key] = _union_merge_lists(existing_value, incoming_value)
            else:
                # Scalar or type mismatch — incoming overwrites
                merged[key] = incoming_value

    return merged


def _union_merge_lists(existing: list, incoming: list) -> list:
    """
    Union-merge two lists, preserving order and deduplicating
    serializable items. Non-hashable items (dicts, lists) are
    compared by equality.
    """
    result = list(existing)
    seen_hashable = set()

    # Track existing hashable items
    for item in existing:
        try:
            seen_hashable.add(item)
        except TypeError:
            pass  # Non-hashable (dict/list) — handled by equality check

    for item in incoming:
        try:
            if item not in seen_hashable:
                result.append(item)
                seen_hashable.add(item)
        except TypeError:
            # Non-hashable — check by equality
            if item not in result:
                result.append(item)

    return result
