"""
md-to-latex.py — Standalone Markdown → LaTeX converter.

Converts one or more markdown files to a single well-formatted LaTeX document,
applying UNISA formatting requirements (A4, 12pt, 1.5 spacing, natbib author-year).

Usage:
    conda run -n afrikaans-aac python scripts/md-to-latex.py \\
        --input   proposal/01-introduction.md [proposal/02-research-questions.md ...] \\
        --output  pipeline-outputs/proposal.tex \\
        [--bib    literature/references.bib] \\
        [--title  "RAG for ODL: A PhD Research Proposal"] \\
        [--author "Johannes Foulds"] \\
        [--date   "March 2026"] \\
        [--template article|report|<path-to-preamble.tex>]

Output:
    <output>.tex  — compilable LaTeX document
    Compile with: lualatex <output>.tex && bibtex <output> && lualatex <output>.tex (×2)

Templates:
    article  (default) — \\documentclass{article}, suitable for proposals and papers
    report            — \\documentclass{report}, suitable for longer documents with chapters
    <path>            — path to a .tex file containing a custom preamble (everything up to
                        but NOT including \\begin{document}); the tool appends body + \\end{document}

Citation syntax (Pandoc standard):
    Use [@cite-key] in markdown — Pandoc converts these natively via --natbib:
      [@lewis-2020-rag]                  →  \\citep{lewis-2020-rag}
      Lewis et al. [-@lewis-2020-rag]    →  Lewis et al. \\citealt{lewis-2020-rag}
      [@key1; @key2]                     →  \\citep{key1,key2}
    The cite key must exactly match an entry in references.bib.
    No fuzzy surname+year lookup is performed — keys are verified by the
    citation integrity checker (.claude/scripts/check_citation_integrity.py).
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# UNISA / academic formatting constants
# ---------------------------------------------------------------------------
ARTICLE_PREAMBLE = r"""\documentclass[12pt,a4paper]{{article}}

% Compiled with lualatex (handles Unicode natively)
% Typography — fontspec replaces fontenc/inputenc for LuaLaTeX
\usepackage{{fontspec}}
\setmainfont{{Latin Modern Roman}}
\setmonofont{{Latin Modern Mono}}
\usepackage{{microtype}}

% Page geometry — UNISA: left margin ≥ 2cm; standard academic margins elsewhere
\usepackage[a4paper, left=3cm, right=2.5cm, top=2.5cm, bottom=2.5cm]{{geometry}}

% Line spacing — UNISA requires at least 1.5
\usepackage{{setspace}}
\onehalfspacing

% Mathematics
\usepackage{{amsmath,amssymb}}

% Tables
\usepackage{{booktabs}}
\usepackage{{longtable}}
\usepackage{{array}}
\usepackage{{pdflscape}}  % landscape environment for wide tables on a rotated page

% Figures
\usepackage{{graphicx}}

% Spacing — \frenchspacing prevents enlarged inter-sentence gaps (standard in arXiv papers)
\frenchspacing

% Hyperlinks (load before natbib to avoid conflicts)
% \autoref{{}} automatically prepends "Section", "Figure", "Table" etc.
\usepackage[hidelinks, breaklinks=true]{{hyperref}}

% Citations — natbib; options and style set by --ref-style
\usepackage[{natbib_options}]{{natbib}}
\bibliographystyle{{{bib_style}}}

% Code listings
\usepackage{{listings}}
\lstset{{basicstyle=\ttfamily\footnotesize, breaklines=true,
         frame=single, xleftmargin=0.5cm}}

% Section heading style
\usepackage{{titlesec}}
\titleformat{{\section}}{{\large\bfseries}}{{\thesection}}{{1em}}{{}}
\titleformat{{\subsection}}{{\normalsize\bfseries}}{{\thesubsection}}{{1em}}{{}}
\titleformat{{\subsubsection}}{{\normalsize\itshape}}{{\thesubsubsection}}{{1em}}{{}}

% Footnote font size — UNISA: 10pt
\renewcommand{{\footnotesize}}{{\fontsize{{10}}{{12}}\selectfont}}

% Paragraph spacing
\setlength{{\parskip}}{{0.5em}}
\setlength{{\parindent}}{{0em}}

% Figure best practice (for architecture diagrams etc.):
%   \begin{{figure}}[htbp]  — never [h] alone; [htbp] prevents "float too large"
%     \centering             — not \begin{{center}}
%     \includegraphics[width=\linewidth]{{filename}}
%     \caption{{Caption text below the figure.}}
%     \label{{fig:label}}
%   \end{{figure}}
% Use \autoref{{fig:label}} in text (outputs "Figure 1" with hyperlink).

