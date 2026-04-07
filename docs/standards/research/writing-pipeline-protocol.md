# Multi-Model Academic Writing Pipeline — Protocol

> Last updated: 2026-03-17
> Status: Implemented and tested. See `scripts/writing-pipeline.py`, `scripts/coherence-check.py`,
> `.claude/commands/write-section.md`, and `.claude/commands/coherence-check.md`.

---

## 1. Purpose and Full Workflow

### 1.1 Pipeline purpose

This pipeline takes an **existing** proposal section and improves it through structured critique, revision, language polish, and citation verification. It does not draft from scratch — input is existing prose, output is improved prose.

### 1.2 Full proposal-to-final-draft sequence

The pipeline alone does not produce a final draft. It produces a verified, improved **substrate** — typically 3–7× the original word count because it addresses every critique item without a length constraint. The substrate is then reduced to near-final length via a post-improvement coherence check. This is the substrate-to-draft mechanism.

```text
Phase 1 — Fix structural skeleton (before any pipeline runs)
  /coherence-check on current proposal
  → targeted structural edits (repetition, transitions, scope violations)
  → commit clean baseline

Phase 2 — Improve all sections through the pipeline
  /write-section (section A) → accept back to proposal/research/
  /write-section (section B) → accept back to proposal/research/
  ... repeat for all sections ...

Phase 3 — Structural reduction pass (substrate → near-final length)
  /coherence-check on fully improved proposal
  → pipeline expansion re-introduces repetition and scope violations
  → coherence report provides structurally justified reasons to cut each passage
  → cuts reduce document to near-final length without arbitrary trimming

Phase 4 — Finalise
  Light voice/length pass per section → commit
```

**Why Phase 3 reduces length:** The pipeline expands sections by adding depth to every critique item, including items that belong in other sections. When the coherence check runs on the expanded substrate, it identifies those passages as scope violations ("this infrastructure analysis belongs in §3, not §1") or repetition ("this argument is already made in §3.8 — replace with a cross-reference"). Resolving those items removes the expansion that was structurally misplaced — without discarding any genuine argument.

**Why Phase 1 matters:** Running the coherence check before the pipeline means the pipeline improves structurally clean text. If §1.3 duplicates §3.8 before the pipeline runs, the pipeline will improve both copies — making the duplication worse and harder to untangle later.

The design is grounded in the empirical literature on LLM critique-revision:

- **Self-Refine (Madaan et al., 2023)**: iterative LLM refinement gives ~20% improvement over single-pass. Two rounds is the empirically justified cap before diminishing returns.
- **CriticBench (Yu et al., 2024)**: cross-model critique (different model for critic vs. generator) is empirically superior to self-critique.
- **Liang et al. (2023)**: GPT-4 reviewer feedback overlaps human reviewer feedback at 30–39% — comparable to human-human overlap. LLM critique is at human-reviewer quality for catching substantive weaknesses.
- **LLM-REVal (2025)**: LLM reviewers inflate scores for LLM-authored text. Mitigated by adversarial persona framing and anti-bias instruction.
- **Akpinar et al. (CHI 2026)**: human-edited LLM text > human-only > LLM-only in perceived quality. Human review after the pipeline is mandatory.

---

## 2. Pipeline Architecture

### 2.1 Steps

| Step | What happens | Model |
| ---- | ---- | ---- |
| 1 | Extract section from input file | — |
| 2–3 | Critique + revise (round 1) | Bedrock Sonnet 4.6 (reviewer + reviser) |
| 2–3 | Critique + revise (round 2) | Bedrock Sonnet 4.6 (different persona) |
| 4 | Language polish (+ optional style anchoring) | Bedrock Sonnet 4.6 (default) or Opus 4.6 (opt-in) |
| 5a | Verify claims on polished output | Bedrock Sonnet 4.6 via verify-claims.py |
| 5b | Resolution pass: fix flagged items | Bedrock Sonnet 4.6 |
| 5c | Re-verify resolved output | Bedrock Sonnet 4.6 |
| 6 | Human review | JH |

All steps default to AWS Bedrock — no personal API cost unless `--polisher-model claude-opus-4-6` is specified.

### 2.2 Output files

```text
pipeline-outputs/
  <section>-critique-r1.md       — critique, round 1
  <section>-revised-r1.md        — revised draft, round 1
  <section>-critique-r2.md       — critique, round 2
  <section>-revised-r2.md        — revised draft, round 2
  <section>-polished.md          — language-polished draft
  <section>-resolved.md          — FINAL: polished + verification-resolved (deliverable)
  <section>-verification-report.md  — claim-by-claim verification results
  <section>-verification-summary.md — one-line verdict per citation
```

If all claims verify on the first pass, `-resolved.md` is not produced and `-polished.md` is the deliverable.

