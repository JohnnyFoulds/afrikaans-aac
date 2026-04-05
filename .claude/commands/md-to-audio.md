# md-to-audio

Convert any Markdown file to an MP3 audio file using Edge TTS (Neural voice `en-US-AriaNeural`). Tables and equations are treated as first-class content — not silently dropped.

Works for any Markdown: notes, articles, README files, academic papers. Use `--profile paper-lean` when converting academic papers to strip references, affiliations, and appendices.

**Usage:** `/md-to-audio <input.md> <output.mp3> [options]`

**Presets** (expand to a fixed combination of options before applying any overrides):

| Preset | Profile | Math | Tables | Rate | Use for |
|--------|---------|------|--------|------|---------|
| `--preset research` | `paper-lean` | `verbalize` | `llm-summary` | `+0%` | Academic papers — best quality; benchmarked combination |
| `--preset paper` | `paper-lean` | `placeholder` | `script` | `+0%` | Academic papers — no external dependencies |
| `--preset keshav-pass1` | `keshav-pass1` | `strip` | `script` | `+30%` | Keshav Pass 1 — title + abstract + intro + headings + conclusions only; fast scan |
| `--preset keshav-pass2` | `keshav-pass2` | `placeholder` | `script` | `+30%` | Keshav Pass 2 — full paper body, math placeholders |
| `--preset keshav-pass3` | `keshav-pass3` | `verbalize` | `llm-summary` | `+0%` | Keshav Pass 3 — full paper, math verbalized, LLM table summaries |

**Defaults** (when no preset is given):

- Markdown profile: `general` — no structural stripping; converts the full document
- Math mode: `strip` — silently drops LaTeX equations (safe for non-math content)
- Table mode: `script` — deterministic rule-based summarisation; no external dependencies

**Options:**

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--preset` | `research` `paper` `keshav-pass1` `keshav-pass2` `keshav-pass3` | — | Named preset; individual options override preset values |
| `--profile` | `general` `paper` `paper-lean` `keshav-pass1` `keshav-pass2` `keshav-pass3` | `general` | Preprocessing profile |
| `--math` | `strip` `placeholder` `keep` `verbalize` | `strip` | How to handle LaTeX equations |
| `--tables` | `script` `llm-summary` `local-llm-summary` | `script` | How to handle Markdown tables |
| `--table-model` | `openai:gpt-4.1`, `gemini-2.0-flash`, `mistral:mistral-small-latest`, … | `openai:gpt-4.1` | LLM for table summaries (used when `--tables llm-summary`) |
| `--local-model` | any Ollama model name | `qwen2.5:3b` | Local model (used when `--tables local-llm-summary`) |
| `--local-endpoint` | URL | `http://localhost:11434/api/generate` | Ollama endpoint |
| `--voice` | any Edge voice | `en-US-AriaNeural` | TTS voice |
| `--rate` | `+10%`, `-5%`, … | `+0%` | Speaking rate adjustment |
| `--bib` | path to `.bib` file | — | BibTeX file for ID3 tag lookup |
| `--cite-key` | BibTeX cite key | input filename stem | Cite key to look up in `--bib`; defaults to stem of input file |

**Examples:**

```
# General Markdown (notes, articles, README)
/md-to-audio notes/2026-03-31.md notes/2026-03-31.mp3

# Academic paper — best quality (benchmarked)
/md-to-audio literature/mkv/abdallah-2025-retrieval.md pipeline-outputs/abdallah-2025-retrieval.mp3 --preset research

# Academic paper — no external dependencies
/md-to-audio literature/mkv/abdallah-2025-retrieval.md pipeline-outputs/abdallah-2025-retrieval.mp3 --preset paper

# Override one option within a preset
/md-to-audio literature/mkv/paper.md pipeline-outputs/paper.mp3 --preset research --tables local-llm-summary

# Keshav Pass 1 — fast relevance scan (abstract + intro + headings + conclusions)
/md-to-audio literature/mkv/lewis-2020-rag.md literature/mp3/pass1/lewis-2020-rag.mp3 --preset keshav-pass1

# Keshav Pass 2 — careful full read (with ID3 tags from BibTeX)
/md-to-audio literature/mkv/lewis-2020-rag.md literature/mp3/pass2/lewis-2020-rag.mp3 --preset keshav-pass2 --bib literature/references.bib

# Keshav Pass 3 — deep read with math and table summaries
/md-to-audio literature/mkv/lewis-2020-rag.md literature/mp3/pass3/lewis-2020-rag.mp3 --preset keshav-pass3 --bib literature/references.bib

# Embed ID3 tags with explicit cite key (when filename stem doesn't match bib key)
/md-to-audio paper.md paper.mp3 --preset keshav-pass2 --bib literature/references.bib --cite-key lewis-2020-rag
```

---

## Profile guide

| Profile | Use for |
| --------- | ------- |
| `general` | Notes, articles, README, any non-paper Markdown |
| `paper` | Academic papers — stops at References, keeps front matter |
| `paper-lean` | Academic papers — also strips affiliations, funding, appendices |
| `keshav-pass1` | Pass 1 scan — title + abstract + intro + section headings + conclusions only |
| `keshav-pass2` | Pass 2 — full paper body (alias for paper-lean; math/table defaults differ) |
| `keshav-pass3` | Pass 3 — full paper body (alias for paper-lean; math/table defaults differ) |

## Math mode guide

- `strip` — silently drops all equations; best for non-math content
- `placeholder` — says "equation omitted"; good fallback for math papers when Node.js unavailable
- `verbalize` — LaTeX → MathML → SRE Clearspeak spoken English; best quality; requires Node.js + `npm install -g speech-rule-engine`
- `keep` — leaves raw LaTeX in the text; TTS reads it literally (not recommended)

## Table mode guide

- `script` — deterministic row-filtering; no external dependencies
- `llm-summary` — LLM-generated 2–4 sentence summary per table; best quality; requires API key
- `local-llm-summary` — same as above via Ollama; no API cost; requires Ollama running locally

---

## Prerequisites

- `unisa-phd-proposal` conda environment
- For `--math verbalize`: `node` on PATH + `npm install -g speech-rule-engine`
- For `--tables llm-summary`: `OPENAI_API_KEY` in `.env` (or `GEMINI_API_KEY` / `MISTRAL_API_KEY`)
- For `--tables local-llm-summary`: Ollama running at the configured endpoint
- For `--bib`: `mutagen` package (already in `requirements.txt`); no extra setup needed; cite key defaults to the input filename stem, so `lewis-2020-rag.md` → looks up `lewis-2020-rag` in the bib file automatically

---

## Execute

Run this command using the Bash tool:

```bash
/opt/homebrew/Caskroom/miniconda/base/envs/unisa-phd-proposal/bin/python3 /Users/johannes/code/unisa/unisa-phd-proposal/scripts/md-to-audio.py $ARGUMENTS
```

Then run `ls -lh <output-path>` and report the file size.

If stderr contains a Node.js warning (verbalize mode), report it and suggest `--math placeholder`.
If a table LLM call failed and fell back to script mode, note this.
