#!/usr/bin/env python3
"""
epub-to-mkv: Convert an EPUB to a full-text MKV markdown file with extracted images.

Mirrors the mistral-ocr.py output conventions exactly:
  - Images saved to literature/img/<cite-key>/img-NNNN.png (JPEG/PNG/GIF/WebP as-is;
    SVG converted to PNG via cairosvg)
  - Image refs use relative paths  ../img/<cite-key>/filename
  - Optional --describe-images: Gemini Flash adds <details> description blocks
  - Post-processing: unclosed fences, heading levels, image spacing (same helpers
    as mistral-ocr.py)

Usage:
    # By cite key (EPUB must exist in literature/papers/<key>.epub)
    python3 scripts/epub-to-mkv.py --cite-key <key>

    # By EPUB path (cite key derived from filename stem)
    python3 scripts/epub-to-mkv.py --epub <path/to/file.epub>

    # Override output directory
    python3 scripts/epub-to-mkv.py --cite-key <key> --output <dir>

    # Describe extracted images with Gemini Flash (requires GEMINI_API_KEY in .env)
    python3 scripts/epub-to-mkv.py --cite-key <key> --describe-images

Output paths (without --output):
    --cite-key  → literature/mkv/<key>.md  +  literature/img/<key>/
    --epub      → if stem matches a bib entry, same as --cite-key
                  otherwise <epub-dir>/<stem>.md  +  <epub-dir>/<stem>/

Images are extracted from the EPUB zip. JPEG/PNG/GIF/WebP saved as-is. SVG images
are converted to PNG via cairosvg (install: conda install -c conda-forge cairosvg).
All images are referenced with relative paths so they render in Obsidian and VSCode.

Post-processing applied (same as mistral-ocr.py):
  - Unclosed fences removed with warning
  - Blank line inserted after every image reference
  - Heading levels remapped for numerically-prefixed headings
"""

import argparse
import base64
import mimetypes
import os
import re
import sys
import time
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

# ---------------------------------------------------------------------------
# Resolve paths relative to repo root
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

SKIP_IDREFS = {"cover", "toc", "ncx", "nav", "index"}

# Raster image extensions extracted as-is
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
# SVG is converted to PNG via cairosvg
SVG_EXTS = {".svg"}


# ---------------------------------------------------------------------------
# .env loader (no python-dotenv dependency)
# ---------------------------------------------------------------------------
def _load_dotenv(env_path: Path) -> None:
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


# ---------------------------------------------------------------------------
# BibTeX helpers
# ---------------------------------------------------------------------------
def _bib_keys(bib_path: Path) -> set[str]:
    if not bib_path.exists():
        return set()
    return set(re.findall(r"^@\w+\{([^,\s]+),", bib_path.read_text(), re.MULTILINE))


# ---------------------------------------------------------------------------
# Post-processing helpers (mirrors mistral-ocr.py)
# ---------------------------------------------------------------------------
def _check_unclosed_fences(text: str, mkv_path: Path) -> bool:
    lines = text.splitlines(keepends=True)
    in_fence = False
    pending_open: int | None = None
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


def _fix_heading_levels(text: str) -> str:
    heading_re = re.compile(r"^(#{1,6}) (.+)$", re.MULTILINE)
    numeric_prefix_re = re.compile(r"^(\d+(?:\.\d+)*\.?)\s")

    def _remap(m: re.Match) -> str:
        hashes = m.group(1)
        title = m.group(2)
        pm = numeric_prefix_re.match(title)
        if not pm:
            return m.group(0)
        prefix = pm.group(1).rstrip(".")
        depth = min(len(prefix.split(".")) + 1, 6)
        correct_hashes = "#" * depth
        if correct_hashes == hashes:
            return m.group(0)
        return f"{correct_hashes} {title}"

    return heading_re.sub(_remap, text)


