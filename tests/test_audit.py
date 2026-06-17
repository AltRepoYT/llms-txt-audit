import unittest

from llms_txt_audit.audit import AuditOptions, audit_text
from llms_txt_audit.models import Severity

VALID = """# ExampleDev

> ExampleDev is a toolkit.

## Core
- [Overview](https://example.com/index.html.md): Project overview

## Optional
- [Sitemap](https://example.com/sitemap.xml): URL list
"""


def codes(result):
    return {finding.code for finding in result.findings}


def severities(result):
    return {finding.severity for finding in result.findings}


class AuditTests(unittest.TestCase):
    def test_valid_document_passes_core_checks(self):
        result = audit_text(VALID)

        self.assertTrue(result.ok)
        self.assertEqual(result.score, 100)
        self.assertEqual(result.section_count, 2)
        self.assertEqual(result.link_count, 2)
        self.assertTrue(result.optional_section)
        self.assertIn("title-found", codes(result))

    def test_missing_title_is_error(self):
        result = audit_text("> Summary\n\n## Core\n- [Docs](https://example.com/docs): Docs\n")

        self.assertFalse(result.ok)
        self.assertIn("title-missing", codes(result))
        self.assertIn(Severity.ERROR, severities(result))

    def test_strict_missing_summary_is_error(self):
        result = audit_text("# Example\n\n## Core\n- [Docs](https://example.com/docs): Docs\n", options=AuditOptions(strict=True))

        self.assertFalse(result.ok)
        self.assertIn("summary-missing", codes(result))

    def test_private_urls_and_robots_directives_are_warned(self):
        result = audit_text("""# Example

> Summary

User-agent: *

## Core
- [Admin](https://example.com/admin): Admin area
""")

        self.assertTrue(result.ok)
        self.assertIn("robots-directive", codes(result))
        self.assertIn("private-looking-url", codes(result))

    def test_relative_links_warn_when_disabled(self):
        result = audit_text(VALID.replace("https://example.com/index.html.md", "/index.html.md"), options=AuditOptions(allow_relative_links=False))

        self.assertIn("relative-link", codes(result))


if __name__ == "__main__":
    unittest.main()
