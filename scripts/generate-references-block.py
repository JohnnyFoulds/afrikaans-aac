#!/usr/bin/env python3
"""
generate-references-block.py — Auto-generate the human-review ## References block.

Reads references.bib and either:
  - a list of cite keys (--keys key1 key2 ...)
  - a markdown file (--input file.md) from which it extracts all [@key] and @key citations

For each cited key it formats an IEEE-style line:
  [@key] Author(s), "Title," *Journal*, vol. V, no. N, pp. X–Y, YYYY. doi: ...

Outputs a ready-to-paste ## References block in markdown.

Usage:
  # From a markdown file (auto-extracts cited keys):
  python3 scripts/generate-references-block.py --input admin/research-outline/research-outline.md

  # From an explicit key list:
  python3 scripts/generate-references-block.py --keys hevner-2004-dsr lewis-2020-rag

  # Write directly into a file (replaces existing ## References section):
  python3 scripts/generate-references-block.py --input admin/research-outline/research-outline.md --update

The ## References block is for standalone markdown review only. It is
automatically stripped by md-to-latex.py before Pandoc conversion so it
never creates a doubled bibliography in the compiled PDF.
"""

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
BIB_FILE = REPO_ROOT / "references" / "references.bib"

# ---------------------------------------------------------------------------
# BibTeX parser
# ---------------------------------------------------------------------------

def parse_bib(bib_path: Path) -> dict[str, dict]:
    """Parse a .bib file into a dict of {cite_key: fields_dict}."""
    text = bib_path.read_text(encoding="utf-8")
    entries: dict[str, dict] = {}

    for m in re.finditer(r"@(\w+)\s*\{([^,\s]+),\s*(.*?)(?=\n@|\Z)", text, re.DOTALL):
        entry_type = m.group(1).lower()
        key = m.group(2).strip()
        body = m.group(3)

        fields: dict[str, str] = {"_type": entry_type}
        for fm in re.finditer(
            r"(\w+)\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", body
        ):
            fields[fm.group(1).lower()] = fm.group(2).strip()

        # Also catch year = 2004 (no braces)
        for fm in re.finditer(r"(\w+)\s*=\s*(\d{4})", body):
            if fm.group(1).lower() not in fields:
                fields[fm.group(1).lower()] = fm.group(2)

        entries[key] = fields

    return entries


# ---------------------------------------------------------------------------
# Citation key extraction
# ---------------------------------------------------------------------------

PANDOC_CITE_RE = re.compile(
    r'\[@([a-z][a-z]+-(?:19|20)\d{2}-[a-z][a-z0-9]+(?:-[a-z][a-z0-9]+)*)'
)
BARE_AT_KEY_RE = re.compile(
    r'(?<!\[)@([a-z][a-z]+-(?:19|20)\d{2}-[a-z][a-z0-9]+(?:-[a-z][a-z0-9]+)*)'
)


def extract_keys_from_file(md_path: Path) -> list[str]:
    text = md_path.read_text(encoding="utf-8")
    # Strip the existing References block before extraction to avoid re-listing
    text = re.sub(r"\n#{1,2}\s+References\s*\n.*", "", text, flags=re.DOTALL | re.IGNORECASE)
    pandoc = set(PANDOC_CITE_RE.findall(text))
    bare = set(BARE_AT_KEY_RE.findall(text))
    all_keys = pandoc | bare
    # Return sorted by order of first appearance
    seen = []
    for m in re.finditer(r'(?:\[@|(?<!\[)@)([a-z][a-z]+-(?:19|20)\d{2}-[a-z][a-z0-9]+(?:-[a-z][a-z0-9]+)*)', text):
        k = m.group(1)
        if k in all_keys and k not in seen:
            seen.append(k)
    return seen


# ---------------------------------------------------------------------------
# IEEE citation formatter
# ---------------------------------------------------------------------------

def _format_authors(author_field: str) -> str:
    """
    Convert BibTeX author field to abbreviated IEEE form.
    'Hevner, Alan R. and March, Salvatore T. and Park, Jinsoo and Ram, Sudha'
    → 'A. R. Hevner, S. T. March, J. Park, and S. Ram'
    """
    raw_authors = [a.strip() for a in re.split(r"\s+and\s+", author_field, flags=re.IGNORECASE)]
    formatted = []
    for a in raw_authors:
        if "," in a:
            parts = [p.strip() for p in a.split(",", 1)]
            last = parts[0]
            first_parts = parts[1].split() if len(parts) > 1 else []
        else:
            words = a.split()
            last = words[-1] if words else a
            first_parts = words[:-1]

        initials = " ".join(w[0] + "." for w in first_parts if w)
        if initials:
            formatted.append(f"{initials} {last}")
        else:
            formatted.append(last)

    if len(formatted) > 1:
        return ", ".join(formatted[:-1]) + ", and " + formatted[-1]
    return formatted[0] if formatted else author_field


