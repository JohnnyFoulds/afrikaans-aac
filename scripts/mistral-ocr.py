#!/usr/bin/env python3
"""
Mistral OCR conversion: PDF → MKV + extracted images.

Usage:
    # By cite key (PDF must exist in literature/papers/)
    conda run -n claude-llm python3 scripts/mistral-ocr.py --cite-key <key>

    # By PDF path (cite key derived from filename stem)
    conda run -n claude-llm python3 scripts/mistral-ocr.py --pdf <path/to/file.pdf>

    # Override output directory in either case
    conda run -n claude-llm python3 scripts/mistral-ocr.py --cite-key <key> --output <dir>
    conda run -n claude-llm python3 scripts/mistral-ocr.py --pdf <path> --output <dir>

    # Describe extracted images with Gemini Flash (requires GEMINI_API_KEY in .env)
    conda run -n claude-llm python3 scripts/mistral-ocr.py --cite-key <key> --describe-images

Output paths (without --output):
    --cite-key  → literature/mkv/<key>.md  +  literature/img/<key>/
    --pdf       → if stem matches a bib entry, same as --cite-key
                  otherwise <pdf-dir>/<stem>.md  +  <pdf-dir>/<stem>/

This is the Tier 1 default for all PDF-to-MKV conversions. Use --describe-images
(requires GEMINI_API_KEY) to add Gemini Flash figure descriptions: agents read the
prose inside <details> blocks, humans see the JPEG. 95% cheaper than Bedrock and
handles copyright-blocked PDFs that Bedrock refuses. See notes/pdf-acquisition.md.

Known quirks handled automatically: unclosed fences removed; blank lines inserted
after image references; italic citation brackets stripped; heading levels remapped
from numeric prefixes; spaced math identifiers collapsed.

With --describe-images, Gemini Flash describes each extracted JPEG and inserts
the description as a <details> block after the ![]() tag: collapsed for humans,
readable by agents. Requires GEMINI_API_KEY in .env.
"""

import argparse
import sys
import os
import base64
import re
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve paths relative to repo root (script may be run from anywhere)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


def _load_dotenv(env_path: Path) -> None:
    """Minimal .env loader — no dependency on python-dotenv."""
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv(REPO_ROOT / ".env")

from mistralai import Mistral  # noqa: E402


def _bib_keys(bib_path: Path) -> set[str]:
    """Return all cite keys defined in a .bib file."""
    if not bib_path.exists():
        return set()
    return set(re.findall(r"^@\w+\{([^,\s]+),", bib_path.read_text(), re.MULTILINE))


def _check_unclosed_fences(text: str, mkv_path: Path) -> bool:
    """Detect and remove fence lines that are opened but never closed.

    Markdown fences do not nest.  Any line matching ^``` toggles state:
      OUT → IN  (open: record this line number as a pending open)
      IN  → OUT (close: pair it with the most recent pending open, clear it)

    At EOF, any pending open that was never paired is spurious.
    Mistral OCR occasionally wraps styled callout boxes (e.g. tip boxes,
    sidebars) in ```markdown fences without ever closing them, which causes
    all subsequent content to be hidden inside a code block.

    Strategy: remove every spurious opening line and warn.  Lines are deleted
    in reverse order so that earlier line numbers stay valid after deletion.
    We do NOT insert closing fences — we cannot know the intended boundary.
    Legitimate code blocks (balanced open + close pairs) are never touched.

    Returns True if the file was modified.
    """
    lines = text.splitlines(keepends=True)

    in_fence = False
    pending_open: int | None = None  # 1-based line number of current unmatched open
    spurious: list[int] = []

    for i, line in enumerate(lines, start=1):
        if line.startswith("```"):
            if not in_fence:
                in_fence = True
                pending_open = i
            else:
                in_fence = False
                pending_open = None

    if in_fence and pending_open is not None:
        spurious.append(pending_open)

    if not spurious:
        return False

    for lineno in sorted(spurious, reverse=True):
        print(
            f"  WARNING: unclosed fence at line {lineno} "
            f"({lines[lineno - 1].rstrip()!r}) — removing spurious opening line."
        )
        del lines[lineno - 1]

    mkv_path.write_text("".join(lines), encoding="utf-8")
    return True


