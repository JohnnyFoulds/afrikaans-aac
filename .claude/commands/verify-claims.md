# verify-claims

Run strong, tier-aware citation verification on one or more proposal files.

For each citation found in the `--context` files, the tool:
1. Resolves the author-year citation to an entry in `literature/references.bib`
2. Locates the corresponding markdown conversion in `literature/mkv/`
3. If `--auto-fetch` is set and no mkv file exists, attempts to download the PDF (arXiv/DOI) and convert it via the Anthropic API
4. Classifies the claim as T1_EMPIRICAL / T2_SYNTHESIS / T3_APPLICATION (Option C, two-call)
5. Sends the claim + source text to **Bedrock Haiku 4.5** with a tier-specific verification prompt
6. Outputs a full report with VERIFIED / NEEDS_VERIFICATION / NO_SOURCE per citation

**Default backend: Bedrock Haiku 4.5** (HAIKU_ARN from .env). ~$0.0075/claim. No personal API cost.

**Usage:** `/verify-claims --context <file> [<file> ...] [options]`

**Required:**
- `--context <file> [<file> ...]` — one or more proposal markdown files to check. Typically all proposal files.

**Options:**
- `--bib <path>` — path to BibTeX database. Default: `literature/references.bib`
- `--mkv-dir <path>` — directory of markdown paper conversions. Default: `literature/mkv/`
- `--output-dir <path>` — where to write reports. Default: `pipeline-outputs/`
- `--auto-fetch` — if a paper has no mkv file, try to download it (arXiv PDF or Sci-Hub via DOI) and convert via Anthropic API. Adds ~65s per missing paper (API rate limit). Use when running a full pre-submission audit.
- `--backend bedrock|openai|local` — LLM backend. Default: `bedrock`
- `--model <model_id>` — model ID or ARN. Default: HAIKU_ARN from .env (Bedrock), `gpt-4o` (OpenAI), `Qwen3.5-35B-A3B` (local)
- `--local-url <url>` — base URL for local backend. Default: `http://dragon:8080`
- `--tier-aware` — enable tier-aware verification (default: on via `--tier-architecture C`)
- `--tier-architecture A|B|C` — verification architecture. Default: `C` (classify → tier-specific template)
- `--pipeline two-stage` — run Qwen35 Arch C first (free); escalate NO_SOURCE verdicts to Haiku Arch C. Best cost/accuracy tradeoff (~$0.68 per 150-claim pass). Requires `--backend local` to be reachable.

**Recommended invocations:**

```bash
# Standard: Haiku Arch C (best verified cost/accuracy — $0.0075/claim)
/verify-claims --context proposal/01-introduction.md ... --auto-fetch

# Free option: local Qwen35 Arch C (requires Dragon running at http://dragon:8080)
/verify-claims --context proposal/01-introduction.md ... --backend local --model Qwen3.5-35B-A3B --local-url http://dragon:8080 --tier-aware --tier-architecture C

# Two-stage pipeline: Qwen35 first, Haiku escalation on NO_SOURCE (~$0.68/150-claim pass)
/verify-claims --context proposal/01-introduction.md ... --pipeline two-stage
```

## Verification standard

**Strong verification** is used. A citation is VERIFIED only if:
- The mkv source text contains a specific, verbatim-quotable passage that directly supports the exact claim being made in the proposal.

Logical inference, general topic overlap, or "the paper is about X and the claim is about X" is **not** sufficient for VERIFIED. Those cases return NEEDS_VERIFICATION.

## Output files

All output goes to `--output-dir` (default: `pipeline-outputs/`):

```
verification-report.md   — full report: claim sentence, verdict, supporting quote, reasoning per citation
verification-summary.md  — one-line table: cite key | raw citation | verdict | confidence
```

## Verdicts

| Verdict | Meaning |
|---------|---------|
| `VERIFIED` | A specific quotable passage directly supports the claim |
| `NEEDS_VERIFICATION` | Source is relevant but no passage directly supports the exact claim |
| `NO_SOURCE` | Source text does not address the claim, or citation unresolved in .bib |
| `SKIPPED` | No mkv file found and --auto-fetch not used or failed |

