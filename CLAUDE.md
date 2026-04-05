# Afrikaans AAC for Post-Stroke Aphasia

## Project

A custom Augmentative and Alternative Communication (AAC) tool built for a specific user: an Afrikaans-speaking man who lost his speech following a stroke. Comprehension is intact; he can read and use a touchscreen with large targets.

**Research direction:** Assistive technology design for post-stroke aphasia; methodology undecided between User-Centred Design (UCD) / Assistive Technology (AT) research and Design Science Research (DSR, Hevner et al. 2004)

**Methodology:** To be confirmed — UCD/AT or DSR (Hevner et al. 2004)

---

## ⛔ CITATION INTEGRITY — ABSOLUTE RULES — NO EXCEPTIONS

These rules apply to **every piece of written output** in this repo: proposal sections, outreach emails, research outlines, notes, summaries. No exceptions. A false or unverifiable citation in academic or professional work is a serious credibility risk.

### THE HARD RULE

**You may not write any claim about a paper unless you have read the full text of that paper in `literature/mkv/<cite-key>.md`.**

Not the abstract. Not the title. Not a summary from memory. The full mkv.

This rule applies to:

- Every citation in `proposal/research/` and `proposal/business/`
- Every reference to a paper in `admin/outreach/` emails
- Every synthesis claim in `notes/`
- Every pipeline output before it is accepted into `proposal/`

### BEFORE WRITING ANY DOCUMENT THAT REFERENCES A PAPER

Run this checklist. **Stop and complete it before writing a single sentence.**

```text
For each paper you intend to cite or reference:
  [ ] Does literature/mkv/<cite-key>.md exist?
      NO → retrieve PDF, convert to mkv, THEN write. No exceptions.
  [ ] Have you read the mkv in this session (used Read tool)?
      NO → read it now. Do not rely on memory or summaries.
  [ ] Can you find a quotable passage in the mkv that directly supports your claim?
      NO → do not make the claim. Qualify or remove it.
```

A false or unverifiable claim in this can result in rejection or disqualification academically and severe credibility loss professionally.

**Before writing or accepting any revision to any proposal section:**

1. Every cited paper must have a full mkv in `literature/mkv/<cite-key>.md`
2. Every factual claim must be verified against a quotable passage in that mkv — not the abstract, not memory, not a pipeline summary
3. The `/verify-claims` pipeline must pass before any section is committed to `proposal/`
4. Any item flagged `[NEEDS VERIFICATION]` must be resolved (sourced, qualified, or removed) before the file is committed — never leave `[NEEDS VERIFICATION]` in committed proposal text

**The pipeline is not a substitute for reading.** Even if `/verify-claims` passes, if you wrote a claim without reading the mkv, stop and verify manually. Automated verification catches missing citations; it does not catch claims that are plausible but wrong.

### SPECIFIC RULE FOR OUTREACH EMAILS AND HIGH-STAKES DOCUMENTS

Every paper referenced in an outreach email, grant application, or ethics submission must have:

1. A PDF in `literature/papers/<cite-key>.pdf`
2. A full mkv in `literature/mkv/<cite-key>.md`
3. Every claim verified against a quotable passage in the mkv — sentence by sentence

**Do not draft, revise, or finalise any such document until all referenced papers have full MKVs and every claim has been verified sentence by sentence against the mkv.**

If a paper cannot be retrieved: either remove the reference, or restrict claims strictly to what the abstract states, marked explicitly as "the abstract reports."

### ENFORCEMENT

If at any point during writing you realise you are about to make a claim about a paper whose mkv you have not read in this session:

**STOP. Do not write the claim. Retrieve and read the mkv first.**

This is not optional. There is no urgency that justifies bypassing it.

---

## Citation Syntax — Pandoc Standard (REQUIRED)

All citations in guarded files (`proposal/research/`, `proposal/business/`, `admin/outreach/`) **must** use pure Pandoc citation syntax. **Never type author names or years manually** — Pandoc generates them from `references.bib` at render time. Style (IEEE numbered vs APA author-year) is a render-time flag (`--ref-style ieee` or `--ref-style apa`).

### The two Pandoc citation forms

