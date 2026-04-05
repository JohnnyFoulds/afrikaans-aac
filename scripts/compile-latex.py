"""
compile-latex.py — Standalone LaTeX → PDF compiler.

Runs the standard pdflatex + bibtex three-pass sequence on a .tex file and
produces a PDF. Copies the project .bib file into the output directory so
bibtex can resolve citations regardless of where the .tex file lives.

Usage:
    conda run -n kb-nav-agent python scripts/compile-latex.py \\
        --input   pipeline-outputs/proposal.tex \\
        [--output-dir pipeline-outputs/] \\
        [--open]

Requires:
    MacTeX CLI tools: brew install --cask mactex-no-gui
    pdflatex binary:  /Library/TeX/texbin/pdflatex
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# MacTeX installs its binaries here; may not be on PATH in conda envs
TEXBIN = Path("/Library/TeX/texbin")
LUALATEX = TEXBIN / "lualatex"   # handles Unicode natively; required for fontspec
BIBTEX = TEXBIN / "bibtex"


def find_binary(name: str, preferred: Path) -> Path:
    if preferred.exists():
        return preferred
    # Fall back to PATH
    found = shutil.which(name)
    if found:
        return Path(found)
    sys.exit(
        f"ERROR: '{name}' not found. Install MacTeX:\n"
        "  brew install --cask mactex-no-gui\n"
        "Then open a new terminal or add /Library/TeX/texbin to PATH."
    )


def run(cmd: list, cwd: Path, label: str, check_exit: bool = True) -> str:
    """Run a command, return stdout+stderr combined.

    check_exit=True  — fail on non-zero exit code (used for bibtex).
    check_exit=False — fail only on actual LaTeX '!' errors in log output
                       (used for pdflatex, which exits 1 on pass-1 warnings
                       like missing .bbl that are normal and expected).
    """
    result = subprocess.run(
        [str(c) for c in cmd],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    log = result.stdout + result.stderr

    if check_exit and result.returncode != 0:
        print(f"\n[compile-latex] {label} FAILED (exit {result.returncode})", file=sys.stderr)
        lines = log.splitlines()
        for line in lines[-40:]:
            print(f"  {line}", file=sys.stderr)
        sys.exit(1)

    # For pdflatex passes, fail only on hard errors (lines starting with '!')
    hard_errors = [line for line in log.splitlines() if line.startswith("!")]
    if hard_errors:
        print(f"\n[compile-latex] {label} — LaTeX errors found:", file=sys.stderr)
        for e in hard_errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)

    return log


def extract_errors(log: str) -> list[str]:
    """Extract lines beginning with '!' (LaTeX errors) from a pdflatex log."""
    return [line for line in log.splitlines() if line.startswith("!")]


def extract_warnings(log: str) -> list[str]:
    """Extract non-trivial warnings (citation undefined, reference undefined)."""
    keywords = ["Citation", "Reference", "Undefined", "multiply defined", "runaway"]
    return [
        line for line in log.splitlines()
        if any(kw.lower() in line.lower() for kw in keywords)
        and not line.strip().startswith("%")
    ]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compile a .tex file to PDF (pdflatex + bibtex, three-pass)."
    )
    parser.add_argument(
        "--input", required=True, metavar="FILE",
        help="Path to the .tex file to compile.",
    )
    parser.add_argument(
        "--output-dir", default=None, dest="output_dir", metavar="DIR",
        help=(
            "Directory for compiled PDF and aux files. "
            "Default: same directory as the input .tex file."
        ),
    )
    parser.add_argument(
        "--open", action="store_true",
        help="Open the resulting PDF after compilation (macOS: uses 'open').",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    repo_root = Path(__file__).parent.parent

    pdflatex = find_binary("lualatex", LUALATEX)
    bibtex = find_binary("bibtex", BIBTEX)

    # Resolve input
    tex_path = Path(args.input)
    if not tex_path.is_absolute():
        tex_path = repo_root / tex_path
    if not tex_path.exists():
        sys.exit(f"ERROR: input file not found: {tex_path}")

    # Resolve output directory
    if args.output_dir:
        out_dir = Path(args.output_dir)
        if not out_dir.is_absolute():
            out_dir = repo_root / out_dir
    else:
        out_dir = tex_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = tex_path.stem

    # If the tex file lives elsewhere, copy it into out_dir for compilation
    working_tex = out_dir / tex_path.name
    if tex_path.resolve() != working_tex.resolve():
        shutil.copy2(tex_path, working_tex)
        print(
            f"[compile-latex] Copied {tex_path.name} → {out_dir}/",
            file=sys.stderr,
        )

    # Copy .bib into output directory so bibtex can find it
    bib_src = repo_root / "references" / "references.bib"
    if bib_src.exists():
        bib_dst = out_dir / bib_src.name
        if bib_src.resolve() != bib_dst.resolve():
            shutil.copy2(bib_src, bib_dst)
            print(
                f"[compile-latex] Copied {bib_src.name} → {out_dir}/",
                file=sys.stderr,
            )
    else:
        print(
            f"WARNING: {bib_src} not found — bibtex may fail to resolve citations.",
            file=sys.stderr,
        )

    lualatex_cmd = [
        pdflatex,   # variable holds lualatex path
        "-interaction=nonstopmode",
        "-output-directory", str(out_dir),
        str(working_tex),
    ]

    # Pass 1 — exit code 1 is expected (no .bbl yet); fail only on hard errors
    print("[compile-latex] Pass 1/3: lualatex...", file=sys.stderr)
    log1 = run(lualatex_cmd, out_dir, "lualatex pass 1", check_exit=False)

    # bibtex — use exit code
    print("[compile-latex] bibtex...", file=sys.stderr)
    run([bibtex, stem], out_dir, "bibtex", check_exit=True)

    # Pass 2
    print("[compile-latex] Pass 2/3: lualatex...", file=sys.stderr)
    log2 = run(lualatex_cmd, out_dir, "lualatex pass 2", check_exit=False)

    # Pass 3
    print("[compile-latex] Pass 3/3: lualatex...", file=sys.stderr)
    log3 = run(lualatex_cmd, out_dir, "lualatex pass 3", check_exit=False)

    pdf_path = out_dir / f"{stem}.pdf"
    if not pdf_path.exists():
        sys.exit(f"ERROR: compilation appeared to succeed but PDF not found at {pdf_path}")

    print(f"[compile-latex] PDF: {pdf_path}", file=sys.stderr)
    # Print to stdout so the skill can capture it
    print(str(pdf_path))

    # Report errors and warnings from final pass
    errors = extract_errors(log3)
    warnings = extract_warnings(log3)

    if errors:
        print("\n[compile-latex] LaTeX errors:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)

    if warnings:
        print("\n[compile-latex] Notable warnings:", file=sys.stderr)
        for w in set(warnings):  # deduplicate
            print(f"  {w}", file=sys.stderr)

    if not errors and not warnings:
        print("[compile-latex] No errors or notable warnings.", file=sys.stderr)

    if args.open:
        subprocess.run(["open", str(pdf_path)], check=False)


if __name__ == "__main__":
    main()
