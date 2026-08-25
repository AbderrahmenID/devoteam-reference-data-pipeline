"""D1 confidentiality decisions and safe logging helpers."""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Mapping


class ConfidentialityLevel(IntEnum):
    PUBLIC = 0
    INTERNAL = 1
    RESTRICTED = 2
    CONFIDENTIAL = 3


def can_use_external_llm(
    level: ConfidentialityLevel,
    *,
    provider_approved: bool,
    content_redacted: bool = False,
) -> bool:
    """Apply the approved B1/D1 external-LLM boundary."""

    if not provider_approved:
        return False
    if level is ConfidentialityLevel.PUBLIC:
        return True
    if level is ConfidentialityLevel.INTERNAL:
        return content_redacted
    return False


def redact_sensitive_mapping(
    payload: Mapping[str, Any],
    sensitive_keys: set[str],
) -> dict[str, Any]:
    normalized_sensitive = {key.casefold() for key in sensitive_keys}
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        if key.casefold() in normalized_sensitive:
            redacted[key] = "[REDACTED]"
        elif isinstance(value, Mapping):
            redacted[key] = redact_sensitive_mapping(value, sensitive_keys)
        else:
            redacted[key] = value
    return redacted
