#!/usr/bin/env python3
"""
Citation integrity check.

Usage:
  # CI mode (GitHub Actions) — scans all guarded files in the repo:
  python3 check_citation_integrity.py --ci

  # Pre-commit hook mode — reads staged file content from git:
  python3 check_citation_integrity.py --pre-commit

  # Claude Code PreToolUse hook mode — checks a single file's content:
  python3 check_citation_integrity.py <file_path> <file_content>

Exit codes:
  0 — all cited keys have MKVs, or file is not guarded
  1 — one or more cited keys are missing MKVs (CI / pre-commit)
  2 — one or more cited keys are missing MKVs (Claude Code hook, exit 2 = block)

Guarded paths (any file under these paths is checked):
  proposal/
  admin/outreach/
  admin/research-outline/

Citation syntax:
  Primary (Pandoc standard): [@cite-key] or [@cite-key; @cite-key2]
  Legacy (bare key, prose context): firstauthor-YEAR-keyword — still detected
  The [@key] form is authoritative; the bare form is a fallback for prose that
  has not yet been migrated to Pandoc syntax.
"""

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MKV_DIR = REPO_ROOT / "literature" / "mkv"
BIB_FILE = REPO_ROOT / "references" / "references.bib"

GUARDED_PATHS = [
    REPO_ROOT / "proposal",
    REPO_ROOT / "admin" / "outreach",
    REPO_ROOT / "admin" / "research-outline",
]

# Primary: Pandoc [@cite-key] syntax — extracts key from inside [@ ... ]
# Handles single: [@lewis-2020-rag]  and multi: [@es-2024-ragas; @hevner-2004-dsr]
PANDOC_CITE_RE = re.compile(r'\[@([a-z][a-z]+-(?:19|20)\d{2}-[a-z][a-z0-9]+(?:-[a-z][a-z0-9]+)*)')

# Fallback: bare cite-key in prose (for files not yet migrated to [@key] syntax)
# The 4-digit year distinguishes real cite keys from hyphenated prose words.
BARE_CITE_KEY_RE = re.compile(r'\b([a-z][a-z]+-(?:19|20)\d{2}-[a-z][a-z0-9]+(?:-[a-z][a-z0-9]+)*)\b')

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def load_bib_keys() -> set:
    """Return all cite keys defined in references.bib."""
    if not BIB_FILE.exists():
        return set()
    return set(re.findall(
        r'^@\w+\{([^,\s]+),',
        BIB_FILE.read_text(encoding="utf-8"),
        re.MULTILINE
    ))


def extract_cite_keys(text: str) -> set:
    """Extract all cite keys from text.

    Detects both Pandoc [@key] syntax (primary) and bare cite keys in prose
    (fallback for files not yet migrated). Both forms are checked against the
    bib and MKV corpus.
    """
    pandoc_keys = set(PANDOC_CITE_RE.findall(text))
    bare_keys = set(BARE_CITE_KEY_RE.findall(text))
    return pandoc_keys | bare_keys


def is_guarded(path: Path) -> bool:
    """Return True if path falls under a guarded path."""
    for guard in GUARDED_PATHS:
        if guard.is_dir():
            try:
                path.relative_to(guard)
                return True
            except ValueError:
                pass
        elif guard.is_file() or not guard.exists():
            if path == guard:
                return True
    return False


def check_keys(cited_keys: set, bib_keys: set) -> tuple[list, list]:
    """
    Returns (missing_mkv, not_in_bib).

    missing_mkv: keys in bib but with no MKV — claims unverifiable
    not_in_bib:  keys matching the cite-key pattern but absent from bib —
                 paper not added to corpus at all

    Both are violations. We do not silently ignore a key just because it
    isn't in the bib — if it looks like a cite key it must be in the bib.
    """
    missing_mkv = sorted(
        k for k in cited_keys & bib_keys
        if not (MKV_DIR / f"{k}.md").exists()
    )
    not_in_bib = sorted(cited_keys - bib_keys)
    return missing_mkv, not_in_bib