```markdown
# 1. Narrative (@key) — author is grammatical subject; Pandoc generates "Author et al. (YYYY)" or "[N]":
@lewis-2020-rag demonstrate that RAG reduces hallucination.
@hevner-2004-dsr's framework consists of three design cycles.

# 2. Parenthetical ([@key]) — fully parenthetical "(Author, YYYY)" or "[N]":
retrieval is corpus-dependent [@thakur-2021-beir].

# Multi-cite:
infrastructure constraints [@lembani-2020-digital-divide; @ndibalema-2022-odl-constraints]

# Suppressed author (rare — cite number/year only, no author repeated):
[-@lewis-2020-rag] in their follow-up work...
```

### Human-review References block

Each markdown document in `proposal/research/` and `proposal/business/` ends with a `## References` section for standalone human review. Format:

```markdown
## References

[@hevner-2004-dsr] A. R. Hevner, S. T. March, J. Park, and S. Ram, "Design science in information systems research," *MIS Q.*, vol. 28, no. 1, pp. 75–105, 2004. doi: 10.2307/25148625.
```

**This block is for human reading only.** It is:

- Auto-generated by `scripts/generate-references-block.py` (never hand-typed)
- Automatically stripped by `scripts/md-to-latex.py` before Pandoc conversion, preventing a doubled bibliography in the compiled PDF
- The real bibliography in the PDF is generated by BibTeX from `\bibliography{references}`

To regenerate the References block for a file:

```bash
python3 scripts/generate-references-block.py --input <file.md> --update
```

### Why this matters

- Both `@key` and `[@key]` forms are detected by `check_citation_integrity.py` (via `BARE_CITE_KEY_RE`) and `verify-claims.py` (via Pass 1 and Pass 3)
- Pandoc `--natbib` converts `@key` → `\citet{key}`, `[@key]` → `\citep{key}` for LaTeX
- The `scripts/md-to-latex.py` pipeline uses Pandoc `--natbib` — no custom citation mapping is needed
- Style is controlled by `--ref-style ieee` (default, IEEE numbered) or `--ref-style apa` (author-year)

### Rules

1. **Never type author names or years manually** — use `@key` or `[@key]`; Pandoc generates the formatted text
2. Use `@key` when the author is the grammatical subject of the sentence
3. Use `[@key]` for all other citations (parenthetical, end-of-clause, multi-cite)
4. The cite key must exactly match an entry in `literature/references.bib`
5. The cited paper must have an MKV in `literature/mkv/<cite-key>.md`
6. Never invent a cite key — look it up in `literature/references.bib`
7. The `## References` block is auto-generated — never edit it manually; run `generate-references-block.py --update` instead

---

## Conda Environment

The correct conda environment for this project is always defined in `environment.yml` — check it first before running any Python command. The environment name is `afrikaans-aac`.

If a required dependency is missing from the environment, add it to `requirements.txt` (not `requirements_dev.txt` unless it is a dev-only tool) and install it into the environment:

```bash
/opt/homebrew/Caskroom/miniconda/base/envs/afrikaans-aac/bin/pip install <package>
# Then add to requirements.txt so it is reproducible
```

Never use a different conda environment (e.g. `kb-nav-agent`, `claude-llm`) as a workaround for a missing dependency — fix the project environment instead.

---

## Web Fetching — Use These Tools Only

**Never use WebFetch.** Use curl, wget, or Playwright only.

| Task | Tool |
| ---- | ---- |
| Public REST API (Semantic Scholar, arXiv API) | `curl` |
| File download (PDF, data) | `wget` or `curl -L -o file` |
| JS-rendered page, anonymous | `/fetch-page` skill (Playwright headless Chromium) |
| JS-rendered page, logged in | `/fetch-page-auth` skill (Playwright CDP to running Chrome) |
| Bot-protected download (ScienceDirect, Cloudflare) | `/fetch-page-chrome` skill (AppleScript → running Chrome) |

### Playwright environment

```bash
conda run -n afrikaans-aac python -c "from playwright.sync_api import sync_playwright; print('ok')"
```

Chromium binary: `~/Library/Caches/ms-playwright/`
User agent to use: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36`
JS wait: `time.sleep(5)` after `page.goto()` for React/Next.js sites.

For CDP (credentialed) access: Chrome must be running with `--remote-debugging-port=9222`. Check: `curl -s http://localhost:9222/json/version`.

---

## Literature Files — Naming Convention (CRITICAL)

Every file in `literature/papers/` and `literature/mkv/` **must** be named using
the BibTeX cite key from `literature/references.bib` as the filename stem:

