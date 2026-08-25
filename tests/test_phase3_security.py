from devoteam_reference_ai.phase3_security import redact_text


CONFIG = {"security": {
    "redact_email": True,
    "redact_phone_like_numbers": True,
    "redact_iban": True,
    "redact_monetary_amounts": True,
}}


def test_redaction_masks_sensitive_patterns_without_logging_values():
    text = "Contact test@example.com, +216 98 746 814, montant 12 000 TND."
    redacted, counts = redact_text(text, CONFIG)
    assert "test@example.com" not in redacted
    assert "+216 98 746 814" not in redacted
    assert "12 000 TND" not in redacted
    assert counts["EMAIL"] == 1
    assert counts["MONETARY_AMOUNT"] == 1