def _strip_braces(s: str) -> str:
    """Remove LaTeX brace escapes like {RAG} → RAG."""
    return re.sub(r"\{([^}]*)\}", r"\1", s)


def format_entry(key: str, fields: dict) -> str:
    """Format a single bib entry as an IEEE-style markdown reference line."""
    entry_type = fields.get("_type", "article")
    author = _format_authors(_strip_braces(fields.get("author", "Unknown")))
    title = _strip_braces(fields.get("title", "Untitled"))
    year = fields.get("year", "n.d.")
    doi = fields.get("doi", "")
    url = fields.get("url", "")

    # Build the body depending on entry type
    if entry_type in ("article",):
        journal = _strip_braces(fields.get("journal", ""))
        volume = fields.get("volume", "")
        number = fields.get("number", "")
        pages = fields.get("pages", "").replace("--", "\u2013")
        parts = [f"*{journal}*" if journal else ""]
        if volume:
            parts.append(f"vol. {volume}")
        if number:
            parts.append(f"no. {number}")
        if pages:
            parts.append(f"pp. {pages}")
        parts.append(year)
        body = ", ".join(p for p in parts if p)

    elif entry_type in ("inproceedings", "conference"):
        booktitle = _strip_braces(fields.get("booktitle", ""))
        pages = fields.get("pages", "").replace("--", "\u2013")
        parts = [f"in *{booktitle}*" if booktitle else ""]
        if pages:
            parts.append(f"pp. {pages}")
        parts.append(year)
        body = ", ".join(p for p in parts if p)

    elif entry_type in ("incollection",):
        booktitle = _strip_braces(fields.get("booktitle", ""))
        publisher = _strip_braces(fields.get("publisher", ""))
        pages = fields.get("pages", "").replace("--", "\u2013")
        parts = [f"in *{booktitle}*" if booktitle else ""]
        if publisher:
            parts.append(publisher)
        if pages:
            parts.append(f"pp. {pages}")
        parts.append(year)
        body = ", ".join(p for p in parts if p)

    else:
        # Fallback: just year
        body = year

    line = f'[@{key}] {author}, "{title}," {body}.'

    if doi:
        line += f" doi: {doi}."
    elif url:
        line += f" {url}."

    return line


# ---------------------------------------------------------------------------
# Block generation
# ---------------------------------------------------------------------------

def generate_block(keys: list[str], bib_entries: dict[str, dict]) -> str:
    lines = ["## References", ""]
    missing = []
    for key in keys:
        if key in bib_entries:
            lines.append(format_entry(key, bib_entries[key]))
        else:
            lines.append(f"[@{key}] <!-- NOT IN BIB: {key} -->")
            missing.append(key)
    if missing:
        print(f"WARNING: {len(missing)} key(s) not found in bib: {missing}", file=sys.stderr)
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Update file in-place
# ---------------------------------------------------------------------------

def update_file(md_path: Path, new_block: str) -> None:
    text = md_path.read_text(encoding="utf-8")
    # Remove any existing References section
    stripped = re.sub(
        r"\n#{1,2}\s+References\s*\n.*",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    ).rstrip()
    updated = stripped + "\n\n" + new_block
    md_path.write_text(updated, encoding="utf-8")
    print(f"Updated: {md_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Auto-generate the IEEE ## References block from references.bib."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--input", metavar="FILE",
        help="Markdown file to extract cited keys from.",
    )
    group.add_argument(
        "--keys", nargs="+", metavar="KEY",
        help="Explicit list of cite keys.",
    )
    parser.add_argument(
        "--bib", default=str(BIB_FILE), metavar="FILE",
        help=f"BibTeX file. Default: {BIB_FILE}",
    )
    parser.add_argument(
        "--update", action="store_true",
        help="Update the --input file in-place (replaces existing ## References section).",
    )
    args = parser.parse_args()

    bib_path = Path(args.bib)
    if not bib_path.exists():
        sys.exit(f"ERROR: bib file not found: {bib_path}")

    bib_entries = parse_bib(bib_path)
    print(f"[gen-refs] Loaded {len(bib_entries)} bib entries.", file=sys.stderr)

    if args.input:
        md_path = Path(args.input)
        if not md_path.exists():
            sys.exit(f"ERROR: input file not found: {md_path}")
        keys = extract_keys_from_file(md_path)
        print(f"[gen-refs] Found {len(keys)} cited keys in {md_path.name}.", file=sys.stderr)
    else:
        keys = args.keys
        md_path = None

    block = generate_block(keys, bib_entries)

    if args.update:
        if md_path is None:
            sys.exit("ERROR: --update requires --input (cannot update without a target file).")
        update_file(md_path, block)
    else:
        print(block)


if __name__ == "__main__":
    main()