% Abstract environment
\renewenvironment{{abstract}}{{%
  \begin{{center}}\bfseries Abstract\end{{center}}%
  \begin{{quotation}}
}}{{%
  \end{{quotation}}
}}

% Pandoc compatibility shims
\providecommand{{\tightlist}}{{\setlength{{\itemsep}}{{0pt}}\setlength{{\parskip}}{{0pt}}}}
\newcounter{{none}}

% Prompt box — styled like NLP/AI papers (tcolorbox wrapping fancyvrb Verbatim)
% The outer tcolorbox provides border + background; the inner Verbatim handles
% small monospace font and automatic line breaking.
\usepackage{{fancyvrb}}
\usepackage{{fvextra}}  % extends fancyvrb with breaklines support
\usepackage{{tcolorbox}}
\tcbuselibrary{{breakable,skins}}
\newtcolorbox{{promptbox}}{{
  breakable,
  enhanced,
  colback=gray!8,
  colframe=gray!40,
  boxrule=0.4pt,
  arc=2pt,
  left=2pt, right=2pt, top=2pt, bottom=2pt,
}}

{title_block}
"""

REPORT_PREAMBLE = r"""\documentclass[12pt,a4paper]{{report}}

% Compiled with lualatex (handles Unicode natively)
% Typography — fontspec replaces fontenc/inputenc for LuaLaTeX
\usepackage{{fontspec}}
\setmainfont{{Latin Modern Roman}}
\setmonofont{{Latin Modern Mono}}
\usepackage{{microtype}}

% Page geometry — UNISA: left margin ≥ 2cm
\usepackage[a4paper, left=3cm, right=2.5cm, top=2.5cm, bottom=2.5cm]{{geometry}}

% Line spacing — UNISA requires at least 1.5
\usepackage{{setspace}}
\onehalfspacing

% Mathematics
\usepackage{{amsmath,amssymb}}

% Tables
\usepackage{{booktabs}}
\usepackage{{longtable}}
\usepackage{{array}}
\usepackage{{adjustbox}}

% Figures
\usepackage{{graphicx}}

% Spacing — \frenchspacing prevents enlarged inter-sentence gaps
\frenchspacing

% Hyperlinks — \autoref{{}} prepends "Section", "Figure", "Table" automatically
\usepackage[hidelinks, breaklinks=true]{{hyperref}}

% Citations — natbib; options and style set by --ref-style
\usepackage[{natbib_options}]{{natbib}}
\bibliographystyle{{{bib_style}}}

% Code listings
\usepackage{{listings}}
\lstset{{basicstyle=\ttfamily\footnotesize, breaklines=true,
         frame=single, xleftmargin=0.5cm}}

% Footnote font size — UNISA: 10pt
\renewcommand{{\footnotesize}}{{\fontsize{{10}}{{12}}\selectfont}}

% Paragraph spacing
\setlength{{\parskip}}{{0.5em}}
\setlength{{\parindent}}{{0em}}

% Pandoc compatibility shims
\providecommand{{\tightlist}}{{\setlength{{\itemsep}}{{0pt}}\setlength{{\parskip}}{{0pt}}}}
\newcounter{{none}}

% Prompt box
\usepackage{{fancyvrb}}
\usepackage{{fvextra}}  % extends fancyvrb with breaklines support
\usepackage{{tcolorbox}}
\tcbuselibrary{{breakable,skins}}
\newtcolorbox{{promptbox}}{{
  breakable,
  enhanced,
  colback=gray!8,
  colframe=gray!40,
  boxrule=0.4pt,
  arc=2pt,
  left=2pt, right=2pt, top=2pt, bottom=2pt,
}}

