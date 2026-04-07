# to-latex

Convert one or more markdown files to a compilable LaTeX document.

Applies UNISA-compliant formatting by default:

- A4 paper, 12pt body font, 10pt footnotes
- 1.5 line spacing (as required by UNISA M&D Procedures)
- Left margin 3 cm, other margins 2.5 cm
- `natbib` with IEEE numeric citation style (default; see `--ref-style`)
- Clean section headings, `booktabs` tables, `listings` for code

**Usage:** `/to-latex --input <file> [<file> ...] --output <file> [options]`

**Required:**

- `--input <file> [<file> ...]` — one or more markdown files, assembled in order
- `--output <file>` — path for the output `.tex` file (e.g. `pipeline-outputs/proposal.tex`)

**Options:**

- `--bib <file>` — BibTeX database. Default: `literature/references.bib`
- `--title <text>` — document title (optional; omit to suppress `\maketitle`)
- `--author <text>` — document author (optional)
- `--date <text>` — document date (optional; omit to let LaTeX use today)
- `--template article|report|<path>` — document class:
  - `article` (default) — `\documentclass{article}`, suitable for proposals and papers
  - `report` — `\documentclass{report}`, suitable for longer documents with chapters
  - `<path>` — path to a custom `.tex` preamble file (everything before `\begin{document}`)
- `--ref-style ieee|apa|plainnat|unsrtnat` — bibliography style. Default: `ieee` (numeric [1] citations, IEEEtranN.bst). `apa` = author-year apalike.bst (easier for review). `plainnat`/`unsrtnat` = author-year natbib variants.
- `--no-cite-map` — skip Pandoc `--natbib`; leave `[@key]` anchors as plain text

**Citation syntax (Pandoc standard):**

All citations in source markdown must use pure Pandoc syntax — never type author
names or years manually. Pandoc generates the formatted text from `references.bib`
at render time; style is controlled by `--ref-style`.

| Markdown form | LaTeX output (natbib) | Rendered (IEEE) | Rendered (APA) |
| --- | --- | --- | --- |
| `@lewis-2020-rag demonstrate...` | `\citet{lewis-2020-rag} demonstrate...` | `Lewis et al. [1] demonstrate...` | `Lewis et al. (2020) demonstrate...` |
| `[@lewis-2020-rag]` | `\citep{lewis-2020-rag}` | `[1]` | `(Lewis et al., 2020)` |
| `[@key1; @key2]` | `\citep{key1,key2}` | `[1, 2]` | `(Auth1, YYYY; Auth2, YYYY)` |
| `[-@lewis-2020-rag]` | `\citealt{lewis-2020-rag}` | `[1]` | `2020` |

**## References block handling:**

Each source file may end with a `## References` section (human-review format:
`[@key] Full IEEE citation...`). This block is automatically stripped before
Pandoc conversion — it is for standalone markdown review only. The PDF
bibliography is generated from `\bibliography{references}` by BibTeX.

To regenerate the References block for a file:

```bash
python3 scripts/generate-references-block.py --input <file.md> --update
```

**Compiling the output:**

```bash
cd pipeline-outputs/
lualatex proposal.tex
bibtex proposal
lualatex proposal.tex
lualatex proposal.tex
```

Four passes are needed: lualatex builds the document, bibtex resolves references,
second+third lualatex passes resolve cross-references and page numbers.
Use `lualatex` (not `pdflatex`) — the preamble uses `fontspec` which requires LuaLaTeX.

Or use the `/compile-latex` skill which handles all passes automatically:

```bash
/compile-latex --input pipeline-outputs/proposal.tex --open
```

**Examples:**

```bash
# Full proposal, all sections in order, IEEE style (default)
/to-latex --input proposal/01-introduction.md proposal/02-research-questions.md \
          proposal/03-literature-review.md proposal/04-methodology.md \
          proposal/05-timeline.md \
          --output pipeline-outputs/proposal.tex \
          --title "RAG for ODL: A PhD Research Proposal" \
          --author "Johannes Foulds" \
          --date "March 2026"

# APA style for review (author-year, easier to read before submission)
/to-latex --input proposal/01-introduction.md proposal/02-research-questions.md \
          proposal/03-literature-review.md proposal/04-methodology.md \
          proposal/05-timeline.md \
          --output pipeline-outputs/proposal-review.tex \
          --ref-style apa \
          --title "RAG for ODL: A PhD Research Proposal" \
          --author "Johannes Foulds"

# Single section, no title block
/to-latex --input proposal/03-literature-review.md \
          --output pipeline-outputs/literature-review.tex

# Report class (for longer documents with chapters)
/to-latex --input proposal/04-methodology.md \
          --output pipeline-outputs/methodology.tex \
          --template report
```

## Execute

```bash
conda run -n afrikaans-aac python /Users/johannes/code/personal/afrikaans-aac/scripts/md-to-latex.py $ARGUMENTS
```

After the script completes, report:

1. The output `.tex` file path
2. The number of `\cite` commands produced by Pandoc `--natbib`
3. The compile command to produce a PDF
