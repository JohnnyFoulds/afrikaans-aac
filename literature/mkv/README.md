# literature/mkv/

Full-text Markdown conversions of PDFs, used by `verify-claims` for citation
verification. Every file must be named `<cite-key>.md` where `<cite-key>` exactly
matches the entry key in `literature/references.bib`.

Convert PDFs via `/mistral-ocr` (primary) or Bedrock streaming (fallback).
Never use PyMuPDF or other local text-extraction tools — see [CLAUDE.md](../../CLAUDE.md).

See [literature/README.md](../README.md) for the full conversion workflow.
