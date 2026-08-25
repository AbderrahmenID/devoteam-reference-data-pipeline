from __future__ import annotations

from typing import Any

from .phase2_utils import normalize_text


def normalized_set(values: list[Any]) -> set[str]:
    return {normalize_text(value) for value in values if normalize_text(value)}


def is_blocked_header(header: Any, config: dict) -> bool:
    blocked = normalized_set(config["exclusions"]["never_ingest_headers"])
    return normalize_text(header) in blocked


def may_follow_links(header: Any, config: dict) -> bool:
    if is_blocked_header(header, config):
        return False
    denied = normalized_set(config["exclusions"]["never_follow_link_headers"])
    return normalize_text(header) not in denied


def classify_path(path: str, config: dict) -> tuple[bool, str]:
    normalized_path = f" {normalize_text(path)} "
    for term in config["exclusions"]["excluded_path_terms"]:
        normalized_term = normalize_text(term)
        if normalized_term and f" {normalized_term} " in normalized_path:
            return True, f"excluded_path_term:{normalized_term}"
    return False, ""


def allowed_mime(mime_type: str, config: dict) -> bool:
    return mime_type in set(config["evidence"]["allowed_mime_types"])