{title_block}
"""

# ---------------------------------------------------------------------------
# Reference style registry
# Maps --ref-style name → (natbib_options, bst_filename)
# natbib_options: passed to \usepackage[...]{natbib}
# bst_filename:   passed to \bibliographystyle{...}
# ---------------------------------------------------------------------------
REF_STYLES: dict[str, tuple[str, str]] = {
    "ieee":      ("numbers,sort&compress", "IEEEtranN"),
    "apa":       ("authoryear,round",      "apalike"),
    "plainnat":  ("authoryear,round",      "plainnat"),
    "unsrtnat":  ("authoryear",            "unsrtnat"),
}
DEFAULT_REF_STYLE = "apa"


TITLE_BLOCK_TEMPLATE = r"""\title{{{title}}}
\author{{{author}}}
\date{{{date}}}"""

BIB_BLOCK = r"""
\bibliography{{{bib_stem}}}
"""


# ---------------------------------------------------------------------------
# Pre-processing helpers
# ---------------------------------------------------------------------------
def strip_references_block(md_text: str) -> str:
    """
    Remove any trailing '## References' (or '# References') section and
    everything after it from the markdown text before Pandoc conversion.

    The human-readable References block (format: '[@key] Full citation...')
    exists only for standalone markdown review. It must not reach Pandoc
    because Pandoc would convert [@key] to \\citep{key} and pass the rest
    of the line as plain text, creating a doubled bibliography alongside
    \\bibliography{references}.
    """
    # Match a level-1 or level-2 heading named "References" (case-insensitive),
    # possibly preceded by whitespace. Strip it and everything that follows.
    return re.sub(
        r"\n#{1,2}\s+References\s*\n.*",
        "",
        md_text,
        flags=re.DOTALL | re.IGNORECASE,
    )


# ---------------------------------------------------------------------------
# Pandoc conversion
# ---------------------------------------------------------------------------
def markdown_to_latex_body(md_text: str, bib_path: Path | None = None) -> str:
    """
    Use pandoc to convert markdown to LaTeX body (no preamble, no \\begin{document}).
    Pandoc handles: headings, bold, italic, lists, tables, code blocks, blockquotes.

    When bib_path is provided, --natbib is passed so that Pandoc converts
    [@cite-key] anchors to \\citep{} / \\citet{} commands natively.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(md_text)
        tmp_path = tmp.name

    cmd = [
        "pandoc",
        tmp_path,
        "--from", "markdown",
        "--to", "latex",
        "--listings",            # use lstlisting instead of verbatim (enables breaklines + footnotesize)
        "--no-highlight",
        "--wrap=none",
    ]
    if bib_path and bib_path.exists():
        # --natbib tells Pandoc to emit \citep{}/\citet{} commands (for natbib)
        # instead of resolving citations to formatted text (which --citeproc does).
        cmd += ["--natbib", f"--bibliography={bib_path}"]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    Path(tmp_path).unlink(missing_ok=True)

    if result.returncode != 0:
        sys.exit(f"ERROR: pandoc failed:\n{result.stderr}")

    body = result.stdout

    # Strip numeric prefixes that pandoc preserved verbatim in \section{} titles.
    # e.g. \section{Chapter 1: Introduction} → \section{Introduction}
    #      \subsection{1.1 Background}       → \subsection{Background}
    #      \subsubsection{3.2.1 DSR}         → \subsubsection{DSR}
    # LaTeX auto-numbering produces the correct numbers; the markdown numbers
    # are for source readability only and must not appear in the compiled output.
    # Also strips "Chapter N:" prefix from top-level sections.
    body = re.sub(
        r"(\\(?:sub)*section\{)Chapter\s+\d+:\s*",
        r"\1",
        body,
    )
    body = re.sub(
        r"(\\(?:sub)*section\{)\d+(?:\.\d+)*\s+",
        r"\1",
        body,
    )

    # Replace \begin{verbatim}...\end{verbatim} with a styled prompt box.
    # Strategy: replace verbatim with fancyvrb Verbatim (which supports fontsize
    # and breaklines) wrapped in a tcolorbox for border + background.
    # The verbatim content is kept verbatim — LaTeX special chars remain safe.
    def verbatim_to_promptbox(m: re.Match) -> str:
        content = m.group(1)  # content between \begin{verbatim} and \end{verbatim}
        return (
            "\\begin{promptbox}\n"
            "\\begin{Verbatim}[fontsize=\\small,breaklines=true,breakanywhere=true]\n"
            + content.lstrip("\n")
            + "\\end{Verbatim}\n"
            "\\end{promptbox}"
        )

    body = re.sub(
        r"\\begin\{verbatim\}\n?(.*?)\\end\{verbatim\}",
        verbatim_to_promptbox,
        body,
        flags=re.DOTALL,
    )

    # Replace Unicode block-fill characters (U+2588 █) used in Gantt tables
    # with a solid LaTeX box of equivalent visual weight.
    body = body.replace("\u2588", r"\rule{0.8em}{0.7em}")

    # Wrap wide longtables (> 5 columns) in a landscape page so they get the
    # full A4 landscape width (~25cm). Narrow tables stay portrait.
    # Handles pandoc's optional {\def\LTcaptype{none}...} wrapper around the table.
    def maybe_landscape(m: re.Match) -> str:
        pre   = m.group(1) or ""   # {\def\LTcaptype{none} ... opening brace group
        col_spec = m.group(2)
        table_body = m.group(3)
        post  = m.group(4) or ""   # closing } of the brace group
        n_cols = len(re.findall(r"[lcrp]", col_spec))
        inner = pre + "\\begin{longtable}[]{" + col_spec + "}" + table_body + "\\end{longtable}" + post
        if n_cols > 5:
            return "\\begin{landscape}\n" + inner + "\n\\end{landscape}"
        return inner

    # Column spec like @{}lllllll@{} contains nested braces, so we can't use
    # [^}]* — instead match the known pandoc pattern @{} ... @{} explicitly.
    body = re.sub(
        r"(\{\\def\\LTcaptype\{none\}[^\n]*\n)?"
        r"\\begin\{longtable\}\[\]\{(@\{\}[lcrp|@ {}]*@\{\})\}(.*?)\\end\{longtable\}"
        r"(\n\})?",
        maybe_landscape,
        body,
        flags=re.DOTALL,
    )

    # Pull any section/subsection heading that immediately precedes \begin{landscape}
    # inside the landscape block, so the heading and table appear on the same rotated page.
    # "Immediately precedes" means only whitespace/newlines between heading and landscape.
    body = re.sub(
        r"(\\(?:sub)*section\{[^}]*\}\\label\{[^}]*\}\n+)(\\begin\{landscape\})",
        r"\2\n\1",
        body,
    )

    return body


