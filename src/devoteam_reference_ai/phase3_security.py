from __future__ import annotations

import re


EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
IBAN_RE = re.compile(r"(?i)\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+\d{1,3}[ .-]?)?(?:\d[ .-]?){8,14}(?!\w)")
MONEY_RE = re.compile(
    r"(?i)(?:\b\d[\d\s.,]*\s?(?:TND|DT|EUR|USD|FCFA|F\s?CFA)\b|"
    r"(?:€|\$)\s?\d[\d\s.,]*)"
)


def redact_text(text: str, config: dict) -> tuple[str, dict[str, int]]:
    security = config["security"]
    redacted = text
    counts: dict[str, int] = {}
    rules = [
        ("EMAIL", EMAIL_RE, security.get("redact_email", True)),
        ("IBAN", IBAN_RE, security.get("redact_iban", True)),
        ("MONETARY_AMOUNT", MONEY_RE, security.get("redact_monetary_amounts", True)),
        ("PHONE_LIKE", PHONE_RE, security.get("redact_phone_like_numbers", True)),
    ]
    for label, pattern, enabled in rules:
        if not enabled:
            continue
        redacted, count = pattern.subn(f"[{label}]", redacted)
        if count:
            counts[label] = count
    return redacted, counts