def _strip_data_uri_prefix(b64_string: str) -> str:
    """Remove 'data:<mime>;base64,' prefix if present.

    base64.b64decode() silently ignores non-base64 characters, so passing the
    full data URI causes the prefix bytes to be decoded as garbage and prepended
    to the real image data.  Always strip before decoding.
    """
    if "," in b64_string:
        return b64_string.split(",", 1)[1]
    return b64_string


def _fix_italic_citations(text: str) -> str:
    """Remove spurious italic markers wrapping numeric citation brackets.

    Mistral OCR consistently italicises inline citations, producing *[1]*,
    *[2, 3]* instead of the standard [1], [2, 3].  Strip the asterisks.
    Only matches brackets whose content is digits, commas, and spaces —
    leaving any intentional italic markup untouched.
    """
    return re.sub(r"\*(\[\d[\d,\s]*\])\*", r"\1", text)


def _fix_heading_levels(text: str) -> str:
    """Remap heading levels for headings that have a numeric section prefix.

    Mistral OCR occasionally collapses heading depth — a sub-section like
    "3.2.1 Scaled Dot-Product Attention" may be emitted as H1 (#) instead of
    H4 (####).  For headings whose text begins with a numeric section number
    (e.g. "1", "2.3", "3.2.1"), the correct depth can be inferred from the
    number of dot-separated components:

        1 component  (e.g. "3")       → H2
        2 components (e.g. "3.2")     → H3
        3 components (e.g. "3.2.1")   → H4
        N components                  → H(N+1), capped at H6

    Headings without a numeric prefix (Abstract, Introduction, etc.) are left
    exactly as Mistral produced them — we have no basis for correcting those.

    A numeric prefix is defined as one or more dot-separated tokens where the
    first token is a decimal integer (handles "3.2.1", "10.1.2", "I" is NOT
    matched since it is not a decimal integer).  Optional trailing punctuation
    after the number (e.g. "3." or "3.2.") is stripped before counting.
    """
    # Matches: any number of # chars, space, then a heading text
    heading_re = re.compile(r"^(#{1,6}) (.+)$", re.MULTILINE)
    # A numeric section prefix: first token is digits, separated by dots,
    # optionally ending with a dot.  Examples: "1", "3.2", "3.2.1.", "10.1"
    numeric_prefix_re = re.compile(r"^(\d+(?:\.\d+)*\.?)\s")

    def _remap(m: re.Match) -> str:
        hashes = m.group(1)
        title = m.group(2)
        pm = numeric_prefix_re.match(title)
        if not pm:
            return m.group(0)  # no numeric prefix — leave untouched
        prefix = pm.group(1).rstrip(".")
        depth = len(prefix.split(".")) + 1  # 1 component → H2
        depth = min(depth, 6)
        correct_hashes = "#" * depth
        if correct_hashes == hashes:
            return m.group(0)  # already correct
        return f"{correct_hashes} {title}"

    return heading_re.sub(_remap, text)


def _fix_spaced_math_identifiers(text: str) -> str:
    """Collapse letter-spaced identifiers inside LaTeX math commands.

    Mistral OCR occasionally produces tracked/letter-spaced text inside math
    commands when the source PDF uses that styling.  The result is individual
    characters separated by spaces inside the braces, e.g.:

        \\operatorname {A t t e n t i o n}
        \\text {e m b e d}
        \\mathrm {e l i t e}

    This function collapses those back to the correct form:

        \\operatorname{Attention}
        \\text{embed}
        \\mathrm{elite}

    The pattern: a LaTeX command (\\word) followed by a space and a brace group
    whose contents are exclusively single non-space characters separated by
    single spaces (e.g. "A t t e n t i o n").  Multi-character tokens inside
    braces are left untouched, as are already-correct forms like \\text{embed}.
    """
    # Match: \command {single chars separated by spaces}
    # The brace content must be: (X )+ where X is any non-space char, ending
    # with a single non-space char (no trailing space).
    pattern = re.compile(
        r"(\\[A-Za-z]+)"          # LaTeX command, e.g. \operatorname
        r"\s*"                     # optional space before brace
        r"\{("                     # opening brace
        r"(?:[^\s{}] )+"           # one or more "X " pairs
        r"[^\s{}]"                 # final char (no trailing space)
        r")\}"                     # closing brace
    )

    def _collapse(m: re.Match) -> str:
        cmd = m.group(1)
        content = m.group(2)
        # Only collapse if every token between spaces is a single character
        tokens = content.split(" ")
        if all(len(t) == 1 for t in tokens):
            return f"{cmd}{{{content.replace(' ', '')}}}"
        return m.group(0)  # leave untouched

    return pattern.sub(_collapse, text)


