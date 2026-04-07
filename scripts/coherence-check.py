"""
coherence-check.py — Whole-document structural coherence checker for the
RAG-for-ODL PhD proposal.

Reads all proposal sections in order and produces a structured report
identifying: repetition, transition breaks, argument spine consistency,
and scope boundary violations. Does NOT rewrite anything.

Usage:
    python scripts/coherence-check.py \\
        --sections proposal/01-introduction.md \\
                   proposal/02-research-questions.md \\
                   proposal/03-literature-review.md \\
                   proposal/04-methodology.md \\
                   proposal/05-timeline.md \\
        [--output-dir pipeline-outputs/]
        [--section-under-review 1.3]   # highlight one recently revised section

Output:
    <output-dir>/coherence-report.md   — full structured report
"""
import argparse
import os
import sys
from pathlib import Path

try:
    import boto3
    from botocore.config import Config as BotocoreConfig
except ImportError:
    sys.exit("ERROR: boto3 not installed. Run: pip install boto3")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BEDROCK_REGION = "eu-west-1"
BEDROCK_MODEL_ARN = (
    "arn:aws:bedrock:eu-west-1:557116085116:"
    "application-inference-profile/vb6ydtnx7fbs"
)
MAX_TOKENS = 6000

SYSTEM_PROMPT = """\
You are a senior academic editor reviewing a PhD research proposal for internal \
structural coherence. Your sole task is to identify structural problems in the \
document — you are NOT asked to rewrite, improve the argument, or assess quality.

The proposal follows Design Science Research methodology and targets UNISA PhD \
examination. It has five sections: Introduction, Research Questions, Literature \
Review, Methodology, and Timeline/Gantt.

You will be given the full proposal text. Analyse it for the four structural \
dimensions below and produce a numbered report. Be specific — quote the \
exact sentence or phrase at issue and state exactly where it appears.

Do not comment on writing quality, citation completeness, or argument strength. \
Those are handled in separate passes. Focus exclusively on structure.

---

DIMENSION 1 — REPETITION
Identify arguments, claims, or explanations that appear more than once across \
sections where they should appear only once. Note: legitimate recurrence of the \
core research problem, key definitions (first formal use then free use), and the \
contribution claim across introduction/literature gap/methodology justification \
is EXPECTED — do not flag these. Flag only: identical or near-identical sentences \
copied across sections; evidence cited to make the same point twice; concepts \
re-explained at length after already being explained in full.

DIMENSION 2 — TRANSITION BREAKS
For each section boundary, assess whether the opening sentence of the new section \
follows naturally from the closing argument of the preceding section. Flag breaks \
where the reader would experience a jarring shift with no bridging sentence.

DIMENSION 3 — ARGUMENT SPINE CONSISTENCY
The core research problem, research questions, and proposed contribution must be \
stated consistently throughout. Flag any instance where the framing, scope, or \
key terminology drifts across sections (e.g. the problem is stated as X in §1 but \
implicitly as Y in §3, or the contribution claim changes between introduction and \
methodology).

DIMENSION 4 — SCOPE BOUNDARY VIOLATIONS
Flag instances where one section is doing another section's job: literature review \
pre-empting methodology decisions; introduction pre-empting literature review \
conclusions; methodology repeating background already established in the literature \
review; timeline section making claims that belong in methodology.

---

Structure your response EXACTLY as follows:

COHERENCE REPORT

OVERALL ASSESSMENT: [Well-structured / Minor issues / Significant structural problems]

REPETITION:
[Numbered list. For each item: quote the repeated phrase/sentence, state which \
sections it appears in, state which instance should be kept and which removed or \
replaced with a cross-reference. If none: write "none identified."]

TRANSITION BREAKS:
[Numbered list. For each item: name the section boundary (e.g. §1 → §2), quote \
the closing sentence of §1 and the opening sentence of §2, explain why the \
transition breaks, and suggest what kind of bridging sentence is needed (one \
sentence description — do not write the sentence). If none: write "none identified."]

ARGUMENT SPINE CONSISTENCY:
[Numbered list. For each item: quote the two conflicting framings, state where \
each appears, and describe the inconsistency precisely. If none: write "none identified."]

SCOPE BOUNDARY VIOLATIONS:
[Numbered list. For each item: quote the offending passage, state which section \
it appears in, state which section it belongs in instead, and explain why it is \
misplaced. If none: write "none identified."]

ITEMS REQUIRING NO ACTION:
[List any structural choices that might look like problems but are intentional and \
correct — e.g. deliberate recurrence of the core research problem.]"""


CHECKER_PROMPT_TEMPLATE = """\
Below is the full text of a PhD research proposal. Analyse it for structural \
coherence as instructed.{highlight}

---

{proposal_text}"""


# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------
def load_env(repo_root: Path) -> None:
    env_file = repo_root / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


# ---------------------------------------------------------------------------
# Bedrock call
# ---------------------------------------------------------------------------
def make_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=BEDROCK_REGION,
        config=BotocoreConfig(read_timeout=300, connect_timeout=10),
    )


def run_coherence_check(proposal_text: str, section_under_review: str | None, bedrock_client) -> str:
    highlight = ""
    if section_under_review:
        highlight = (
            f"\n\nNote: section {section_under_review} was recently revised — "
            f"pay particular attention to how it fits its neighbours."
        )

    user_message = CHECKER_PROMPT_TEMPLATE.format(
        highlight=highlight,
        proposal_text=proposal_text,
    )

    response = bedrock_client.converse(
        modelId=BEDROCK_MODEL_ARN,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": user_message}]}],
        inferenceConfig={"maxTokens": MAX_TOKENS, "temperature": 0.3},
    )
    return response["output"]["message"]["content"][0]["text"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Whole-document structural coherence checker for the PhD proposal."
    )
    parser.add_argument(
        "--sections",
        nargs="+",
        required=True,
        metavar="FILE",
        help="Proposal section files in order (e.g. proposal/01-introduction.md ...)",
    )
    parser.add_argument(
        "--output-dir",
        default="pipeline-outputs",
        metavar="DIR",
        help="Directory for the coherence report. Default: pipeline-outputs/",
    )
    parser.add_argument(
        "--section-under-review",
        default=None,
        metavar="ID",
        help="Section ID recently revised (e.g. 1.3) — highlighted in the prompt.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    repo_root = Path(__file__).parent.parent
    load_env(repo_root)

    # Assemble proposal text
    parts = []
    for path_str in args.sections:
        p = Path(path_str)
        if not p.exists():
            sys.exit(f"ERROR: file not found: {p}")
        text = p.read_text(encoding="utf-8")
        parts.append(f"# FILE: {p.name}\n\n{text}")
    proposal_text = "\n\n---\n\n".join(parts)

    word_count = len(proposal_text.split())
    print(f"[coherence-check] Full proposal: {word_count:,} words across {len(parts)} sections", file=sys.stderr)

    # Output dir
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run check
    print("[coherence-check] Running structural coherence analysis...", file=sys.stderr)
    bedrock_client = make_bedrock_client()
    report = run_coherence_check(proposal_text, args.section_under_review, bedrock_client)

    # Save
    report_path = output_dir / "coherence-report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"[coherence-check] Report written to {report_path}", file=sys.stderr)

    # Print to stdout as well
    print(report)

    # Exit code
    lower = report.lower()
    if "significant structural problems" in lower:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
