from __future__ import annotations

import re

from .models import LinkRef, ParsedLlmsTxt, Section

H1_RE = re.compile(r"^#\s+(.+?)\s*$")
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
QUOTE_RE = re.compile(r"^>\s+(.+?)\s*$")
LINK_RE = re.compile(r"^-\s+\[([^\]]+)\]\(([^)\s]+)\)\s*:?(.*)$")
ROBOTS_DIRECTIVE_RE = re.compile(r"^\s*(User-agent|Disallow|Allow|Crawl-delay|Sitemap)\s*:", re.IGNORECASE)


def parse_llms_txt(text: str, *, source: str = "<text>") -> ParsedLlmsTxt:
    title: str | None = None
    title_line: int | None = None
    summary: str | None = None
    summary_line: int | None = None
    h1_count = 0
    sections: list[Section] = []
    section_links: dict[int, list[LinkRef]] = {}
    links: list[LinkRef] = []
    robots_lines: list[int] = []
    current_section_index: int | None = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if ROBOTS_DIRECTIVE_RE.match(line):
            robots_lines.append(line_number)
        if match := H1_RE.match(line):
            h1_count += 1
            if title is None:
                title = match.group(1).strip()
                title_line = line_number
            current_section_index = None
            continue
        if summary is None and (match := QUOTE_RE.match(line)):
            summary = match.group(1).strip()
            summary_line = line_number
            continue
        if match := H2_RE.match(line):
            sections.append(Section(title=match.group(1).strip(), line=line_number, links=()))
            current_section_index = len(sections) - 1
            section_links[current_section_index] = []
            continue
        if match := LINK_RE.match(line):
            section_name = sections[current_section_index].title if current_section_index is not None else ""
            link = LinkRef(
                title=match.group(1).strip(),
                url=match.group(2).strip(),
                note=match.group(3).strip(),
                line=line_number,
                section=section_name,
            )
            links.append(link)
            if current_section_index is not None:
                section_links.setdefault(current_section_index, []).append(link)

    finalized_sections = tuple(
        Section(title=section.title, line=section.line, links=tuple(section_links.get(index, [])))
        for index, section in enumerate(sections)
    )
    return ParsedLlmsTxt(
        source=source,
        title=title,
        title_line=title_line,
        summary=summary,
        summary_line=summary_line,
        sections=finalized_sections,
        links=tuple(links),
        h1_count=h1_count,
        robots_directive_lines=tuple(robots_lines),
    )