def _ensure_image_spacing(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    for i, line in enumerate(lines):
        out.append(line)
        if line.strip().startswith("![") and "](../img/" in line:
            next_idx = i + 1
            if next_idx < len(lines) and lines[next_idx].strip() != "":
                out.append("\n")
    return "".join(out)


# ---------------------------------------------------------------------------
# HTML → Markdown converter
# ---------------------------------------------------------------------------
def _strip_ns(tag: str) -> str:
    return re.sub(r"\{[^}]+\}", "", tag)


def _node_to_md(el: ET.Element, img_id_to_relpath: dict[str, str]) -> str:
    """Recursively convert an HTML/XHTML element to plain markdown text."""
    tag = _strip_ns(el.tag).lower()
    text = (el.text or "").strip()
    tail = (el.tail or "").strip()

    children_md = "".join(_node_to_md(c, img_id_to_relpath) for c in el)

    if tag in ("script", "style", "head"):
        return (" " + tail) if tail else ""

    if tag == "h1":
        content = (text + children_md).strip()
        result = f"\n# {content}\n\n"
    elif tag == "h2":
        content = (text + children_md).strip()
        result = f"\n## {content}\n\n"
    elif tag == "h3":
        content = (text + children_md).strip()
        result = f"\n### {content}\n\n"
    elif tag in ("h4", "h5", "h6"):
        content = (text + children_md).strip()
        result = f"\n#### {content}\n\n"
    elif tag == "p":
        content = (text + children_md).strip()
        result = f"\n{content}\n" if content else ""
    elif tag == "li":
        content = (text + children_md).strip()
        result = f"- {content}\n"
    elif tag in ("ul", "ol"):
        result = "\n" + text + children_md + "\n"
    elif tag == "pre":
        content = (text + children_md).strip()
        result = f"\n```\n{content}\n```\n"
    elif tag == "code" and not text.startswith("\n"):
        result = f"`{text}{children_md}`"
    elif tag in ("em", "i"):
        content = (text + children_md).strip()
        result = f"*{content}*" if content else ""
    elif tag in ("strong", "b"):
        content = (text + children_md).strip()
        result = f"**{content}**" if content else ""
    elif tag == "a":
        content = (text + children_md).strip()
        result = content  # drop href
    elif tag == "img":
        src = el.get("src", "")
        alt = el.get("alt", "")
        # Resolve relative src to an img map key
        # Strip leading ../ fragments to normalise to just the basename/subpath
        src_key = src.lstrip("./").lstrip("../")
        # Try exact match first, then suffix match
        rel_path = img_id_to_relpath.get(src, "")
        if not rel_path:
            for k, v in img_id_to_relpath.items():
                if k.endswith(src_key) or src_key.endswith(k.split("/")[-1]):
                    rel_path = v
                    break
        if rel_path:
            result = f"\n![{alt}]({rel_path})\n"
        elif alt:
            result = f"\n[image: {alt}]\n"
        else:
            result = "\n[image]\n"
    elif tag == "br":
        result = "\n"
    elif tag == "hr":
        result = "\n---\n"
    elif tag == "table":
        result = "\n[table]\n" + text + children_md + "\n"
    elif tag in (
        "div", "section", "article", "body", "html",
        "span", "figure", "figcaption", "aside", "nav",
        "header", "footer", "main", "svg",
    ):
        result = text + children_md
    else:
        result = text + children_md

    if tail:
        result += " " + tail
    return result


# ---------------------------------------------------------------------------
# Gemini image description
# ---------------------------------------------------------------------------
def _describe_image(img_bytes: bytes, mime_type: str, api_key: str) -> str:
    try:
        from google import genai  # noqa: PLC0415
        from google.genai import types  # noqa: PLC0415

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type=mime_type),
                (
                    "Describe this figure from an academic book concisely but completely. "
                    "Focus on what information it conveys: data, structure, relationships, "
                    "labels. Use plain prose."
                ),
            ],
        )
        return response.text.strip()
    except Exception as e:  # noqa: BLE001
        print(f"  WARNING: Gemini description failed: {e}")
        return ""