def _ensure_image_spacing(text: str) -> str:
    """Ensure a blank line follows every image reference line.

    Mistral OCR frequently places the figure caption on the very next line
    after the image tag with no blank line, causing the caption to render
    inline with the image in markdown viewers.  Insert a blank line between
    the image line and whatever follows it when one is not already present.
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    for i, line in enumerate(lines):
        out.append(line)
        if line.strip().startswith("![") and "](../img/" in line:
            # Look ahead: if the next non-empty line exists and there is no
            # blank line already, insert one.
            next_idx = i + 1
            if next_idx < len(lines) and lines[next_idx].strip() != "":
                out.append("\n")
    return "".join(out)


def _describe_image(img_bytes: bytes, api_key: str) -> str:
    """Call Gemini Flash to produce a prose description of an academic figure.

    Returns the description string, or an empty string on any error (with a
    printed warning so the caller can continue without failing the conversion).
    """
    try:
        from google import genai  # noqa: PLC0415
        from google.genai import types  # noqa: PLC0415

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                (
                    "Describe this figure from an academic paper concisely but completely. "
                    "Focus on what information it conveys: data, structure, relationships, "
                    "labels. Use plain prose."
                ),
            ],
        )
        return response.text.strip()
    except Exception as e:  # noqa: BLE001
        print(f"  WARNING: Gemini description failed: {e}")
        return ""


def convert(
    pdf_path: Path,
    cite_key: str,
    output_dir: Path,
    describe_images: bool = False,
    gemini_api_key: str = "",
) -> None:
    """Run Mistral OCR on pdf_path and write MKV + images under output_dir."""
    mkv_path = output_dir / f"{cite_key}.md"
    standard_mkv_dir = REPO_ROOT / "literature" / "mkv"
    if output_dir.resolve() == standard_mkv_dir.resolve():
        img_dir = REPO_ROOT / "literature" / "img" / cite_key
    else:
        img_dir = output_dir / cite_key

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        sys.exit("ERROR: MISTRAL_API_KEY not set in environment / .env")

    print(f"Reading {pdf_path} ({pdf_path.stat().st_size // 1024} KB)...")
    pdf_b64 = base64.standard_b64encode(pdf_path.read_bytes()).decode("ascii")

    print("Calling Mistral OCR API (mistral-ocr-latest)...")
    client = Mistral(api_key=api_key)
    result = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{pdf_b64}",
        },
        include_image_base64=True,
    )

    # ------------------------------------------------------------------
    # Build a global image index across all pages so filenames are unique
    # even when Mistral resets per-page counters.
    # ------------------------------------------------------------------
    global_img_index: int = 0
    id_to_filename: dict[str, str] = {}
    filename_to_bytes: dict[str, bytes] = {}

    has_images = any(getattr(page, "images", None) for page in result.pages)
    if has_images:
        img_dir.mkdir(parents=True, exist_ok=True)

    for page in result.pages:
        for img in getattr(page, "images", []) or []:
            raw_b64 = img.image_base64 or ""
            if not raw_b64:
                continue
            clean_b64 = _strip_data_uri_prefix(raw_b64)
            img_bytes = base64.b64decode(clean_b64)

            filename = f"img-{global_img_index:04d}.jpeg"
            out_path = img_dir / filename
            out_path.write_bytes(img_bytes)

            id_to_filename[img.id] = filename
            filename_to_bytes[filename] = img_bytes
            global_img_index += 1

    print(f"  Extracted {global_img_index} image(s).")

    # ------------------------------------------------------------------
    # Assemble markdown, rewriting per-page image ids to relative paths.
    # Image refs are relative to the mkv file location so they render in
    # both Obsidian and VSCode regardless of output_dir.
    # ------------------------------------------------------------------
    # When output_dir is the standard literature/mkv/, images live at
    # ../img/<cite-key>/.  For non-standard output dirs we use a sibling
    # directory with the same name as the cite key.
    if output_dir.resolve() == standard_mkv_dir.resolve():
        img_rel_dir = f"../img/{cite_key}"
    else:
        img_rel_dir = cite_key  # sibling dir next to the MKV

    # Pre-compute Gemini descriptions once per image (not once per page×image).
    filename_to_description: dict[str, str] = {}
    if describe_images and filename_to_bytes:
        gemini_call_count: int = 0
        for filename, img_bytes in filename_to_bytes.items():
            if gemini_call_count > 0 and gemini_call_count % 15 == 0:
                time.sleep(60)  # respect free-tier 15 req/min limit
            elif gemini_call_count > 0:
                time.sleep(1)
            description = _describe_image(img_bytes, gemini_api_key)
            gemini_call_count += 1
            if description:
                filename_to_description[filename] = description

    pages_md: list[str] = []
    for page in result.pages:
        md = page.markdown or ""
        for orig_id, filename in id_to_filename.items():
            rel_path = f"{img_rel_dir}/{filename}"
            md = md.replace(f"![{orig_id}]({orig_id})", f"![{filename}]({rel_path})")
            md = re.sub(
                rf"!\[([^\]]*)\]\({re.escape(orig_id)}\)",
                rf"![\1]({rel_path})",
                md,
            )
            if filename in filename_to_description:
                details_block = (
                    f"\n\n<details><summary>Figure description</summary>"
                    f"\n\n{filename_to_description[filename]}\n\n</details>"
                )
                md = md.replace(
                    f"![{filename}]({rel_path})",
                    f"![{filename}]({rel_path}){details_block}",
                )
        pages_md.append(md)

    full_text = f"<!-- Source PDF: {pdf_path.name} -->\n\n" + "\n\n".join(pages_md)
    full_text = _fix_italic_citations(full_text)
    full_text = _fix_heading_levels(full_text)
    full_text = _fix_spaced_math_identifiers(full_text)
    full_text = _ensure_image_spacing(full_text)
    output_dir.mkdir(parents=True, exist_ok=True)
    mkv_path.write_text(full_text, encoding="utf-8")
    print(f"  Written MKV: {mkv_path} ({len(full_text):,} chars)")

    _check_unclosed_fences(full_text, mkv_path)

    if global_img_index:
        print(f"  Images:      {img_dir}/")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a PDF to MKV using Mistral OCR.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--cite-key",
        metavar="KEY",
        help="BibTeX cite key; PDF resolved from literature/papers/<key>.pdf",
    )
    group.add_argument(
        "--pdf",
        metavar="PATH",
        type=Path,
        help="Path to an arbitrary PDF; cite key derived from filename stem",
    )
    parser.add_argument(
        "--output",
        metavar="DIR",
        type=Path,
        help="Override output directory for MKV and images",
    )
    parser.add_argument(
        "--describe-images",
        action="store_true",
        help="Call Gemini Flash to describe each extracted image (requires GEMINI_API_KEY in .env)",
    )
    args = parser.parse_args()

    gemini_api_key = ""
    if args.describe_images:
        gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_api_key:
            sys.exit("ERROR: --describe-images requires GEMINI_API_KEY in environment / .env")

    bib_path = REPO_ROOT / "references" / "references.bib"
    bib_keys = _bib_keys(bib_path)

    if args.cite_key:
        cite_key = args.cite_key
        pdf_path = REPO_ROOT / "literature" / "papers" / f"{cite_key}.pdf"
        if not pdf_path.exists():
            sys.exit(f"ERROR: PDF not found: {pdf_path}")
        default_output = REPO_ROOT / "literature" / "mkv"
    else:
        pdf_path = args.pdf.resolve()
        if not pdf_path.exists():
            sys.exit(f"ERROR: PDF not found: {pdf_path}")
        cite_key = pdf_path.stem
        if cite_key in bib_keys:
            print(f"  Note: '{cite_key}' matches a bib entry — writing to literature/")
            default_output = REPO_ROOT / "literature" / "mkv"
        else:
            print(f"  Note: '{cite_key}' has no bib entry — writing next to PDF")
            default_output = pdf_path.parent

    output_dir = args.output.resolve() if args.output else default_output
    convert(
        pdf_path,
        cite_key,
        output_dir,
        describe_images=args.describe_images,
        gemini_api_key=gemini_api_key,
    )


if __name__ == "__main__":
    main()