# ---------------------------------------------------------------------------
# Preamble builder
# ---------------------------------------------------------------------------
def build_preamble(
    template: str,
    title: str,
    author: str,
    date: str,
    natbib_options: str,
    bib_style: str,
) -> str:
    title_block = ""
    if title or author or date:
        title_block = TITLE_BLOCK_TEMPLATE.format(
            title=_latex_escape(title),
            author=_latex_escape(author),
            date=_latex_escape(date),
        )

    fmt = dict(title_block=title_block, natbib_options=natbib_options, bib_style=bib_style)
    if template == "article":
        return ARTICLE_PREAMBLE.format(**fmt)
    if template == "report":
        return REPORT_PREAMBLE.format(**fmt)
    # Custom preamble file — ref style not injected (user controls their own preamble)
    p = Path(template)
    if not p.exists():
        sys.exit(f"ERROR: custom preamble file not found: {template}")
    preamble = p.read_text(encoding="utf-8")
    if title_block:
        preamble = preamble.rstrip() + "\n" + title_block + "\n"
    return preamble


def _latex_escape(s: str) -> str:
    """Escape special LaTeX characters in plain text strings (title, author)."""
    replacements = [
        ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
        ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"),
        ("^", r"\^{}"),
    ]
    for char, escaped in replacements:
        s = s.replace(char, escaped)
    return s


