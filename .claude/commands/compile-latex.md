# compile-latex

Compile a `.tex` file to PDF using pdflatex + bibtex.

Runs the standard three-pass sequence required for bibliography resolution:
1. `lualatex` — first pass (builds aux files, resolves internal refs)
2. `bibtex` — resolves bibliography from `.aux` + `.bib`
3. `lualatex` — second pass (inserts resolved citations)
4. `lualatex` — third pass (resolves any remaining cross-references)

Uses `lualatex` (not `pdflatex`) because the generated `.tex` files use `fontspec`
and may contain Unicode characters that require LuaLaTeX's native Unicode engine.

**Usage:** `/compile-latex --input <file.tex> [options]`

**Required:**

- `--input <file.tex>` — path to the `.tex` file to compile

**Options:**

- `--output-dir <dir>` — directory for the compiled PDF and aux files.
  Default: same directory as the input `.tex` file
- `--open` — open the resulting PDF after compilation (macOS: uses `open`)

**Examples:**

```bash
# Compile the full proposal
/compile-latex --input pipeline-outputs/proposal.tex

# Compile and open PDF immediately
/compile-latex --input pipeline-outputs/proposal.tex --open

# Compile to a specific output directory
/compile-latex --input pipeline-outputs/proposal.tex --output-dir pipeline-outputs/pdf/
```

**Requirements:**

- MacTeX (CLI tools) must be installed. Install: `brew install --cask mactex-no-gui`
- `pdflatex` must be on PATH: `/Library/TeX/texbin/pdflatex`
- The `.bib` file referenced in the `.tex` must be accessible from the output directory.
  The compile script copies `literature/references.bib` into the output directory automatically.

**Output:**

- `<stem>.pdf` — compiled PDF
- `<stem>.aux`, `<stem>.log`, `<stem>.bbl` — LaTeX auxiliary files (can be ignored)

## Execute

```bash
conda run -n afrikaans-aac python /Users/johannes/code/unisa/unisa-phd-proposal/scripts/compile-latex.py $ARGUMENTS
```

After the script completes, report the path to the PDF and any LaTeX errors or warnings
extracted from the log (underfull/overfull hbox warnings can be ignored; actual errors
beginning with `!` must be reported).
