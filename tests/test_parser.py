import unittest

from llms_txt_audit.parser import parse_llms_txt

VALID = """# ExampleDev

> ExampleDev is a toolkit.

## Core
- [Overview](https://example.com/index.html.md): Project overview

## Optional
- [Sitemap](https://example.com/sitemap.xml): URL list
"""


class ParserTests(unittest.TestCase):
    def test_parser_extracts_title_summary_sections_and_links(self):
        parsed = parse_llms_txt(VALID)

        self.assertEqual(parsed.title, "ExampleDev")
        self.assertEqual(parsed.summary, "ExampleDev is a toolkit.")
        self.assertEqual([section.title for section in parsed.sections], ["Core", "Optional"])
        self.assertEqual(len(parsed.links), 2)
        self.assertEqual(parsed.links[0].title, "Overview")
        self.assertEqual(parsed.links[0].section, "Core")

    def test_parser_detects_robots_directives(self):
        parsed = parse_llms_txt("# X\n\nUser-agent: *\nDisallow: /admin\n")

        self.assertEqual(parsed.robots_directive_lines, (3, 4))


if __name__ == "__main__":
    unittest.main()