---

## 3. Reviewer Personas

Four personas are implemented in `scripts/reviewer_personas.py`. Each produces genuinely differentiated critique — tested across multiple runs.

| Persona | Simulates | Best for |
| ---- | ---- | ---- |
| `unisa` | UNISA PhD examination committee (default round 1) | All sections — most relevant to actual submission |
| `adversarial` | Hostile examiner finding every weakness (default round 2) | Catches what unisa missed; surfaces ungrounded claims |
| `misq` | MIS Quarterly reviewer (rigour-relevance) | Methodology sections, DSR positioning |
| `irrodl` | IRRODL reviewer | ODeL context, literature review, implications sections |

### Persona rotation

Round 1: `--persona` (default: `unisa`)
Round 2: `--persona-r2` (default: next in rotation — `adversarial`)
Round 3+: continues rotating through `[unisa, adversarial, misq, irrodl]`

### Citation cross-check

After each critique, the pipeline parses the `PAPERS CITED IN THIS REVIEW` section (required structured output) and cross-references each cited paper against `references.bib`. Papers not in the bib are logged as `CITATION ALERT` — potential literature gaps worth investigating.

---

## 4. Fabrication Prevention

The reviser is instructed: if a critique item asks for a claim that cannot be grounded in an existing cited source, mark it `[NEEDS VERIFICATION]` rather than inventing content.

The verifier (`verify-claims.py`) uses **strong verification**: VERIFIED only if a specific, quotable passage in the mkv source directly supports the claim. General topic overlap is not sufficient.

The resolution pass then takes NEEDS_VERIFICATION / NO_SOURCE items and either:

- Rewrites the sentence to match what the source actually says (if an mkv file exists)
- Qualifies or scopes the claim (if no source is available)
- Marks it `[NEEDS VERIFICATION: <specific description of what evidence is needed>]` for human follow-up

---

## 5. Key Design Decisions

**`--context` is mandatory for PhD-level work.** Without it, the reviser fabricates content (in testing: invented a PRISMA Appendix A and a non-existent 7-database search protocol). With context, the reviser correctly flags fabrications as `[NEEDS VERIFICATION]`.

**`--target-words` is opt-in, not a default.** The auto-default (1.5× original) was removed after testing showed it silently dropped directional retrieval hypotheses, scope qualifications, and multi-component validation logic — all examinable content. For PhD work, review the expanded output and decide what belongs in this section vs. a later chapter.

**The resolution pass uses the mkv source files directly.** If `literature/mkv/<cite-key>.md` exists, the resolver is given the first 3,000 characters of the source and instructed to rewrite the flagged sentence to accurately reflect what the source says. Missing mkv files produce qualified claims rather than resolved ones — this is the correct behaviour.

**`pipeline-outputs/` is gitignored.** All pipeline outputs are ephemeral. Regenerate on demand. Commit only the final human-reviewed text back to `proposal/research/`.

---

## 6. Known Limitations

- **Significant expansion**: unconstrained runs expand a 332-word section to ~2,000–2,600 words. This often reflects genuinely examinable content (directional hypotheses, scope qualifications). Review and decide what to retain.
- **Adversarial persona overshoots**: finds real weaknesses but also pushes into over-critique. Apply judgement on which items to honour.
- **NEEDS_VERIFICATION after resolution**: some items remain flagged after the resolution pass — typically compound claims, researcher synthesis (correct behaviour), or claims requiring sources not in the bib. These require human follow-up.
- **Sci-Hub fetch failures**: `--auto-fetch` tries Sci-Hub for papers with DOIs. Paywalled papers without arXiv versions may not be fetchable. Add the PDF manually via `wget`/`curl` and convert via the Anthropic API (see CLAUDE.md).

---

## 7. Coherence Check

### 7.1 Purpose

Whole-document structural diagnosis. Reads all proposal sections in order. Produces a numbered report — no rewrites. Four dimensions:

| Dimension | What it catches |
| ---- | ---- |
| Repetition | Arguments/evidence explained twice when they should appear once |
| Transition breaks | Section boundaries where opening doesn't follow from preceding close |
| Argument spine consistency | Drift in research problem framing, scope, or terminology |
| Scope boundary violations | One section doing another section's job |

### 7.2 What it does NOT flag as problems

- Core research problem recurring across multiple sections (expected, not repetition)
- Key terms defined once then used freely (correct)
- Contribution claim in introduction + literature gap statement + methodology justification (structurally required)

### 7.3 Invoke

```bash
/coherence-check --sections proposal/research/01-introduction.md \
                             proposal/research/02-research-questions.md \
                             proposal/research/03-literature-review.md \
                             proposal/research/04-methodology.md \
                             proposal/research/05-timeline.md
```