def format_error(missing_mkv: list, not_in_bib: list, source: str = "") -> str:
    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════╗",
        "║         CITATION INTEGRITY VIOLATION — COMMIT BLOCKED       ║",
        "╚══════════════════════════════════════════════════════════════╝",
        "",
    ]
    if source:
        lines.append(f"  File: {source}")
        lines.append("")
    if not_in_bib:
        lines.append("  Keys matching cite-key pattern but NOT in references.bib:")
        lines.append("  (Paper not added to corpus — cannot verify any claim)")
        lines.append("")
        for k in not_in_bib:
            lines.append(f"    NOT IN BIB: {k}")
        lines.append("")
    if missing_mkv:
        lines.append("  Keys in bib but with NO MKV in literature/mkv/:")
        lines.append("  (Paper not converted — claims cannot be verified against full text)")
        lines.append("")
        for k in missing_mkv:
            lines.append(f"    MISSING MKV: {k}")
        lines.append("")
    lines += [
        "  Required steps before committing:",
        "    1. Add bib entry  →  literature/references.bib",
        "    2. Retrieve PDF   →  literature/papers/<key>.pdf",
        "    3. Verify PDF     →  file literature/papers/<key>.pdf",
        "    4. Convert        →  Anthropic API → literature/mkv/<key>.md",
        "    5. Read the MKV   →  verify your claim against the full text",
        "    6. Re-stage and commit",
        "",
        "  See CLAUDE.md §CITATION INTEGRITY for full procedure.",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def run_ci() -> int:
    """Scan all guarded files in the repo. Used by GitHub Actions."""
    bib_keys = load_bib_keys()
    all_violations = {}

    for guard in GUARDED_PATHS:
        if guard.is_file() and guard.exists():
            files = [guard]
        elif guard.is_dir():
            files = list(guard.rglob("*.md"))
        else:
            files = []

        for f in files:
            text = f.read_text(encoding="utf-8")
            keys = extract_cite_keys(text)
            missing_mkv, not_in_bib = check_keys(keys, bib_keys)
            if missing_mkv or not_in_bib:
                rel = f.relative_to(REPO_ROOT)
                all_violations[str(rel)] = (missing_mkv, not_in_bib)

    if all_violations:
        for path, (missing_mkv, not_in_bib) in all_violations.items():
            print(format_error(missing_mkv, not_in_bib, path), file=sys.stderr)
        return 1

    total = sum(
        len(extract_cite_keys(
            (REPO_ROOT / p).read_text(encoding="utf-8")
            if (REPO_ROOT / p).is_file() else ""
        ) & bib_keys)
        for guard in GUARDED_PATHS
        for p in ([guard] if guard.is_file() else list(guard.rglob("*.md")))
        if Path(p).is_file()
    )
    print(f"Citation integrity OK — all cited bib keys have MKVs.")
    return 0


def run_pre_commit() -> int:
    """Check staged files. Used by the Git pre-commit hook."""
    import subprocess
    bib_keys = load_bib_keys()

    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    staged = result.stdout.strip().splitlines()

    all_violations = {}
    for rel_path in staged:
        abs_path = REPO_ROOT / rel_path
        if not is_guarded(abs_path):
            continue
        # Skip non-markdown files (binary files such as MP3/PDF crash text=True)
        if abs_path.suffix.lower() not in (".md", ".txt"):
            continue
        # Read staged content (not working tree)
        staged_content = subprocess.run(
            ["git", "show", f":{rel_path}"],
            capture_output=True, text=True, cwd=REPO_ROOT
        )
        if staged_content.returncode != 0:
            continue
        keys = extract_cite_keys(staged_content.stdout)
        missing_mkv, not_in_bib = check_keys(keys, bib_keys)
        if missing_mkv or not_in_bib:
            all_violations[rel_path] = (missing_mkv, not_in_bib)

    if all_violations:
        for path, (missing_mkv, not_in_bib) in all_violations.items():
            print(format_error(missing_mkv, not_in_bib, path), file=sys.stderr)
        return 1

    return 0


def run_claude_hook(file_path: str, content: str) -> int:
    """
    Check a single file's content. Used as a Claude Code PreToolUse hook.
    Returns exit code 2 to block the tool call.
    """
    bib_keys = load_bib_keys()
    abs_path = Path(file_path).resolve() if file_path else Path()

    if not is_guarded(abs_path):
        return 0

    keys = extract_cite_keys(content)
    missing_mkv, not_in_bib = check_keys(keys, bib_keys)

    if missing_mkv or not_in_bib:
        print(format_error(missing_mkv, not_in_bib, file_path), file=sys.stderr)
        return 2  # Claude Code interprets exit 2 as a tool call block

    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]

    if args and args[0] == "--ci":
        sys.exit(run_ci())

    elif args and args[0] == "--pre-commit":
        sys.exit(run_pre_commit())

    elif len(args) >= 2:
        # Claude Code hook: file_path content
        sys.exit(run_claude_hook(args[0], args[1]))

    elif len(args) == 1:
        # Called with just a file path — read from disk
        p = Path(args[0]).resolve()
        if p.exists():
            sys.exit(run_claude_hook(str(p), p.read_text(encoding="utf-8")))
        sys.exit(0)

    else:
        # No args — run CI mode as default
        sys.exit(run_ci())
