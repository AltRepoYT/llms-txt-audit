from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    PASS = "pass"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    message: str
    line: int | None = None
    hint: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
        }
        if self.line is not None:
            data["line"] = self.line
        if self.hint:
            data["hint"] = self.hint
        return data


@dataclass(frozen=True)
class LinkRef:
    title: str
    url: str
    note: str
    line: int
    section: str


@dataclass(frozen=True)
class Section:
    title: str
    line: int
    links: tuple[LinkRef, ...] = ()


@dataclass(frozen=True)
class ParsedLlmsTxt:
    source: str
    title: str | None
    title_line: int | None
    summary: str | None
    summary_line: int | None
    sections: tuple[Section, ...]
    links: tuple[LinkRef, ...]
    h1_count: int
    robots_directive_lines: tuple[int, ...] = ()


@dataclass(frozen=True)
class AuditResult:
    source: str
    score: int
    findings: tuple[Finding, ...]
    title: str | None
    summary: str | None
    section_count: int
    link_count: int
    optional_section: bool

    @property
    def ok(self) -> bool:
        return not any(item.severity is Severity.ERROR for item in self.findings)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "ok": self.ok,
            "score": self.score,
            "title": self.title,
            "summary": self.summary,
            "section_count": self.section_count,
            "link_count": self.link_count,
            "optional_section": self.optional_section,
            "findings": [item.as_dict() for item in self.findings],
        }


@dataclass
class MutableAudit:
    source: str
    findings: list[Finding] = field(default_factory=list)

    def add(self, code: str, severity: Severity, message: str, *, line: int | None = None, hint: str | None = None) -> None:
        self.findings.append(Finding(code=code, severity=severity, message=message, line=line, hint=hint))
