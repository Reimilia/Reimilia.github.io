#!/usr/bin/env python3
"""Generate publication and news HTML from small metadata files.

Inputs:
  content/publications.bib  BibTeX entries. Supported optional fields:
                             selected, summary, url, pdf, code, project, doi, eprint.
  content/news.md           Markdown list entries: - YYYY[-MM[-DD]] | Text

Outputs are written into marked regions of index.html and publications/index.html.
The parser is intentionally small and dependency-free for GitHub Pages workflows.
"""
from __future__ import annotations

import html
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLICATIONS_BIB = ROOT / "content" / "publications.bib"
NEWS_MD = ROOT / "content" / "news.md"
INDEX_HTML = ROOT / "index.html"
PUBLICATIONS_HTML = ROOT / "publications" / "index.html"

MONTHS = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}


def clean_value(value: str) -> str:
    value = value.strip().rstrip(",").strip()
    if len(value) >= 2 and value[0] in "{\"" and value[-1] in "}\"":
        value = value[1:-1]
    return re.sub(r"\s+", " ", value).strip()


def parse_bibtex(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    i = 0
    while True:
        start = text.find("@", i)
        if start == -1:
            break
        brace = text.find("{", start)
        if brace == -1:
            break
        entry_type = text[start + 1:brace].strip().lower()
        depth = 0
        end = brace
        for pos in range(brace, len(text)):
            if text[pos] == "{":
                depth += 1
            elif text[pos] == "}":
                depth -= 1
                if depth == 0:
                    end = pos
                    break
        body = text[brace + 1:end]
        key, _, fields_text = body.partition(",")
        entry: dict[str, str] = {"type": entry_type, "key": key.strip()}
        field_pattern = re.compile(r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|[^,]+)\s*,?", re.S)
        for match in field_pattern.finditer(fields_text):
            entry[match.group(1).lower()] = clean_value(match.group(2))
        entry["_order"] = str(len(entries))
        entries.append(entry)
        i = end + 1
    return entries


def parse_news(text: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = re.match(r"^\s*-\s*(\d{4}(?:-\d{2})?(?:-\d{2})?)\s*\|\s*(.+?)\s*$", line)
        if match:
            items.append((match.group(1), match.group(2)))
    return sorted(items, key=lambda item: item[0], reverse=True)


def display_date(value: str) -> str:
    parts = value.split("-")
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{MONTHS.get(parts[1], parts[1])} {parts[0]}"
    return f"{MONTHS.get(parts[1], parts[1])} {int(parts[2])}, {parts[0]}"


def authors(value: str) -> str:
    return ", ".join(part.strip() for part in re.split(r"\s+and\s+", value) if part.strip())


def venue(entry: dict[str, str]) -> str:
    for field in ("journal", "booktitle", "publisher", "institution", "school"):
        if entry.get(field):
            return entry[field]
    eprint = entry.get("eprint")
    archive = entry.get("archiveprefix", "arXiv")
    return f"{archive}:{eprint}" if eprint else ""


def is_selected(entry: dict[str, str]) -> bool:
    return entry.get("selected", "").strip().lower() in {"1", "yes", "true"}


def link_html(entry: dict[str, str]) -> str:
    links: list[tuple[str, str]] = []
    if entry.get("url"):
        links.append(("Link", entry["url"]))
    if entry.get("pdf"):
        links.append(("PDF", entry["pdf"]))
    if entry.get("code"):
        links.append(("Code", entry["code"]))
    if entry.get("project"):
        links.append(("Project", entry["project"]))
    if entry.get("doi"):
        links.append(("DOI", f"https://doi.org/{entry['doi']}"))
    if entry.get("eprint") and entry.get("archiveprefix", "arXiv").lower() == "arxiv":
        links.append(("arXiv", f"https://arxiv.org/abs/{entry['eprint']}"))
    if not links:
        return ""
    anchors = [f'<a href="{html.escape(url, quote=True)}">{html.escape(label)}</a>' for label, url in links]
    return f'\n          <p class="links">{" · ".join(anchors)}</p>'


def publication_article(entry: dict[str, str], include_summary: bool) -> str:
    title = html.escape(entry.get("title", "Untitled"))
    meta_parts = [authors(entry.get("author", "")), venue(entry), entry.get("year", "")]
    meta = " · ".join(html.escape(part) for part in meta_parts if part)
    klass = "item publication-entry" if include_summary else "item"
    summary = ""
    if include_summary and entry.get("summary"):
        summary = f"\n          <p>{html.escape(entry['summary'])}</p>"
    return (
        f'        <article class="{klass}">\n'
        f"          <h3>{title}</h3>\n"
        f'          <p class="meta">{meta}</p>'
        f"{summary}{link_html(entry)}\n"
        f"        </article>"
    )


def replace_between(text: str, marker: str, replacement: str) -> str:
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    pattern = re.compile(rf"{re.escape(start)}.*?{re.escape(end)}", re.S)
    block = f"{start}\n{replacement}\n        {end}"
    new, count = pattern.subn(block, text)
    if count != 1:
        raise RuntimeError(f"Expected exactly one {marker} block")
    return new


def build_news_html(items: list[tuple[str, str]]) -> str:
    lines = ['        <ul class="news-list">']
    for date, text in items:
        lines.append(f'          <li><time datetime="{html.escape(date)}">{display_date(date)}</time> {html.escape(text)}</li>')
    lines.append("        </ul>")
    return "\n".join(lines)


def year_sort_value(entry: dict[str, str]) -> int:
    try:
        return int(entry.get("year", "0") or "0")
    except ValueError:
        return 0


def build_selected_publications(entries: list[dict[str, str]]) -> str:
    selected = [entry for entry in entries if is_selected(entry)] or entries[:3]
    selected = sorted(selected, key=lambda entry: (-year_sort_value(entry), int(entry.get("_order", "0"))))[:3]
    return "\n".join(publication_article(entry, include_summary=False) for entry in selected)


def build_publications_page(entries: list[dict[str, str]]) -> str:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for entry in sorted(entries, key=lambda entry: (-year_sort_value(entry), int(entry.get("_order", "0")))):
        groups[entry.get("year", "Year unknown")].append(entry)
    sections: list[str] = []
    for year in sorted(groups, key=lambda value: int(value) if value.isdigit() else 0, reverse=True):
        articles = "\n".join(publication_article(entry, include_summary=True) for entry in groups[year])
        sections.append(f'      <section class="section">\n        <h2>{html.escape(year)}</h2>\n{articles}\n      </section>')
    return "\n\n".join(sections)


def main() -> None:
    entries = parse_bibtex(PUBLICATIONS_BIB.read_text())
    news_items = parse_news(NEWS_MD.read_text())

    index = INDEX_HTML.read_text()
    index = replace_between(index, "NEWS", build_news_html(news_items))
    index = replace_between(index, "SELECTED_PUBLICATIONS", build_selected_publications(entries))
    INDEX_HTML.write_text(index)

    publications = PUBLICATIONS_HTML.read_text()
    publications = replace_between(publications, "PUBLICATIONS", build_publications_page(entries))
    PUBLICATIONS_HTML.write_text(publications)

    print(f"Generated {len(news_items)} news items and {len(entries)} publication entries.")


if __name__ == "__main__":
    main()
