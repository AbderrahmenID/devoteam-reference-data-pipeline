from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from devoteam_reference_ai.security import (  # noqa: E402
    ConfidentialityLevel,
    can_use_external_llm,
    redact_sensitive_mapping,
)


class SecurityTests(unittest.TestCase):
    def test_unapproved_provider_is_always_blocked(self) -> None:
        for level in ConfidentialityLevel:
            self.assertFalse(can_use_external_llm(level, provider_approved=False))

    def test_public_requires_approved_provider(self) -> None:
        self.assertTrue(
            can_use_external_llm(ConfidentialityLevel.PUBLIC, provider_approved=True)
        )

    def test_internal_requires_redaction_and_approval(self) -> None:
        self.assertFalse(
            can_use_external_llm(ConfidentialityLevel.INTERNAL, provider_approved=True)
        )
        self.assertTrue(
            can_use_external_llm(
                ConfidentialityLevel.INTERNAL,
                provider_approved=True,
                content_redacted=True,
            )
        )

    def test_restricted_and_confidential_are_never_external(self) -> None:
        for level in (
            ConfidentialityLevel.RESTRICTED,
            ConfidentialityLevel.CONFIDENTIAL,
        ):
            self.assertFalse(
                can_use_external_llm(
                    level,
                    provider_approved=True,
                    content_redacted=True,
                )
            )

    def test_sensitive_values_are_redacted(self) -> None:
        payload = {"client": "Example", "token": "secret", "nested": {"api_key": "x"}}
        result = redact_sensitive_mapping(payload, {"token", "api_key"})
        self.assertEqual(result["client"], "Example")
        self.assertEqual(result["token"], "[REDACTED]")
        self.assertEqual(result["nested"]["api_key"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
