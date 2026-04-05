# coherence-check

Run a whole-document structural coherence check on the PhD proposal.

Reads all proposal sections in order and produces a structured report identifying:

1. **Repetition** — arguments, claims, or explanations appearing more than once when they should appear only once (not counting legitimate recurrence of the core problem, contribution claim, or key terms)
2. **Transition breaks** — section boundaries where the opening sentence of the new section does not follow naturally from the close of the preceding one
3. **Argument spine consistency** — drift in the framing, scope, or terminology of the core research problem or contribution claim across sections
4. **Scope boundary violations** — one section doing another section's job (e.g. literature review pre-empting methodology decisions)

**Does NOT rewrite anything.** Output is a numbered report of specific, actionable issues. You decide which to action; Claude executes targeted edits.

---

**Usage:** `/coherence-check [options]`

**Options:**

- `--sections <file> [<file> ...]` — proposal files in order. Default: all five `proposal/` files in sequence.
- `--section-under-review <id>` — section ID recently revised (e.g. `1.3`). The model pays particular attention to how it fits its neighbours.
- `--output-dir <path>` — output directory. Default: `pipeline-outputs/`

**Typical invocation (full proposal):**

```bash
/coherence-check --sections proposal/01-introduction.md \
                             proposal/02-research-questions.md \
                             proposal/03-literature-review.md \
                             proposal/04-methodology.md \
                             proposal/05-timeline.md
```

**After revising a specific section:**

```bash
/coherence-check --sections proposal/01-introduction.md \
                             proposal/02-research-questions.md \
                             proposal/03-literature-review.md \
                             proposal/04-methodology.md \
                             proposal/05-timeline.md \
  --section-under-review 1.3
```

---

## When to run

- After the writing pipeline has produced a revised section and you have accepted it back into `proposal/`
- Before a supervisor review — catch structural issues before they do
- After adding or substantially rewriting multiple sections

## After the report

Read `pipeline-outputs/coherence-report.md`. For each numbered item:

- **Repetition**: decide which instance stays, replace the other with a cross-reference (e.g. "as established in §1.2")
- **Transition break**: add one bridging sentence at the boundary — tell Claude exactly what the bridge should say
- **Argument spine**: pick the correct framing and apply it consistently — tell Claude which instance is authoritative
- **Scope violation**: move or remove the misplaced passage — tell Claude which section it belongs in

Then ask Claude to execute those specific edits.

## Execute

```bash
conda run -n afrikaans-aac python /Users/johannes/code/unisa/unisa-phd-proposal/scripts/coherence-check.py $ARGUMENTS
```

After the script completes, read `pipeline-outputs/coherence-report.md` and present the findings to the user, organised by dimension. Ask which items to action.