# ---------------------------------------------------------------------------
# Document assembly
# ---------------------------------------------------------------------------
def assemble_document(
    preamble: str,
    body: str,
    has_title: bool,
    bib_stem: str | None,
) -> str:
    parts = [preamble.rstrip(), "", r"\begin{document}", ""]
    if has_title:
        parts += [r"\maketitle", ""]
    parts.append(body.strip())
    parts.append("")
    if bib_stem:
        parts.append(BIB_BLOCK.format(bib_stem=bib_stem).strip())
        parts.append("")
    parts.append(r"\end{document}")
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Convert markdown files to a compilable LaTeX document. "
            "Applies UNISA formatting (A4, 12pt, 1.5 spacing, natbib) and "
            "optionally maps author-year citations to \\cite{} commands."
        )
    )
    parser.add_argument(
        "--input", required=True, nargs="+", metavar="FILE",
        help="One or more markdown files to convert, assembled in order.",
    )
    parser.add_argument(
        "--output", required=True, metavar="FILE",
        help="Path for the output .tex file.",
    )
    parser.add_argument(
        "--bib", default="literature/references.bib", metavar="FILE",
        help="Path to the BibTeX database for citation mapping. "
             "Default: literature/references.bib",
    )
    parser.add_argument(
        "--title", default="", metavar="TEXT",
        help="Document title (optional).",
    )
    parser.add_argument(
        "--author", default="", metavar="TEXT",
        help="Document author (optional).",
    )
    parser.add_argument(
        "--date", default="", metavar="TEXT",
        help="Document date. Default: empty (LaTeX uses today's date).",
    )
    parser.add_argument(
        "--template", default="article",
        metavar="article|report|FILE",
        help=(
            "'article' (default) — \\documentclass{article}, for proposals/papers. "
            "'report' — \\documentclass{report}, for longer documents with chapters. "
            "A file path — custom preamble .tex file."
        ),
    )
    parser.add_argument(
        "--ref-style",
        default=DEFAULT_REF_STYLE,
        dest="ref_style",
        metavar="|".join(REF_STYLES),
        help=(
            "Bibliography style. "
            "'ieee' (default) — IEEE numeric [1] citations, IEEEtranN.bst. "
            "'apa' — author-year (Author, YYYY), apalike.bst. "
            "'plainnat' — author-year, sorted alphabetically, plainnat.bst. "
            "'unsrtnat' — author-year, unsorted (citation order), unsrtnat.bst."
        ),
    )
    parser.add_argument(
        "--no-cite-map", action="store_true", dest="no_cite_map",
        help="Skip Pandoc --natbib citation conversion — leave [@key] anchors as plain text.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    repo_root = Path(__file__).parent.parent

    # Resolve input files
    input_paths = []
    for inp in args.input:
        p = Path(inp)
        if not p.is_absolute():
            p = repo_root / p
        if not p.exists():
            sys.exit(f"ERROR: input file not found: {p}")
        input_paths.append(p)

    # Resolve bib
    bib_path = Path(args.bib)
    if not bib_path.is_absolute():
        bib_path = repo_root / bib_path

    bib_stem: str | None = None

    if not args.no_cite_map:
        if not bib_path.exists():
            print(
                f"WARNING: bib file not found ({bib_path}). "
                "Proceeding without citation conversion.",
                file=sys.stderr,
            )
        else:
            bib_stem = bib_path.stem
            print(
                f"[md-to-latex] Bib: {bib_path.name} — Pandoc --natbib will convert [@key] anchors",
                file=sys.stderr,
            )

    # Resolve output
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo_root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Read and concatenate markdown
    md_parts = []
    for p in input_paths:
        text = p.read_text(encoding="utf-8")
        # Strip the human-review References block before Pandoc conversion.
        # The block (format: [@key] Full citation...) is for standalone markdown
        # review only; it must not reach Pandoc to avoid a doubled bibliography.
        text = strip_references_block(text)
        md_parts.append(text)
        print(
            f"[md-to-latex] Input: {p.name} ({len(text.split())} words)",
            file=sys.stderr,
        )

    combined_md = "\n\n".join(md_parts)

    # Pandoc: markdown → LaTeX body
    # --natbib converts [@cite-key] anchors to \citep{}/\citet{} natively.
    print("[md-to-latex] Running pandoc...", file=sys.stderr)
    bib_path_for_pandoc = bib_path if (bib_path.exists() and not args.no_cite_map) else None
    body = markdown_to_latex_body(combined_md, bib_path_for_pandoc)

    all_warnings: list[str] = []
    if bib_path_for_pandoc:
        total_cite_matches = body.count(r"\cite")
        print(
            f"[md-to-latex] Citations: {total_cite_matches} \\cite commands produced by Pandoc --natbib",
            file=sys.stderr,
        )

    # Resolve reference style
    ref_style = args.ref_style.lower()
    if ref_style not in REF_STYLES:
        sys.exit(
            f"ERROR: unknown --ref-style '{ref_style}'. "
            f"Valid options: {', '.join(REF_STYLES)}"
        )
    natbib_options, bib_style = REF_STYLES[ref_style]
    print(f"[md-to-latex] Reference style: {ref_style} ({bib_style})", file=sys.stderr)

    # Build preamble
    preamble = build_preamble(
        args.template, args.title, args.author, args.date,
        natbib_options, bib_style,
    )
    has_title = bool(args.title or args.author or args.date)

    # Assemble
    document = assemble_document(preamble, body, has_title, bib_stem)

    # Write
    output_path.write_text(document, encoding="utf-8")
    print(
        f"[md-to-latex] Written: {output_path} "
        f"({len(document.splitlines())} lines)",
        file=sys.stderr,
    )
    print(
        f"[md-to-latex] Compile: lualatex {output_path.name} && "
        f"bibtex {output_path.stem} && lualatex {output_path.name} && "
        f"lualatex {output_path.name}",
        file=sys.stderr,
    )

    if all_warnings:
        print("\n[md-to-latex] Warnings:", file=sys.stderr)
        for w in all_warnings:
            print(w, file=sys.stderr)


if __name__ == "__main__":
    main()
