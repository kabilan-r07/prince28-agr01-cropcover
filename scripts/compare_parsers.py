"""Compare extraction quality for selected corpus files and append a table to NOTES.md."""

import argparse
from html.parser import HTMLParser
from pathlib import Path

from cropcover.ingest.parse import ParseError, parse_file

ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "NOTES.md"


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "nav", "footer", "header"}:
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "nav", "footer", "header"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def extract(path: Path, parser: str) -> tuple[int, int, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        doc = parse_file(path, pdf_parser=parser)
    elif suffix in {".html", ".htm"} and parser == "plain":
        visible = VisibleText()
        visible.feed(path.read_text(encoding="utf-8", errors="replace"))
        text = "\n".join(visible.parts)
        return (1 if text else 0, len(text), "")
    else:
        doc = parse_file(path)
    return len(doc.pages), sum(len(page.text) for page in doc.pages), doc.title


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="files to compare; defaults to 10 largest PDFs/HTML files",
    )
    args = parser.parse_args()
    paths = (
        args.paths
        or sorted(
            (
                p
                for p in (ROOT / "data/raw").rglob("*")
                if p.is_file() and p.suffix.lower() in {".pdf", ".html", ".htm"}
            ),
            key=lambda p: p.stat().st_size,
            reverse=True,
        )[:10]
    )
    paths = paths[:10]
    if not paths:
        print("No PDF or HTML files found. Supply up to 10 paths.")
        return 1

    rows = []
    for path in paths:
        path = path if path.is_absolute() else ROOT / path
        try:
            if path.suffix.lower() == ".pdf":
                a = extract(path, "pymupdf")
                b = extract(path, "pypdf")
                labels = ("PyMuPDF", "pypdf")
            elif path.suffix.lower() in {".html", ".htm"}:
                a = extract(path, "trafilatura")
                b = extract(path, "plain")
                labels = ("trafilatura", "plain tags")
            else:
                a = extract(path, "pymupdf")
                b = a
                labels = ("single parser", "single parser")
            rows.append(
                (path.relative_to(ROOT) if path.is_relative_to(ROOT) else path, labels, a, b)
            )
        except (ParseError, OSError, ValueError) as exc:
            rows.append((path, ("error", "error"), (0, 0, str(exc)), (0, 0, "not run")))

    lines = [
        "| File | Parser A (pages/chars) | Parser B (pages/chars) | Better and why |",
        "|---|---:|---:|---|",
    ]
    for path, labels, a, b in rows:
        safe_path = str(path).replace("|", r"\|")
        a_result = (
            a[2].replace("|", r"\|").replace("\n", " ")[:100]
            if not a[0] and a[2]
            else f"{a[0]}/{a[1]}"
        )
        b_result = (
            b[2].replace("|", r"\|").replace("\n", " ")[:100]
            if not b[0] and b[2]
            else f"{b[0]}/{b[1]}"
        )
        lines.append(
            f"| `{safe_path}` | {labels[0]}: {a_result} | {labels[1]}: {b_result} | _review_ |"
        )
    table = "\n".join(lines)
    existing = NOTES.read_text(encoding="utf-8") if NOTES.exists() else ""
    section = "## D07 - Parser comparison"
    details_heading = "### D07 - Parsing my corpus"
    details = ""
    if section in existing:
        prefix, previous = existing.split(section, 1)
        details_at = previous.find(details_heading)
        if details_at >= 0:
            details = "\n\n" + previous[details_at:].rstrip()
        existing = prefix.rstrip()
    NOTES.write_text(
        existing.rstrip() + "\n\n" + section + "\n\n" + table + details + "\n",
        encoding="utf-8",
    )
    print(table)
    print(f"\nCompared {len(rows)} files; inspect them and fill in the verdict column.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
