from __future__ import annotations

import argparse
import sys

from .audit import AuditOptions, audit_text
from .io import InputError, read_target
from .models import Severity
from .report import to_json, write_text_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llms-txt-audit",
        description="Validate an llms.txt file locally, over HTTP, or in CI.",
    )
    parser.add_argument("target", help="Path, directory, /llms.txt URL, or site URL with --discover.")
    parser.add_argument("--discover", action="store_true", help="Treat a site URL as its root and read /llms.txt.")
    parser.add_argument("--strict", action="store_true", help="Promote recommended checks to stricter warnings/errors.")
    parser.add_argument("--require-optional", action="store_true", help="Warn when ## Optional is missing.")
    parser.add_argument("--no-relative-links", action="store_true", help="Warn when links are relative instead of absolute.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--fail-on-warning", action="store_true", help="Exit non-zero when warnings are present.")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout in seconds. Default: 10.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source, text = read_target(args.target, timeout=args.timeout, discover=args.discover)
    except InputError as exc:
        print(f"llms-txt-audit: {exc}", file=sys.stderr)
        return 2

    result = audit_text(
        text,
        source=source,
        options=AuditOptions(
            strict=args.strict,
            require_optional=args.require_optional,
            allow_relative_links=not args.no_relative_links,
        ),
    )

    if args.json:
        print(to_json(result))
    else:
        write_text_report(result)

    has_warning = any(item.severity is Severity.WARNING for item in result.findings)
    if not result.ok:
        return 1
    if args.fail_on_warning and has_warning:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
