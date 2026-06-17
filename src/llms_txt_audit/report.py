from __future__ import annotations

import json
import sys
from typing import TextIO

from .models import AuditResult, Severity

ICONS = {
    Severity.PASS: "PASS",
    Severity.INFO: "INFO",
    Severity.WARNING: "WARN",
    Severity.ERROR: "FAIL",
}


def write_text_report(result: AuditResult, *, stream: TextIO | None = None) -> None:
    out = stream or sys.stdout
    print(f"llms.txt audit: {result.source}", file=out)
    print("", file=out)
    for finding in result.findings:
        location = f" line {finding.line}" if finding.line is not None else ""
        print(f"{ICONS[finding.severity]:<5} {finding.message}{location}", file=out)
        if finding.hint:
            print(f"      Hint: {finding.hint}", file=out)
    print("", file=out)
    print(f"Score: {result.score}/100", file=out)
    print(f"Sections: {result.section_count}  Links: {result.link_count}  Optional: {'yes' if result.optional_section else 'no'}", file=out)


def to_json(result: AuditResult) -> str:
    return json.dumps(result.as_dict(), indent=2, sort_keys=True)
