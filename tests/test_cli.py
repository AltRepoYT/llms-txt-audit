import contextlib
import io
import json
import os
import shutil
import unittest
from pathlib import Path

from llms_txt_audit.cli import main

VALID = """# ExampleDev

> ExampleDev is a toolkit.

## Core
- [Overview](https://example.com/index.html.md): Project overview

## Optional
- [Sitemap](https://example.com/sitemap.xml): URL list
"""


class CliTests(unittest.TestCase):
    def setUp(self):
        base = Path(os.environ.get("LLMS_TXT_AUDIT_TEST_TMP", "C:/tmp"))
        self.tmp_root = base / "llms-txt-audit-tests"
        shutil.rmtree(self.tmp_root, ignore_errors=True)
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def make_file(self, name="llms.txt"):
        target = self.tmp_root / name
        target.write_text(VALID, encoding="utf-8")
        return target

    def test_cli_returns_zero_for_valid_file(self):
        target = self.make_file()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main([str(target)])

        self.assertEqual(code, 0)
        self.assertIn("Score: 100/100", stdout.getvalue())

    def test_cli_json_output(self):
        target = self.make_file()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main([str(target), "--json"])

        self.assertEqual(code, 0)
        data = json.loads(stdout.getvalue())
        self.assertTrue(data["ok"])
        self.assertEqual(data["link_count"], 2)

    def test_cli_missing_file_returns_two(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main([str(self.tmp_root / "does-not-exist.txt")])

        self.assertEqual(code, 2)
        self.assertIn("File not found", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