```text
literature/papers/<cite-key>.pdf
literature/mkv/<cite-key>.md
```

`mkv/` = Markdown conversions of PDFs (full-text, used by verify-claims for
citation verification). The cite key is the single identifier that links the
BibTeX entry → PDF → Markdown conversion → author-year citation in `proposal/`.

**Full workflow and rationale:** see [literature/README.md](literature/README.md).

**Never** name files by journal article ID (e.g. `applsci-15-00524`), ERIC
accession number, or author-year variant. Always use the bib cite key.

Verify consistency before committing:

```bash
python3 -c "
import re; from pathlib import Path
bib = set(re.findall(r'^@\w+\{([^,\s]+),', Path('literature/references.bib').read_text(), re.MULTILINE))
print('PDFs not matching bib:', {p.stem for p in Path('literature/papers').glob('*.pdf')} - bib)
print('MKVs not matching bib:', {p.stem for p in Path('literature/mkv').glob('*.md')} - bib)
"
```

---

## PDF to Markdown Conversion

Use Bedrock streaming with `read_timeout=600` (the application inference profile ARN works; `invoke_model` times out but `invoke_model_with_response_stream` succeeds):

```bash
conda run -n afrikaans-aac python3 -c "
import boto3, base64, json
from pathlib import Path
from botocore.config import Config

client = boto3.client('bedrock-runtime', region_name='eu-west-1',
    config=Config(read_timeout=600, connect_timeout=60))
model_id = 'arn:aws:bedrock:eu-west-1:557116085116:application-inference-profile/vb6ydtnx7fbs'

pdf_b64 = base64.standard_b64encode(Path('literature/papers/<cite-key>.pdf').read_bytes()).decode('ascii')
body = json.dumps({
    'anthropic_version': 'bedrock-2023-05-31',
    'max_tokens': 64000,
    'messages': [{'role': 'user', 'content': [
        {'type': 'document', 'source': {'type': 'base64', 'media_type': 'application/pdf', 'data': pdf_b64}},
        {'type': 'text', 'text': 'Convert this academic paper to clean Markdown. Preserve all sections and headings. Render equations in LaTeX. Include all tables, figure captions, and footnotes. Do not summarise — output the full paper text verbatim.'}
    ]}]
})
response = client.invoke_model_with_response_stream(modelId=model_id, body=body)
chunks = []
for event in response['body']:
    chunk = json.loads(event['chunk']['bytes'])
    if chunk.get('type') == 'content_block_delta':
        chunks.append(chunk['delta'].get('text', ''))
text = ''.join(chunks)
Path('literature/mkv/<cite-key>.md').write_text(text, encoding='utf-8')
print(f'done — {len(text)} chars written')
"
```

Rate limit: 30,000 input tokens/minute. Convert sequentially with 65s gap if multiple large PDFs.

### ⛔ PyMuPDF (fitz) text extraction is NEVER acceptable for MKVs

**Do not use PyMuPDF, pdfminer, pdfplumber, or any other local PDF-to-text library to create MKV files.** These tools produce low-quality output: no semantic structure, broken hyphenation, lost equations, garbled tables, and positional text artifacts. An MKV created this way is useless for citation verification.

The two acceptable MKV conversion methods, in order of preference:

1. **Mistral OCR** (primary — default for all PDFs) — use `/mistral-ocr` skill or run directly:

   ```bash
   /opt/homebrew/Caskroom/miniconda/base/envs/afrikaans-aac/bin/python3 \
     scripts/mistral-ocr.py --cite-key <key>
   ```

   95% cheaper than Bedrock; handles copyright-blocked PDFs; auto-fixes unclosed fences,
   italic citations, heading levels. Full details: `docs/standards/research/pdf-acquisition.md`.

2. **Bedrock streaming** (fallback if Mistral API is down) — command below. Use
   `invoke_model_with_response_stream` with `read_timeout=600`.

If both fail: find an alternative PDF source (open access repository, author's page) and retry.
**Never create a PyMuPDF MKV** — a paper without an MKV cannot be cited.

### PDF acquisition fallback chain (before giving up)

If `wget`/`curl`, Anna's Archive MCP, and Sci-Hub all fail to produce a PDF (bot
detection, DOI misindex, paper too new):