## Interpreting results — what the verdicts actually mean in practice

Tested against 28 cases (8 genuinely-supported claims, 8 fabrications, 8 nuanced PhD-level claims, 4 wrong-source cases). Key findings:

**What it catches reliably:**

- Invented statistics and specific numbers attributed to a paper (100% catch rate)
- Claims attributed to the wrong paper (100% catch rate)
- Completely fabricated assertions not related to the source topic (100% catch rate)

**Known behavioural pattern — researcher synthesis:**
When a claim in the proposal is the researcher's own synthesis or application of a source (e.g., "CLT explains why RAG addresses the right problem"), the tool returns NEEDS_VERIFICATION or NO_SOURCE. This is correct behaviour — Sweller (1994) says nothing about RAG. The synthesis is yours, not his. These flags are not bugs; they identify where you need to own the inference explicitly in the text rather than implying it is directly sourced.

**Known behavioural pattern — compound claims:**
If a single sentence makes two claims (e.g., "RAGAS provides X — but has not been applied to Y"), the tool verifies the full sentence against one source. The second half of a compound claim will nearly always produce NEEDS_VERIFICATION even if the first half is verified. Split compound claims across sentences before verifying if you want clean VERIFIED results.

**Known behavioural pattern — soft NO_SOURCE on contradicted claims:**
If a fabricated claim is clearly contradicted by the source (rather than simply absent from it), the tool may return NEEDS_VERIFICATION rather than NO_SOURCE. Both verdicts require human review — treat them identically.

**What VERIFIED means:** A specific, quotable passage in the source directly supports the claim. You can cite it with confidence.

**What NEEDS_VERIFICATION means:** Investigate — do not assume the claim is wrong. Check whether (a) the sentence is researcher synthesis (own it), (b) the claim is split across two papers and needs restructuring, or (c) there is a genuine accuracy problem.

**What NO_SOURCE means:** The source does not address the claim at all, or the citation was not resolved. Check whether the citation is correct before assuming the claim is wrong.

## When to run

Run this **before** submitting a revised section or the full proposal. It is the defence against plausible-sounding fabrications introduced during the critique-revision pipeline.

Typical workflow:
1. Run `/write-section` to improve a section
2. Run `/verify-claims` on the revised file + rest of proposal
3. Fix any NEEDS_VERIFICATION or NO_SOURCE items before committing

## Execute

Tier-aware Arch C is the default — no extra flags needed. The script defaults to `--tier-aware --tier-architecture C` unless overridden.

```bash
conda run -n claude-llm python /Users/johannes/code/unisa/unisa-phd-proposal/scripts/verify-claims.py $ARGUMENTS
```

After the script completes:
1. Read `pipeline-outputs/verification-report.md`
2. Present a summary to the user: counts of VERIFIED / NEEDS_VERIFICATION / NO_SOURCE / SKIPPED
3. For any NEEDS_VERIFICATION or NO_SOURCE items: quote the claim sentence and reasoning, and advise the user on whether to fix the claim, add a supporting source, or remove the unsupported assertion
4. For SKIPPED items: advise the user to either run with `--auto-fetch` or manually add the paper to `literature/mkv/`

## Standard file list

The files that contain citable claims in this repo:

```
proposal/01-introduction.md
proposal/02-research-questions.md
proposal/03-literature-review.md
proposal/04-methodology.md
proposal/05-timeline.md
admin/research-outline/research-outline.md
```

## Example

```bash
# Full proposal + research outline audit (Haiku Arch C — recommended, ~$0.20)
/verify-claims --context proposal/01-introduction.md proposal/02-research-questions.md proposal/03-literature-review.md proposal/04-methodology.md proposal/05-timeline.md admin/research-outline/research-outline.md --auto-fetch

# Single section
/verify-claims --context proposal/01-introduction.md --auto-fetch

# Two-stage pipeline (Qwen35 free + Haiku escalation — Dragon must be running)
/verify-claims --context proposal/03-literature-review.md --pipeline two-stage --auto-fetch
```
