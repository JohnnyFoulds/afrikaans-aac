# mistral-ocr

Convert a PDF to a full-text MKV using Mistral OCR.

This is the **Tier 1 default** for all PDF-to-MKV conversions. Use `--describe-images`
(requires `GEMINI_API_KEY`) to add Gemini Flash figure descriptions alongside each
extracted JPEG — agents read the prose, humans see the image. 95% cheaper than
Bedrock and handles copyright-blocked PDFs that Bedrock refuses. See `notes/pdf-acquisition.md`
for the full tier order.

## Arguments

Exactly one of `--cite-key` or `--pdf` is required. They are mutually exclusive.

| Argument | Description |
| -------- | ----------- |
| `--cite-key <key>` | BibTeX cite key. PDF resolved from `literature/papers/<key>.pdf`. Always writes to `literature/mkv/` and `literature/img/`. |
| `--pdf <path>` | Path to an arbitrary PDF. Cite key derived from filename stem. If the stem matches a bib entry, writes to `literature/`; otherwise writes next to the PDF. |
| `--output <dir>` | Optional. Override the output directory for both the MKV and the images subdirectory. |
| `--describe-images` | Optional. Call Gemini Flash (`gemini-2.0-flash`) to describe each extracted image. Requires `GEMINI_API_KEY` in `.env`. Description inserted as a `<details>` block after each `![]()` tag — collapsed for humans, readable by agents. |

## Output paths (without --output)

| Mode | MKV | Images |
| ---- | --- | ------ |
| `--cite-key` | `literature/mkv/<key>.md` | `literature/img/<key>/` |
| `--pdf` + bib match | `literature/mkv/<stem>.md` | `literature/img/<stem>/` |
| `--pdf` + no bib match | `<pdf-dir>/<stem>.md` | `<pdf-dir>/<stem>/` |

## Known quirk: unclosed fences

Mistral OCR occasionally wraps visually-boxed content (tip boxes, sidebars) in
` ```markdown ` fences **without a closing fence**, trapping all subsequent content
inside a code block. The script detects this automatically after writing the MKV
and removes any unclosed opening fence line, printing:

```text
WARNING: unclosed fence at line N ('```markdown') — removing spurious opening line.
```

Balanced fences (legitimate code listings) are never touched. See
`notes/pdf-acquisition.md` for full details.

## Known quirk: inline figure captions

Mistral OCR frequently places figure captions immediately after the `![]()` image
tag with no blank line, causing the caption to render inline with the image in
Obsidian and VSCode. The script automatically inserts a blank line after every
image reference line when the following line is non-empty.

## Known quirk: italic citation brackets

Mistral OCR wraps inline citations in italics (`*[1]*`, `*[2, 3]*`). Fixed
automatically by `_fix_italic_citations()` — strips asterisks around numeric citation
brackets. See `notes/pdf-acquisition.md` for full details.

## Known quirk: heading level collapse

Mistral OCR sometimes emits deep subsections at the wrong heading level (e.g. section
`3.2.1` as H1). Fixed automatically by `_fix_heading_levels()` for headings with a
numeric section prefix. Unnumbered headings are left untouched. See
`notes/pdf-acquisition.md` for full details.

## Known quirk: spaced math identifiers

When the source PDF uses tracked letter-spacing, Mistral OCR spaces out characters
inside LaTeX commands: `\operatorname {A t t e n t i o n}`. Fixed automatically by
`_fix_spaced_math_identifiers()`. See `notes/pdf-acquisition.md` for full details.

## Execute

```bash
conda run -n claude-llm python3 /Users/johannes/code/personal/afrikaans-aac/scripts/mistral-ocr.py $ARGUMENTS
```

After the script completes:

1. Report the MKV path, character count, and number of images extracted.
2. If a fence warning was printed, note the line number and confirm the content around it reads correctly as prose.
3. If `--cite-key` was used and the stem does not appear in `literature/references.bib`, remind the user to add a bib entry before citing.
4. If `--pdf` was used and the stem has no bib entry, remind the user that this MKV cannot be cited until a bib entry is added and the PDF is moved to `literature/papers/<cite-key>.pdf`.