1. **Check Unpaywall** for a direct OA PDF URL: `curl "https://api.unpaywall.org/v2/<doi>?email=hfoulds@gmail.com"` — check `best_oa_location.url_for_pdf`.
2. **Check arXiv** for a preprint: `curl "http://export.arxiv.org/api/query?search_query=au:<lastname>+AND+ti:<keyword>&max_results=5"`.
3. **Check DOAJ** for the publisher PII/URL: `curl "https://doaj.org/api/search/articles/doi:<doi>"` — check `bibjson.link[].url`.
4. **`/fetch-page-chrome`** — use AppleScript to instruct the running Chrome browser to navigate to the direct PDF URL (e.g. ScienceDirect `pdfft` URL). Chrome uses its own live session cookies and real TLS fingerprint, bypassing all bot detection. **Requires Chrome to be running.** This is the technique that successfully downloaded Li et al. 2025 (Computers and Education: AI) from ScienceDirect when all other methods failed (2026-03-26).

```bash
# Example for ScienceDirect (PII obtained from DOAJ step above):
osascript -e 'tell application "Google Chrome" to open location "https://www.sciencedirect.com/science/article/pii/<PII>/pdfft?isDTMRedir=true&download=true"'
sleep 8 && ls -t ~/Downloads/*.pdf | head -1
```

**No exceptions. A PyMuPDF MKV is worse than no MKV** because it creates a false impression that the paper has been properly processed.

---

## Repo Structure

```text
afrikaans-aac/
  admin/
    outreach/          — outreach emails (guarded: cite key + MKV required)
  docs/
    standards/
      coding/          — coding, CI/CD, docstring, error-handling standards
      logging/         — logging and telemetry standards
      research/
        pdf-acquisition.md      — PDF download and MKV conversion workflow
        radar-note-standard.md  — radar note schema and graduation steps
  image/               — app images / assets
  literature/
    img/               — figures extracted by Mistral OCR (<cite-key>/ subdirs)
    mkv/               — full-text Markdown conversions of PDFs (<cite-key>.md)
    papers/            — original PDFs (<cite-key>.pdf)
    radar/             — sources identified but not yet in formal pipeline
    reviews/           — literature review drafts
    references.bib     — BibTeX source of truth for all cite keys
    README.md          — full literature pipeline documentation
  notes/               — research notes and working documents
  proposal/
    business/          — business case / stakeholder proposals (guarded)
    research/          — research proposal sections (guarded)
  scripts/             — pipeline scripts (mistral-ocr, verify-claims, etc.)
  src/                 — PWA application source
  .claude/
    commands/          — slash command definitions
    scripts/           — citation integrity and fetch helper scripts
  environment.yml      — conda environment definition (name: afrikaans-aac)
  requirements.txt     — Python runtime dependencies
  requirements_dev.txt — Python dev dependencies (includes requirements.txt)
  Makefile             — setup, test, lint, format targets
```

---

## Literature Radar

`literature/radar/` holds sources that may be relevant but have not yet entered the
formal pipeline (`references.bib` → `literature/papers/` → `literature/mkv/`).

**Full standard:** [docs/standards/research/radar-note-standard.md](docs/standards/research/radar-note-standard.md)

### Adding a YouTube video to the radar

```bash
/transcribe-youtube <url> --relevance "<why relevant>"
```

Downloads audio, transcribes locally (MLX Whisper), generates summary and key
claims via Claude (Bedrock), writes `literature/radar/<slug>.md`.
    
### Adding a web article or other URL to the radar

Ask Claude: "add this to the radar: `<url>`". Claude will fetch the page, generate
the structured note, and save it. Or create the file manually using the schema in
[docs/standards/research/radar-note-standard.md](docs/standards/research/radar-note-standard.md).

### Status vocabulary (summary)

| Status | Meaning |
| --- | --- |
| `unread` | Identified, not yet watched/read |
| `skimmed` | Briefly scanned |
| `watched` | Fully watched/read, no synthesis yet |
| `processed` | Summary and key claims written (default after `/transcribe-youtube`) |
| `integrated` | `cite_key` set; bib entry exists; in `literature/index.md` |
| `archived` | Decided not relevant |

### Graduating a radar note to a formal citation

1. Add bib entry to `literature/references.bib`
2. For papers: get PDF → convert to mkv
3. Set `cite_key` in radar note frontmatter; set `status: integrated`
4. Add entry to `literature/index.md`
5. Rename file to `<cite-key>.md`

