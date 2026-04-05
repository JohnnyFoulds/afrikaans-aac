# epub-to-mkv

Convert an EPUB to a full-text MKV markdown file with extracted images.

Mirrors `mistral-ocr` output conventions exactly:
- Images saved to `literature/img/<cite-key>/img-NNNN.png` (JPEG/PNG/GIF/WebP as-is; SVG converted to PNG via cairosvg)
- Image refs use relative paths `../img/<cite-key>/filename` so they render in Obsidian and VSCode
- Optional `--describe-images`: Gemini Flash adds `<details>` description blocks after each image
- Post-processing: unclosed fences removed, heading levels remapped, blank lines inserted after images

## Arguments

Exactly one of `--cite-key` or `--epub` is required. They are mutually exclusive.

| Argument | Description |
| -------- | ----------- |
| `--cite-key <key>` | BibTeX cite key. EPUB resolved from `literature/papers/<key>.epub`. Always writes to `literature/mkv/` and `literature/img/`. |
| `--epub <path>` | Path to an arbitrary EPUB. Cite key derived from filename stem. If stem matches a bib entry, writes to `literature/`; otherwise writes next to the EPUB. |
| `--output <dir>` | Optional. Override the output directory for both the MKV and the images subdirectory. |
| `--describe-images` | Optional. Call Gemini Flash (`gemini-2.0-flash`) to describe each extracted image. Requires `GEMINI_API_KEY` in `.env`. Description inserted as a `<details>` block after each `![]()` tag — collapsed for humans, readable by agents. |

## Output paths (without --output)

| Mode | MKV | Images |
| ---- | --- | ------ |
| `--cite-key` | `literature/mkv/<key>.md` | `literature/img/<key>/` |
| `--epub` + bib match | `literature/mkv/<stem>.md` | `literature/img/<stem>/` |
| `--epub` + no bib match | `<epub-dir>/<stem>.md` | `<epub-dir>/<stem>/` |

## Notes

- SVG images are converted to PNG via cairosvg (installed via conda-forge — `conda install -c conda-forge cairosvg`)
- Post-processing is identical to `mistral-ocr`: unclosed fences removed with warning, blank line inserted after image refs, heading levels remapped for numerically-prefixed headings
- No Mistral API key required — epub conversion is entirely local

## Execute

```bash
/opt/homebrew/Caskroom/miniconda/base/envs/unisa-phd-proposal/bin/python3 \
  /Users/johannes/code/personal/afrikaans-aac/scripts/epub-to-mkv.py $ARGUMENTS
```

After the script completes:

1. Report the MKV path, character count, and number of images extracted.
2. If a fence warning was printed, note the line number and confirm the content around it reads correctly.
3. If `--cite-key` was used and the stem does not appear in `literature/references.bib`, remind the user to add a bib entry before citing.
4. If `--epub` was used and the stem has no bib entry, remind the user that this MKV cannot be cited until a bib entry is added and the EPUB is moved to `literature/papers/<cite-key>.epub`.
