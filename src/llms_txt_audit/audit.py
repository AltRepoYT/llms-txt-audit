from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from .models import AuditResult, MutableAudit, ParsedLlmsTxt, Severity
from .parser import parse_llms_txt

PRIVATE_PATH_MARKERS = (
    "/admin",
    "/account",
    "/accounts",
    "/cart",
    "/checkout",
    "/login",
    "/logout",
    "/signin",
    "/signup",
    "/wp-admin",
)
RECOMMENDED_SECTIONS = {"core", "docs", "api", "examples", "policies", "optional"}


@dataclass(frozen=True)
class AuditOptions:
    strict: bool = False
    require_optional: bool = False
    allow_relative_links: bool = True


def audit_text(text: str, *, source: str = "<text>", options: AuditOptions | None = None) -> AuditResult:
    opts = options or AuditOptions()
    parsed = parse_llms_txt(text, source=source)
    audit = MutableAudit(source=source)

    _check_structure(parsed, audit, opts)
    _check_links(parsed, audit, opts)

    return AuditResult(
        source=source,
        score=_score(audit.findings),
        findings=tuple(audit.findings),
        title=parsed.title,
        summary=parsed.summary,
        section_count=len(parsed.sections),
        link_count=len(parsed.links),
        optional_section=any(section.title.lower() == "optional" for section in parsed.sections),
    )


def _check_structure(parsed: ParsedLlmsTxt, audit: MutableAudit, opts: AuditOptions) -> None:
    if parsed.title:
        audit.add("title-found", Severity.PASS, "H1 title found.", line=parsed.title_line)
    else:
        audit.add("title-missing", Severity.ERROR, "Missing H1 title.", hint="Start with '# Project Name'.")

    if parsed.h1_count > 1:
        audit.add("multiple-h1", Severity.WARNING, "Multiple H1 titles found.", hint="Use one H1, then H2 sections for resource groups.")

    if parsed.summary:
        audit.add("summary-found", Severity.PASS, "Blockquote summary found.", line=parsed.summary_line)
    else:
        severity = Severity.ERROR if opts.strict else Severity.WARNING
        audit.add("summary-missing", severity, "Missing blockquote summary.", hint="Add a short line like '> What this site/project is for'.")

    if parsed.sections:
        audit.add("sections-found", Severity.PASS, f"{len(parsed.sections)} H2 section(s) found.")
    else:
        audit.add("sections-missing", Severity.ERROR, "No H2 resource sections found.", hint="Add sections such as '## Core', '## Docs', or '## Optional'.")

    if parsed.links:
        audit.add("links-found", Severity.PASS, f"{len(parsed.links)} Markdown resource link(s) found.")
    else:
        audit.add("links-missing", Severity.ERROR, "No Markdown list links found.", hint="Use '- [Title](https://example.com/page.md): Why it matters'.")

    optional_found = any(section.title.lower() == "optional" for section in parsed.sections)
    if optional_found:
        audit.add("optional-found", Severity.PASS, "Optional section found.")
    elif opts.require_optional or opts.strict:
        audit.add("optional-missing", Severity.WARNING, "Optional section missing.", hint="Use '## Optional' for secondary links that can be skipped for shorter context.")
    else:
        audit.add("optional-suggested", Severity.INFO, "Consider adding an Optional section for lower-priority resources.")

    for line in parsed.robots_directive_lines:
        audit.add("robots-directive", Severity.WARNING, "robots.txt-style directive found in llms.txt.", line=line, hint="Keep crawl permissions in robots.txt, not llms.txt.")

    section_names = {section.title.lower() for section in parsed.sections}
    if section_names and not section_names.intersection(RECOMMENDED_SECTIONS):
        audit.add("section-names", Severity.INFO, "Section names are custom.", hint="Common names include Core, Docs, API, Examples, Policies, and Optional.")


def _check_links(parsed: ParsedLlmsTxt, audit: MutableAudit, opts: AuditOptions) -> None:
    seen_urls: set[str] = set()
    for link in parsed.links:
        parsed_url = urlparse(link.url)
        if not parsed_url.scheme and not opts.allow_relative_links:
            audit.add("relative-link", Severity.WARNING, "Relative link found.", line=link.line, hint="Use absolute URLs if this file will be consumed outside your site context.")
        if parsed_url.scheme and parsed_url.scheme not in {"http", "https"}:
            audit.add("unsupported-scheme", Severity.WARNING, f"Unsupported URL scheme '{parsed_url.scheme}'.", line=link.line)

        path = parsed_url.path.lower() if parsed_url.path else link.url.lower()
        if any(marker in path for marker in PRIVATE_PATH_MARKERS):
            audit.add("private-looking-url", Severity.WARNING, f"Private-looking URL detected: {link.url}", line=link.line)

        normalized_url = link.url.rstrip("/")
        if normalized_url in seen_urls:
            audit.add("duplicate-url", Severity.INFO, f"Duplicate URL listed: {link.url}", line=link.line)
        seen_urls.add(normalized_url)

        if not link.note:
            audit.add("missing-link-note", Severity.INFO, f"Link has no description: {link.title}", line=link.line, hint="Add ': why this resource matters' after the link.")


def _score(findings: list) -> int:
    score = 100
    for finding in findings:
        if finding.severity is Severity.ERROR:
            score -= 25
        elif finding.severity is Severity.WARNING:
            score -= 10
        elif finding.severity is Severity.INFO:
            score -= 2
    return max(0, min(100, score))