Radar notes are **never deleted** — they record the discovery history.

---

## Proposal Review Workflow

When asked to "review the proposal", "improve a section", "check citations", or
"create a new version of the proposal", execute phases 1–3 below autonomously
without stopping to ask for direction. Phase 4 requires JH and must be flagged
explicitly at the end.

Proposal files live under `proposal/research/` (research proposal sections) or
`proposal/business/` (business case / stakeholder documents). Adjust paths below
to match the actual filenames once sections are created.

### Full proposal-to-final-draft sequence

```text
Phase 1 — Fix structural skeleton  (autonomous)
  /coherence-check  →  apply all fixes per decision rules below  →  commit

Phase 2 — Improve all sections through the pipeline  (autonomous)
  /write-section proposal/research/01-introduction.md  →  accept back  →  commit
  /write-section proposal/research/02-research-questions.md  →  accept back  →  commit
  /write-section proposal/research/03-literature-review.md  →  accept back  →  commit
  /write-section proposal/research/04-methodology.md  →  accept back  →  commit
  /write-section proposal/research/05-timeline.md  →  accept back  →  commit

Phase 3 — Structural reduction pass  (autonomous)
  /coherence-check on fully improved proposal
  →  apply all fixes per decision rules below  →  commit

Phase 4 — Voice/length pass  (STOP — requires JH)
  Inform JH that phases 1–3 are complete and phase 4 requires human review.
  Present a summary of all changes made and any remaining flagged items.

Phase 5 — Produce PDF for review  (autonomous, after Phase 4)
  /to-latex --input proposal/research/01-introduction.md \
                    proposal/research/02-research-questions.md \
                    proposal/research/03-literature-review.md \
                    proposal/research/04-methodology.md \
                    proposal/research/05-timeline.md \
            --output pipeline-outputs/proposal.tex \
            --title "Afrikaans AAC for Post-Stroke Aphasia: A PhD Research Proposal" \
            --author "Johannes Foulds"
  /compile-latex --input pipeline-outputs/proposal.tex --open
  Default style: APA author-year (readable for review).
  For final submission: add --ref-style ieee to /to-latex.
```

Phase 3 is the substrate-to-draft mechanism. The pipeline expands sections 3–7×;
the post-improvement coherence check identifies what to cut on structural grounds
(repetition, content that belongs elsewhere), reducing the document to near-final
length without arbitrary trimming.

### Autonomous decision rules for coherence fixes

Apply these rules without asking for confirmation. They define safe autonomous
actions — no substantive argument is ever silently discarded.

**Repetition:**

- Identify which section is the correct home for the repeated content (the section
  where the argument is developed with full evidence and context).
