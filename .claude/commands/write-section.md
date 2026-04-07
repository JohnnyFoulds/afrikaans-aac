# write-section (improve-section)

Run the multi-model academic writing improvement pipeline on an existing proposal section.

> **Note on naming:** This tool is misnamed. It does not *write* a section from scratch — it *improves* an existing one. A more accurate name would be `improve-section` or `revise-section`. The name `write-section` is retained for compatibility with existing workflow instructions, but the mental model is: *input is existing prose → output is improved prose*.

Takes an existing section from `proposal/` and improves it through:

1. Structured critique — default: Bedrock Sonnet 4.6 (reviewer persona); override to GPT-4o with `--reviewer-model gpt-4o`
2. Claude Sonnet 4.6 (Bedrock) revision incorporating the critique
3. Repeat for N rounds with a different reviewer persona each time
4. Language polish — default: Bedrock Sonnet 4.6; override to Opus with `--polisher-model claude-opus-4-6`

**All steps default to AWS Bedrock — no personal API cost unless you explicitly override.**

**Usage:** `/write-section --input <file> [options]`

**Required:**

- `--input <path>` — path to the markdown file being improved (e.g. `proposal/01-introduction.md`)

**Options:**

- `--section <id>` — section ID to extract (e.g. `1.2` matches `## 1.2 Background...`). If omitted, the entire file is processed.
- `--context <file> [<file> ...]` — one or more markdown files providing proposal context, in logical order. The reviewer and reviser use these to avoid introducing claims that contradict the rest of the proposal. Typically all proposal files except the one being revised. **Strongly recommended — see quality findings below.**
- `--persona <name>` — reviewer persona for round 1. Default: `unisa`. Choices: `unisa`, `adversarial`, `misq`, `irrodl`
- `--persona-r2 <name>` — reviewer persona for round 2. Default: next in rotation after `--persona`
- `--rounds <n>` — number of critique-revision cycles. Default: `2`. Range: 1–4
- `--target-words <n>` — word count ceiling for the revised and polished output. **Default: omitted = unconstrained.** When omitted, the reviser addresses all critique items without a word budget and output may expand significantly — but no arguments are silently dropped. Use this flag only when you know the section must stay within a fixed length (e.g. a journal word limit). For PhD proposal work, omit it and review the expanded output manually to decide which arguments belong here vs. in a later chapter.
- `--style-profile <file>` — path to a `.style-profile.md` produced by `scripts/extract-style-profile.py`. If provided, the language polish step is additionally constrained by specific stylistic hypotheses extracted from the chosen exemplar paper (HyPerAlign-style voice anchoring). Omit for generic academic style rules only. See `notes/voice-and-llm-writing.md` §8 for background.
- `--output-dir <path>` — output directory. Default: `pipeline-outputs/`

## Persona descriptions

| Persona | Simulates | Best for |
| --- | --- | --- |
| `unisa` | UNISA PhD examination committee member | Default — most relevant for the actual submission |
| `adversarial` | Hostile examiner finding every weakness | Round 2 by default — catches what `unisa` missed |
| `misq` | MIS Quarterly reviewer (DSR rigour-relevance framework) | Methodology sections, DSR positioning |
| `irrodl` | IRRODL reviewer | ODeL context, literature review, implications sections |

## Output files

All output goes to `--output-dir` (default: `pipeline-outputs/`):

```text
<section>-critique-r1.md    — critique, round 1
<section>-revised-r1.md     — revised draft after round 1
<section>-critique-r2.md    — critique, round 2
<section>-revised-r2.md     — revised draft after round 2
<section>-polished.md       — FINAL: language polish (the deliverable)
```

## Quality evaluation findings

Tested on a 332-word proposal section with 2 rounds, full context, and all four personas.

**What it does well:**

- **Argument depth**: The critique accurately identifies genuine weaknesses — unsupported "no prior study" claims, logical gaps in compound arguments, single-source dependencies. These are real issues, not noise.
- **Cross-chapter consistency (`--context` matters)**: With context supplied, the reviser correctly respects constraints from other chapters (e.g. if §4.1 states offline operation is not a design requirement, the revised §1.3 reflects this). Without context, the reviser re-introduces scope claims that other chapters disclaim.
- **Citation expansion is safe**: The reviser adds citations drawn from the proposal context that are appropriate and already present elsewhere. It never invents a new author or fabricates a reference.
- **`[NEEDS VERIFICATION]` markers work**: Items the reviser cannot ground in a cited source are correctly flagged (3–4 per run). These mark genuinely unverified claims — search protocol statements, infrastructure assumptions — that require human follow-up.
- **Polisher cleans without corrupting**: Removes revision log, trims word count slightly, eliminates LLM tells. Does not alter argument structure or citations.
- **Personas are genuinely differentiated**: IRRODL uniquely raised the missing student perspective; MISQ emphasised DSR rigour and theoretical grounding; UNISA focused on doctoral contribution framing. Each surfaces critique the others miss.

**Known limitations:**

- **Significant expansion**: Without `--target-words`, a 332-word section expanded to ~2,600 words after 2 rounds. The expansion often contains genuinely examinable content — directional retrieval hypotheses, scope qualifications, three-component validation logic — that should not be silently discarded. Review the expanded output and decide which arguments belong in this section vs. a later chapter. Use `--target-words` only when you have a hard length constraint and understand the trade-off.
- **No context = drift**: Without `--context`, one run introduced a fabricated PRISMA Appendix A and a non-existent 7-database search protocol, asserted as facts. The same run with `--context` correctly flagged these as `[NEEDS VERIFICATION]`. **Always use `--context`.**
- **Adversarial round 2 overshoots**: The round-2 adversarial critique finds real weaknesses but also pushes into persona-driven over-critique. Apply judgement on which items to honour.
- **Polished output is a substrate, not a final draft**: `[NEEDS VERIFICATION]` items require real follow-up. Some resolve by adding a citation; others require a scope acknowledgement or primary research.

**Recommended workflow:**

1. Always pass `--context` with all other proposal chapters.
2. Use `unisa` + `adversarial` (default) for general sections; `misq` for methodology, `irrodl` for ODeL-context sections.
3. After the pipeline: resolve every `[NEEDS VERIFICATION]` item — add a citation, qualify the claim, or remove the assertion.
4. Run `/verify-claims` on the polished output before committing.

## After the pipeline runs

1. Read `<section>-polished.md` — this is the improved version
2. Make targeted human edits where:
   - `[NEEDS VERIFICATION]` items require a real citation or scope qualification
   - Your intended argument was distorted or over-specified during revision
   - Specific phrasings conflict with your voice or terminology
3. The human+LLM hybrid is rated highest by expert readers (CHI 2026 study)

## Execute

```bash
python /Users/johannes/code/personal/afrikaans-aac/scripts/writing-pipeline.py $ARGUMENTS
```

After the script completes, read the polished output file and present it to the user. Then remind them to do Step 6: targeted human review before the section is considered final.

## Example

```bash
/write-section --input proposal/01-introduction.md --section 1.2
/write-section --input proposal/03-literature-review.md --section 3.4 --persona misq --rounds 1
/write-section --input proposal/04-methodology.md --persona adversarial --persona-r2 unisa
/write-section --input proposal/01-introduction.md --section 1.3 --target-words 600
/write-section --input proposal/01-introduction.md --style-profile .style-profile.md
```
