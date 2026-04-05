"""
extract-style-profile.py — HyPerAlign-style voice anchoring: extract specific,
evidence-grounded stylistic hypotheses from an exemplar academic paper (mkv
markdown) and write them to a reusable .style-profile.md file.

Based on the HyPoGenic methodology (Garbacea & Tan, arXiv:2505.00038v2, 2025):
hypotheses are propositional statements backed by direct quotations from the
exemplar text. The profile is consumed by writing-pipeline.py --style-profile.

Usage:
    conda run -n afrikaans-aac python scripts/extract-style-profile.py \\
        --input  literature/mkv/gregor-2020-design-principle.md \\
        --output .style-profile.md \\
        [--n-hypotheses 10] \\
        [--context "DSR methodology paper, JAIS, doctoral-level IS research"]

Output:
    .style-profile.md  — numbered list of stylistic hypotheses with evidence quotes
"""
import argparse
import os
import sys
from datetime import date
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
MAX_TOKENS = 4000

# HyPerAlign works with as few as 4 short writing samples; 8,000 chars of
# full-text mkv is well above that threshold and fits comfortably in one call.
EXEMPLAR_CHAR_LIMIT = 8000

EXTRACTION_SYSTEM_PROMPT = """\
You are an expert academic writing analyst applying the HypoGenic methodology \
for stylistic hypothesis extraction. Given an academic paper as input, your task \
is to generate N specific, evidence-grounded hypotheses that characterise the \
STYLISTIC PATTERNS of this author — not the content, not the argument, but the \
way the author writes at the sentence and paragraph level.

The hypotheses must be:
1. SPECIFIC to this author's observable style — not generic academic advice.
   BAD: "The author writes clearly." GOOD: "The author opens each paragraph \
with an explicit definitional claim before presenting supporting evidence."
2. EVIDENCE-GROUNDED: each hypothesis is backed by a direct quotation from the text.
3. ACTIONABLE: a writing model could apply this constraint directly to new text.
4. COVERING diverse stylistic dimensions, including but not limited to:
   - Sentence rhythm and clause complexity
   - Hedging and epistemic stance (how uncertainty is signalled)
   - Use of passive vs. active voice
   - Degree of explicitness in signposting and transitions
   - Paragraph opening patterns (definitional, problem-setting, forward-looking, etc.)
   - Use of meta-commentary (e.g. "We argue that...", "This paper shows...")
   - Register and formality calibration
   - How evidence is introduced and cited
   - Use of enumeration and bullet-style prose vs. flowing argument

Format each hypothesis EXACTLY as:
**[Specific claim about the author's style]**: [Direct evidence — verbatim quote from text]

Output ONLY the numbered list of hypotheses. No introduction, no conclusion, \
no preamble. Hypotheses should be ordered from most to least stylistically distinctive."""

EXTRACTION_USER_TEMPLATE = """\
Extract {n} stylistic hypotheses from the following academic paper.
Writing context: {context}

---
{exemplar_text}
---"""


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