Output: `pipeline-outputs/coherence-report.md`

---

## 8. Invoke

Via the Claude skill (recommended):

```bash
/write-section --input proposal/research/01-introduction.md \
  --context proposal/research/02-research-questions.md \
             proposal/research/03-literature-review.md \
             proposal/research/04-methodology.md \
             proposal/research/05-timeline.md
```

Direct script invocation:

```bash
conda run -n afrikaans-aac python scripts/writing-pipeline.py \
  --input proposal/research/01-introduction.md \
  --context proposal/research/02-research-questions.md \
            proposal/research/03-literature-review.md \
            proposal/research/04-methodology.md \
            proposal/research/05-timeline.md \
  [--persona misq] [--rounds 1] [--target-words 800] [--polisher-model claude-opus-4-6] \
  [--style-profile .style-profile.md]
```

---

## 9. Producing a PDF

After any review cycle, convert the proposal markdown to a compiled PDF:

```bash
# Step 1: convert to LaTeX (IEEE numeric default)
/to-latex --input proposal/research/01-introduction.md \
                  proposal/research/02-research-questions.md \
                  proposal/research/03-literature-review.md \
                  proposal/research/04-methodology.md \
                  proposal/research/05-timeline.md \
          --output pipeline-outputs/proposal.tex \
          --title "Afrikaans AAC for Post-Stroke Aphasia: A PhD Research Proposal" \
          --author "Johannes Foulds"

# For review (APA author-year — easier to read during drafting):
/to-latex ... --ref-style apa

# Step 2: compile and open
/compile-latex --input pipeline-outputs/proposal.tex --open
```

Available `--ref-style` options: `ieee` (default, numeric [1]), `apa` (author-year), `plainnat`, `unsrtnat`.

**Citation mechanism:** All citations in source markdown use pure Pandoc syntax:

- `@key` — narrative (author as grammatical subject): Pandoc emits `\citet{key}`
- `[@key]` — parenthetical: Pandoc emits `\citep{key}` via `--natbib`

Never type author names or years manually — Pandoc generates them from `literature/references.bib`.

**## References block:** Each source file ends with a human-review `## References` section
(`[@key] Full IEEE citation...`). This block is auto-generated by `generate-references-block.py`
and automatically stripped by `md-to-latex.py` before Pandoc conversion — it never reaches
the compiled PDF. The PDF bibliography comes from `\bibliography{references}` via BibTeX.

**Compiler:** The preamble uses `fontspec` and requires `lualatex` (not `pdflatex`).
The `/compile-latex` skill runs `lualatex → bibtex → lualatex → lualatex` automatically.

The script handles:

- Formatting (A4, 12pt, 1.5 spacing, 3cm left margin)
- Table captions and auto-numbering
- Landscape rotation for wide tables (>5 columns)
- Prompt blocks styled like NLP/AI arXiv papers (framed grey box, small monospace)
- `strip_references_block()` — strips the `## References` section before Pandoc conversion
- Section heading de-duplication (strips markdown numbers before LaTeX auto-numbers)

Output goes to `pipeline-outputs/` (gitignored — regenerate on demand).

---

## 10. Voice Anchoring — `--style-profile`

The language polish step (step 4) can be optionally anchored to a specific
academic writing style via **HyPerAlign-style hypothesis injection**. This is
implemented as a separate one-time extraction tool plus a pipeline flag.

### 10.1 How it works

1. **Run `scripts/extract-style-profile.py`** once on the exemplar paper
   (a paper whose writing style you want to emulate)

2. The extractor calls Bedrock with a HyPoGenic-methodology prompt to produce
   up to 10 specific, evidence-grounded stylistic hypotheses from the exemplar text.
   Each hypothesis is in `**[specific claim about the author's style]**: [evidence quote]` format.

3. The output `.style-profile.md` is a plain markdown file. **Inspect it before use.**
   Hypotheses should be specific enough that you could identify which paper they came from.
   Generic hypotheses ("the author writes clearly") indicate extraction failure — re-run.

4. **Pass `--style-profile .style-profile.md`** to the pipeline. The polish step receives
   the hypotheses as positive constraints on top of the standard academic style rules.

### 10.2 Extraction command

```bash
conda run -n afrikaans-aac python scripts/extract-style-profile.py \
  --input literature/mkv/<cite-key>.md \
  --output .style-profile.md \
  --context "<brief description of the exemplar paper's field and style>"
```

### 10.3 Design basis

Based on Garbacea & Tan (2025) HyPerAlign. Key properties confirmed in the paper:

- Works with as few as 4 short writing samples (>90% win-rate vs fine-tuning)
- Cross-model transfer is robust (extract with one model, apply with another)
- Inference-time only — no fine-tuning required
- 8,000 chars of exemplar text is well above the minimum required