# ---------------------------------------------------------------------------
# Core conversion
# ---------------------------------------------------------------------------
def convert(
    epub_path: Path,
    cite_key: str,
    output_dir: Path,
    describe_images: bool = False,
    gemini_api_key: str = "",
) -> None:
    """Convert epub_path to MKV + images under output_dir."""
    mkv_path = output_dir / f"{cite_key}.md"
    standard_mkv_dir = REPO_ROOT / "literature" / "mkv"
    if output_dir.resolve() == standard_mkv_dir.resolve():
        img_dir = REPO_ROOT / "literature" / "img" / cite_key
        img_rel_dir = f"../img/{cite_key}"
    else:
        img_dir = output_dir / cite_key
        img_rel_dir = cite_key

    z = zipfile.ZipFile(epub_path)
    namelist = set(z.namelist())

    # ---- Find OPF ----
    container_xml = z.read("META-INF/container.xml")
    container = ET.fromstring(container_xml)
    opf_path_str = container.find(
        ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
    ).get("full-path")
    opf_dir = str(Path(opf_path_str).parent)
    if opf_dir == ".":
        opf_dir = ""

    opf = ET.fromstring(z.read(opf_path_str))
    opf_ns = {"opf": "http://www.idpf.org/2007/opf"}

    # ---- Manifest: id → href ----
    manifest: dict[str, str] = {}
    manifest_media_type: dict[str, str] = {}
    for item in opf.findall(".//opf:item", opf_ns):
        item_id = item.get("id", "")
        href = item.get("href", "")
        media_type = item.get("media-type", "")
        manifest[item_id] = href
        manifest_media_type[item_id] = media_type

    # ---- Spine order ----
    spine = [item.get("idref") for item in opf.findall(".//opf:itemref", opf_ns)]

    # ---- Extract images ----
    # Build a map: epub-internal-path → (output-filename, bytes, mime)
    global_img_index = 0
    # key: full epub path (normalised, no leading slash)
    epub_path_to_output: dict[str, tuple[str, bytes, str]] = {}

    img_mime_to_ext = {
        "image/jpeg": ".jpeg",
        "image/jpg": ".jpeg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
    }

    _cairosvg_available: bool | None = None

    def _svg_to_png(svg_bytes: bytes) -> bytes | None:
        """Convert SVG bytes to PNG bytes via cairosvg. Returns None on failure."""
        nonlocal _cairosvg_available
        if _cairosvg_available is False:
            return None
        try:
            import cairosvg  # noqa: PLC0415
            _cairosvg_available = True
            return cairosvg.svg2png(bytestring=svg_bytes)
        except Exception as e:  # noqa: BLE001
            if _cairosvg_available is None:
                print(f"  WARNING: cairosvg not available, SVG images will be skipped: {e}")
            _cairosvg_available = False
            return None

    for item_id, href in manifest.items():
        media_type = manifest_media_type.get(item_id, "")
        href_lower = href.lower()
        is_raster = media_type in img_mime_to_ext or any(href_lower.endswith(ext) for ext in IMAGE_EXTS)
        is_svg = media_type == "image/svg+xml" or href_lower.endswith(".svg")
        if not is_raster and not is_svg:
            continue

        full_epub_path = (f"{opf_dir}/{href}".lstrip("/")) if opf_dir else href
        if full_epub_path not in namelist:
            continue

        raw_bytes = z.read(full_epub_path)
        if not raw_bytes:
            continue

        if is_svg and not is_raster:
            # Convert SVG → PNG
            png_bytes = _svg_to_png(raw_bytes)
            if png_bytes is None:
                continue  # cairosvg unavailable — skip
            img_bytes = png_bytes
            ext = ".png"
            mime = "image/png"
        else:
            img_bytes = raw_bytes
            if media_type in img_mime_to_ext:
                ext = img_mime_to_ext[media_type]
            else:
                ext = Path(href).suffix.lower()
                if ext == ".jpg":
                    ext = ".jpeg"
            mime = media_type if media_type else (mimetypes.guess_type(href)[0] or "image/jpeg")

        filename = f"img-{global_img_index:04d}{ext}"
        epub_path_to_output[full_epub_path] = (filename, img_bytes, mime)
        # Also register by href basename for loose src matching
        epub_path_to_output[href] = (filename, img_bytes, mime)
        epub_path_to_output[href.split("/")[-1]] = (filename, img_bytes, mime)
        global_img_index += 1

    if global_img_index > 0:
        img_dir.mkdir(parents=True, exist_ok=True)
        written_filenames: set[str] = set()
        for full_path, (filename, img_bytes, _mime) in epub_path_to_output.items():
            if filename in written_filenames:
                continue
            (img_dir / filename).write_bytes(img_bytes)
            written_filenames.add(filename)
        print(f"  Extracted {global_img_index} image(s) → {img_dir}/")

    # ---- Build src → relative-path map for the HTML converter ----
    # Keys: full epub path, href, basename
    img_id_to_relpath: dict[str, str] = {}
    for epub_internal, (filename, _bytes, _mime) in epub_path_to_output.items():
        img_id_to_relpath[epub_internal] = f"{img_rel_dir}/{filename}"

    # ---- Optional Gemini descriptions ----
    filename_to_description: dict[str, str] = {}
    if describe_images and global_img_index > 0:
        # Deduplicate: one description per unique filename
        seen: set[str] = set()
        call_count = 0
        for _ep, (filename, img_bytes, mime) in epub_path_to_output.items():
            if filename in seen:
                continue
            seen.add(filename)
            if call_count > 0 and call_count % 15 == 0:
                time.sleep(60)
            elif call_count > 0:
                time.sleep(1)
            desc = _describe_image(img_bytes, mime, gemini_api_key)
            call_count += 1
            if desc:
                filename_to_description[filename] = desc

    # ---- Convert HTML spine items ----
    parts = [f"<!-- Source EPUB: {epub_path.name} -->\n"]
    for idref in spine:
        if idref is None:
            continue
        href = manifest.get(idref, "")
        if not href:
            continue
        if any(s in idref.lower() for s in SKIP_IDREFS):
            continue
        if not href.endswith((".html", ".xhtml", ".htm")):
            continue

        full_path = (f"{opf_dir}/{href}".lstrip("/")) if opf_dir else href
        if full_path not in namelist:
            continue

        try:
            html = z.read(full_path).decode("utf-8", errors="replace")
        except KeyError:
            continue

        # Parse HTML
        html_clean = re.sub(r"<!DOCTYPE[^>]*>", "", html)
        try:
            root = ET.fromstring(html_clean)
        except ET.ParseError:
            continue

        md = _node_to_md(root, img_id_to_relpath)
        md = re.sub(r"\n{3,}", "\n\n", md)
        parts.append(md.strip())

    full_text = "\n\n".join(parts)

    # ---- Insert Gemini <details> blocks after image refs ----
    if filename_to_description:
        def _insert_details(m: re.Match) -> str:
            line = m.group(0)
            # Extract filename from the path
            img_filename = Path(m.group(1)).name
            desc = filename_to_description.get(img_filename, "")
            if desc:
                return (
                    line + "\n\n"
                    f"<details><summary>Figure description</summary>\n\n"
                    f"{desc}\n\n</details>"
                )
            return line

        full_text = re.sub(
            r"!\[[^\]]*\]\(\.\./img/[^)]+\)",
            _insert_details,
            full_text,
        )

    # ---- Post-processing ----
    full_text = _fix_heading_levels(full_text)

    output_dir.mkdir(parents=True, exist_ok=True)
    mkv_path.write_text(full_text, encoding="utf-8")
    print(f"  Written MKV: {mkv_path} ({len(full_text):,} chars)")

    # Spacing fix requires the file to exist (reads back for in-place edit)
    spaced = _ensure_image_spacing(full_text)
    if spaced != full_text:
        mkv_path.write_text(spaced, encoding="utf-8")

    _check_unclosed_fences(mkv_path.read_text(encoding="utf-8"), mkv_path)

    if global_img_index:
        print(f"  Images:      {img_dir}/")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert an EPUB to MKV (markdown) with extracted images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--cite-key",
        metavar="KEY",
        help="BibTeX cite key; EPUB resolved from literature/papers/<key>.epub",
    )
    group.add_argument(
        "--epub",
        metavar="PATH",
        type=Path,
        help="Path to an arbitrary EPUB; cite key derived from filename stem",
    )
    parser.add_argument(
        "--output",
        metavar="DIR",
        type=Path,
        help="Override output directory for MKV and images subdirectory",
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
        epub_path = REPO_ROOT / "literature" / "papers" / f"{cite_key}.epub"
        if not epub_path.exists():
            sys.exit(f"ERROR: EPUB not found: {epub_path}")
        default_output = REPO_ROOT / "literature" / "mkv"
    else:
        epub_path = args.epub.resolve()
        if not epub_path.exists():
            sys.exit(f"ERROR: EPUB not found: {epub_path}")
        cite_key = epub_path.stem
        if cite_key in bib_keys:
            print(f"  Note: '{cite_key}' matches a bib entry — writing to literature/")
            default_output = REPO_ROOT / "literature" / "mkv"
        else:
            print(f"  Note: '{cite_key}' has no bib entry — writing next to EPUB")
            default_output = epub_path.parent

    output_dir = args.output.resolve() if args.output else default_output
    convert(
        epub_path,
        cite_key,
        output_dir,
        describe_images=args.describe_images,
        gemini_api_key=gemini_api_key,
    )


if __name__ == "__main__":
    main()