def extract_hypotheses(
    exemplar_text: str,
    n: int,
    context: str,
    bedrock_client,
) -> str:
    """Call Bedrock to extract stylistic hypotheses from exemplar text."""
    # Trim to char limit — first N chars tend to be abstract + intro,
    # which are the most stylistically representative sections.
    trimmed = exemplar_text[:EXEMPLAR_CHAR_LIMIT]
    if len(exemplar_text) > EXEMPLAR_CHAR_LIMIT:
        print(
            f"[extract-style-profile] Exemplar text trimmed to first "
            f"{EXEMPLAR_CHAR_LIMIT:,} chars (full text: {len(exemplar_text):,} chars)",
            file=sys.stderr,
        )

    user_message = EXTRACTION_USER_TEMPLATE.format(
        n=n,
        context=context or "academic research paper",
        exemplar_text=trimmed,
    )

    response = bedrock_client.converse(
        modelId=BEDROCK_MODEL_ARN,
        system=[{"text": EXTRACTION_SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": user_message}]}],
        inferenceConfig={"maxTokens": MAX_TOKENS, "temperature": 0.3},
    )
    return response["output"]["message"]["content"][0]["text"]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_hypotheses(hypotheses_text: str, n: int) -> list[str]:
    """
    Parse the numbered list and return a list of warnings.
    Does not fail hard — a warning means the human should inspect the output.
    """
    warnings = []
    lines = [l.strip() for l in hypotheses_text.splitlines() if l.strip()]
    numbered = [l for l in lines if l and l[0].isdigit() and "." in l[:3]]

    if len(numbered) < n:
        warnings.append(
            f"Expected {n} hypotheses, found {len(numbered)} numbered items. "
            "The model may have produced fewer than requested."
        )

    for item in numbered:
        if "**" not in item:
            warnings.append(
                f"Item does not follow **[claim]**: [evidence] format: {item[:80]}"
            )
        # Flag generic/non-specific hypotheses
        generic_phrases = [
            "writes clearly", "is clear", "is well-written", "good writing",
            "uses proper", "appropriate language", "academic language",
        ]
        lower = item.lower()
        for phrase in generic_phrases:
            if phrase in lower:
                warnings.append(
                    f"Possibly generic (not specific to this author): {item[:80]}"
                )
                break

    return warnings


# ---------------------------------------------------------------------------
# Output file builder
# ---------------------------------------------------------------------------
def build_profile_file(
    hypotheses_text: str,
    input_path: Path,
    n: int,
) -> str:
    today = date.today().isoformat()
    header = (
        f"# Style Profile: {input_path.stem}\n"
        f"# Source: {input_path}\n"
        f"# Generated: {today}\n"
        f"# Model: Bedrock Sonnet 4.6 (via extract-style-profile.py)\n"
        f"# N hypotheses: {n}\n"
        f"#\n"
        f"# USAGE: pass to writing-pipeline.py via --style-profile <this file>\n"
        f"# The polish step will apply these hypotheses as positive style constraints.\n"
        f"# INSPECT before use: hypotheses should be specific, evidence-grounded,\n"
        f"# and clearly derived from this particular paper's writing style.\n"
        f"\n---\n\n"
    )
    return header + hypotheses_text.strip() + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Extract HyPerAlign-style stylistic hypotheses from an exemplar "
            "academic paper (mkv markdown) for voice anchoring in the writing pipeline."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        metavar="FILE",
        help="Path to an mkv markdown file (full-text conversion of an exemplar paper).",
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="FILE",
        help="Path to write the .style-profile.md output file.",
    )
    parser.add_argument(
        "--n-hypotheses",
        type=int,
        default=10,
        dest="n_hypotheses",
        metavar="N",
        help=(
            "Number of stylistic hypotheses to extract. "
            "HyPerAlign uses up to 10. Default: 10."
        ),
    )
    parser.add_argument(
        "--context",
        default="",
        metavar="TEXT",
        help=(
            "Free-text description of the writing context "
            "(e.g. 'DSR methodology paper, JAIS, doctoral-level IS research'). "
            "Helps orient hypotheses toward the target genre."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    repo_root = Path(__file__).parent.parent
    load_env(repo_root)

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"ERROR: input file not found: {input_path}")

    output_path = Path(args.output)

    exemplar_text = input_path.read_text(encoding="utf-8")
    word_count = len(exemplar_text.split())
    print(
        f"[extract-style-profile] Input: {input_path} "
        f"({word_count:,} words, {len(exemplar_text):,} chars)",
        file=sys.stderr,
    )
    print(
        f"[extract-style-profile] Extracting {args.n_hypotheses} hypotheses...",
        file=sys.stderr,
    )

    bedrock_client = make_bedrock_client()
    hypotheses_text = extract_hypotheses(
        exemplar_text=exemplar_text,
        n=args.n_hypotheses,
        context=args.context,
        bedrock_client=bedrock_client,
    )

    # Validate
    warnings = validate_hypotheses(hypotheses_text, args.n_hypotheses)
    if warnings:
        print("[extract-style-profile] WARNINGS — please inspect output:", file=sys.stderr)
        for w in warnings:
            print(f"  ! {w}", file=sys.stderr)
    else:
        print(
            f"[extract-style-profile] Validation passed — {args.n_hypotheses} "
            "well-formed hypotheses extracted.",
            file=sys.stderr,
        )

    # Write output
    profile_content = build_profile_file(hypotheses_text, input_path, args.n_hypotheses)
    output_path.write_text(profile_content, encoding="utf-8")
    print(f"[extract-style-profile] Profile written to {output_path}", file=sys.stderr)

    # Print to stdout for inspection
    print(profile_content)


if __name__ == "__main__":
    main()
