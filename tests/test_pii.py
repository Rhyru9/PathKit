"""
tests/test_pii.py — Regression tests for PII detection + redaction.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.audit_pii import safe_sample
from scripts.pii_rules import decode, detect_all, redact_token


class TestDecode(unittest.TestCase):
    def test_utf8_multibyte(self):
        # %E2%9C%A8 is U+2728 (sparkles) — must not become mojibake
        self.assertEqual(decode("%E2%9C%A8-apresiasi"), "\u2728-apresiasi")

    def test_ascii_passthrough(self):
        self.assertEqual(decode("panduan-belajar-online"), "panduan-belajar-online")


class TestCredential(unittest.TestCase):
    def test_credential_detected_before_email(self):
        out, label = redact_token("login:user@example.com:secret123")
        self.assertEqual(label, "credential")
        self.assertEqual(out, "")

    def test_credential_with_slash_path(self):
        out, label = redact_token("https:/sso.x.go.id/sys/login:a@b.co:pass")
        self.assertEqual(label, "credential")
        self.assertEqual(out, "")

    def test_audit_samples_never_expose_credentials(self):
        self.assertEqual(
            safe_sample("login:user@example.com:secret123", "credential"),
            "[REDACTED_CREDENTIAL]",
        )

    def test_audit_samples_mask_encoded_names(self):
        self.assertEqual(
            safe_sample("/cgi/exportview/creators/Example=3AName=3A=3A", "encoded_name"),
            "[REDACTED_ENCODED_NAME]",
        )


class TestEmail(unittest.TestCase):
    def test_standalone_email_redacted(self):
        out, label = redact_token("contact@example.com")
        self.assertEqual(label, "email")
        self.assertEqual(out, "[EMAIL]")

    def test_embedded_email_redacted_preserves_structure(self):
        out, label = redact_token("/user/contact@example.com/profile")
        self.assertEqual(label, "email")
        self.assertEqual(out, "/user/[EMAIL]/profile")


class TestEmbeddedIDs(unittest.TestCase):
    def test_embedded_id_code_in_endpoint(self):
        out, label = redact_token("/referensi/data/P1234567")
        self.assertEqual(label, "id_code")
        self.assertEqual(out, "/referensi/data/[ID_CODE]")

    def test_embedded_nip_name_in_endpoint(self):
        out, label = redact_token("/profil/10099994825369-Example-Person")
        self.assertEqual(label, "nip_name")
        self.assertEqual(out, "/profil/[NIP_NAME]")


class TestNoFalsePositive(unittest.TestCase):
    def test_space_hex_not_redacted(self):
        # =20 is a space, NOT an author delimiter
        self.assertNotIn("encoded_name", detect_all("page=20-title"))

    def test_org_code_underscore_not_redacted(self):
        # =5F is underscore (org code), NOT an author delimiter
        _, label = redact_token("ditjen=5Fbudaya=5Fsesditjen")
        self.assertIsNone(label)

    def test_query_parameters_not_redacted(self):
        _, label = redact_token("tabs.php?npsn=69889103")
        self.assertIsNone(label)

    def test_slug_not_redacted(self):
        _, label = redact_token("panduan-belajar-online")
        self.assertIsNone(label)

    def test_bare_equals_hex_not_redacted(self):
        # foo=3Abar is NOT in a /creators/ route -> not an author name
        _, label = redact_token("foo=3Abar")
        self.assertIsNone(label)

    def test_subjects_route_not_redacted(self):
        # /subjects/ uses =3A for topical terms, NOT person names
        _, label = redact_token("/cgi/exportview/subjects/Pendidikan=3AIndonesia")
        self.assertIsNone(label)


class TestEncodedAuthor(unittest.TestCase):
    def test_author_route_redacted(self):
        out, label = redact_token("/cgi/exportview/creators/DM=3AExample_Name=3A=3A")
        self.assertEqual(label, "encoded_name")
        self.assertNotIn("Example_Name", out)
        self.assertIn("creators", out)

    def test_author_percent_encoded_name(self):
        # percent-encoded + =3A author name
        out, label = redact_token("/exportview/creators/Example=3AM=3A=3A")
        self.assertEqual(label, "encoded_name")
        self.assertNotIn("Example", out)


if __name__ == "__main__":
    unittest.main()