- In the correct-home section: leave the content unchanged.
- In the duplicate section: replace with a concise cross-reference sentence
  (e.g. "As established in §3.3.2, infrastructure constraints favour BM25 as the
  primary retrieval component."). Do not delete — always leave a cross-reference.
- Exception: if the duplicate is a verbatim or near-verbatim copy AND the
  correct-home version is substantively more complete, the duplicate may be
  replaced with a single cross-reference sentence. If both versions contain
  unique content, merge into the correct-home section and cross-reference from
  the other.

**Transition breaks:**

- Add one bridging sentence at the section boundary. The sentence should move
  from the closing argument of the preceding section to the opening frame of the
  next. Do not alter the closing or opening sentences themselves.
- Add the bridging sentence as the last sentence of the preceding section's
  final paragraph, or as a new opening sentence before the block-quoted research
  question/chapter header if the break is at a chapter boundary.

**Argument spine consistency:**

- For contribution claim formulations: the §4 (Methodology) formulation is
  authoritative. Apply it consistently to §1 and §3 where the triad is stated.
- For terminology (e.g. "design principles" vs. "provisional hypotheses"):
  prefer the more specific and qualified term. Define it once in its first
  occurrence and use it uniformly thereafter.
- For scope inconsistencies (e.g. three vs. four experimental conditions): do
  not silently alter the research questions to match the methodology. Instead,
  add a clarifying sentence in the methodology explaining the relationship
  (e.g. "RQ2 identifies three retrieval configurations; the fourth experimental
  condition tests the generation component independently").

**Scope boundary violations:**

- If the offending passage exists verbatim or substantially in the correct
  section: remove it from the wrong section and replace with a one-sentence
  forward or back reference.
- If the offending passage does NOT exist in the correct section yet: move it
  to the correct section (insert at the appropriate location) and replace its
  original location with a cross-reference.
- Never delete content that does not exist in the correct section — always
  move it first, then cross-reference.

**What autonomous fixes never do:**

- Remove a substantive argument without replacing it with a cross-reference
- Change the meaning of a claim, only its location or cross-reference status
- Alter the research questions, objectives, or contribution claim without
  applying the §4-authoritative rule above
- Make any fix that is not directly supported by a specific coherence report item

### Coherence check invocation

```bash
/coherence-check --sections proposal/research/01-introduction.md \
                             proposal/research/02-research-questions.md \
                             proposal/research/03-literature-review.md \
                             proposal/research/04-methodology.md \
                             proposal/research/05-timeline.md
```

Produces `pipeline-outputs/coherence-report.md`. Run twice: Phase 1 (before
pipelining) and Phase 3 (after all sections improved).

### Improving a section (Phase 2 — one section at a time)

Invoke for each proposal file in order (01 through 05). Pass all other proposal
files as `--context`. Never omit `--context` — without it the reviser fabricates
content.

```bash
# Example: improving 01-introduction.md
/write-section --input proposal/research/01-introduction.md \
  --context proposal/research/02-research-questions.md \
             proposal/research/03-literature-review.md \
             proposal/research/04-methodology.md \
             proposal/research/05-timeline.md

# Example: improving 03-literature-review.md
/write-section --input proposal/research/03-literature-review.md \
  --context proposal/research/01-introduction.md \
             proposal/research/02-research-questions.md \
             proposal/research/04-methodology.md \
             proposal/research/05-timeline.md
```

The pipeline automatically:

1. Runs 2 critique-revision rounds (unisa + adversarial personas by default)
2. Polishes the revised text (language pass)
3. Runs `verify-claims` on the polished output with `--auto-fetch`
4. Runs a resolution pass to fix NEEDS_VERIFICATION / NO_SOURCE items using available mkv sources
5. Re-verifies and reports remaining items that need human attention

The final output is `pipeline-outputs/<section>-resolved.md` (or `-polished.md` if
all claims verified on the first pass). The verification report is
`pipeline-outputs/<section>-verification-report.md`.

### Accepting a pipeline output back into the proposal (autonomous)

After the pipeline completes for a section:

1. Read `pipeline-outputs/<section>-resolved.md` (or `-polished.md`)
2. For any remaining `[NEEDS VERIFICATION]` items: add a citation from
   `literature/mkv/`, qualify the claim, or remove the assertion — do not leave
   `[NEEDS VERIFICATION]` tags in the committed text
3. Replace the full content of the corresponding `proposal/` file with the
   accepted text (keep the file's existing filename and heading structure)
4. Run the bib consistency check:

```bash
python3 -c "
import re; from pathlib import Path
bib = set(re.findall(r'^@\w+\{([^,\s]+),', Path('literature/references.bib').read_text(), re.MULTILINE))
print('PDFs not matching bib:', {p.stem for p in Path('literature/papers').glob('*.pdf')} - bib)
print('MKVs not matching bib:', {p.stem for p in Path('literature/mkv').glob('*.md')} - bib)
"
```

### Verifying claims only (no improvement)

```bash
/verify-claims --context proposal/research/01-introduction.md \
               proposal/research/02-research-questions.md \
               proposal/research/03-literature-review.md \
               proposal/research/04-methodology.md \
               proposal/research/05-timeline.md \
               --auto-fetch
```

### Citation alerts during the pipeline

If the pipeline logs `CITATION ALERT — reviewer cited X not in references.bib`, that
paper is a potential literature gap. Decide whether to:

- Fetch it: `wget` or `curl -L -o literature/papers/<cite-key>.pdf <url>`, convert it
  (see PDF to Markdown Conversion below), add a bib entry
- Or explicitly acknowledge the gap in the text

---

## Key Decisions

- **PhD by Monograph** (safe default)
- **Research methodology:** UCD/AT or DSR (Hevner et al. 2004) — undecided; do not assume either until confirmed
- **Research artefact:** Progressive Web App (PWA) for a specific post-stroke aphasia user — Afrikaans-speaking, touchscreen tablet, fully offline, Edge TTS `af-ZA-WillemNeural`
- **Deployment status:** App is live and in active daily use
