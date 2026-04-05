"""
apply-style-profile.py — Standalone voice anchoring tool.

Takes any markdown text file and a .style-profile.md produced by
extract-style-profile.py, and applies the stylistic hypotheses as a
polish pass using Bedrock Sonnet 4.6 (or Opus 4.6 via Anthropic direct).

This is a completely independent tool — it has no dependency on the
writing pipeline. Use it:
  - Directly on any text (proposal sections, drafts, standalone paragraphs)
  - After a pipeline run, as an additional style pass on the polished output
  - On JH's own writing samples to check how the exemplar style compares

Usage:
    conda run -n kb-nav-agent python scripts/apply-style-profile.py \\
        --input   proposal/01-introduction.md \\
        --profile .style-profile.md \\
        --output  pipeline-outputs/01-introduction-styled.md \\
        [--section "1.2"] \\
        [--model bedrock|claude-opus-4-6]

Output:
    <output> — style-anchored version of the input text
"""
import argparse
import os
import re
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
MAX_TOKENS = 8000

STYLE_BLOCK_INTRO = (
    "\n\nSTYLE PROFILE — APPLY THESE CONSTRAINTS:\n"
    "The following are specific, evidence-grounded stylistic hypotheses "
    "extracted from a chosen exemplar paper using the HyPoGenic methodology. "
    "Apply them as POSITIVE constraints — write in a way that is consistent "
    "with these patterns. Do not imitate the exemplar's content; only its "
    "stylistic patterns. These constraints supplement (do not replace) the "
    "standard academic style rules listed below.\n\n"
)


def build_style_block(style_hypotheses: str) -> str:
    """
    Return the style-profile injection block for a system prompt.
    Returns an empty string when style_hypotheses is empty.
    Importable by writing-pipeline.py so the block is defined once.
    """
    if not style_hypotheses or not style_hypotheses.strip():
        return ""
    return STYLE_BLOCK_INTRO + style_hypotheses.strip()


SYSTEM_PROMPT_TEMPLATE = """\
You are an expert academic writing editor specialising in British Academic \
English at doctoral level. Your task is a style-only pass — you must NOT \
change the substance, argument structure, citations, or content in any way.\
{style_block}

Standard style rules:
- Vary sentence length and rhythm naturally — avoid monotonous cadence.
- Calibrate hedging language: use 'suggests', 'appears to', \
'is consistent with', 'the evidence indicates' rather than overclaiming \
or underclaiming.
- Eliminate detectable LLM writing tells: no 'it is worth noting', \
'delve into', 'shed light on', 'in the realm of', 'it is important to', \
'underscore', 'robust' (overused).
- Minimise em-dash overuse — use sparingly.
- Balance passive and active voice appropriate to academic register.
- Do NOT change any argument, claim, or factual statement.
- Do NOT add, remove, or restructure any content.
- Do NOT alter any in-text citation."""

USER_PROMPT_TEMPLATE = """\
Apply the style profile to the following text. Produce only the restyled \
text — no preamble, no commentary, no explanation.

---
{input_text}
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
# Section extraction (same logic as writing-pipeline.py)
# ---------------------------------------------------------------------------
def extract_section(full_text: str, section_id: str) -> str:
    pattern = re.compile(
        r"^(#{1,4})\s+" + re.escape(section_id) + r"(?:\s|$).*",
        re.MULTILINE,
    )
    match = pattern.search(full_text)
    if not match:
        sys.exit(f"ERROR: section '{section_id}' not found in input file.")
    level = len(match.group(1))
    start = match.start()
    end_pattern = re.compile(rf"^#{{{1},{level}}}\s+", re.MULTILINE)
    end_match = end_pattern.search(full_text, match.end())
    end = end_match.start() if end_match else len(full_text)
    return full_text[start:end].strip()


# ---------------------------------------------------------------------------
# API clients
# ---------------------------------------------------------------------------
def make_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=BEDROCK_REGION,
        config=BotocoreConfig(read_timeout=300, connect_timeout=10),
    )


def apply_style_bedrock(input_text: str, style_hypotheses: str, bedrock_client) -> str:
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        style_block=build_style_block(style_hypotheses)
    )
    user_message = USER_PROMPT_TEMPLATE.format(input_text=input_text)
    response = bedrock_client.converse(
        modelId=BEDROCK_MODEL_ARN,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_message}]}],
        inferenceConfig={"maxTokens": MAX_TOKENS, "temperature": 0.3},
    )
    return response["output"]["message"]["content"][0]["text"]


def apply_style_opus(input_text: str, style_hypotheses: str) -> str:
    try:
        import anthropic as _anthropic
    except ImportError:
        sys.exit("ERROR: anthropic not installed. Run: pip install anthropic")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        sys.exit("ERROR: --model claude-opus-4-6 requires ANTHROPIC_API_KEY in .env")
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        style_block=build_style_block(style_hypotheses)
    )
    user_message = USER_PROMPT_TEMPLATE.format(input_text=input_text)
    client = _anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": user_message}],
        system=system_prompt,
    )
    return response.content[0].text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Standalone voice anchoring: apply a .style-profile.md to any "
            "markdown text file. Independent of the writing pipeline."
        )
    )
    parser.add_argument(
        "--input", required=True, metavar="FILE",
        help="Path to the markdown file to restyle.",
    )
    parser.add_argument(
        "--profile", required=True, metavar="FILE",
        help="Path to the .style-profile.md produced by extract-style-profile.py.",
    )
    parser.add_argument(
        "--output", required=True, metavar="FILE",
        help="Path to write the restyled output.",
    )
    parser.add_argument(
        "--section", default=None, metavar="ID",
        help=(
            "Section ID to extract from the input file (e.g. '1.2'). "
            "If omitted, the entire file is restyled."
        ),
    )
    parser.add_argument(
        "--model", default="bedrock", choices=["bedrock", "claude-opus-4-6"],
        help=(
            "'bedrock' = Sonnet 4.6 via AWS Bedrock (default, no personal cost). "
            "'claude-opus-4-6' = Opus via Anthropic direct API (requires ANTHROPIC_API_KEY)."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    repo_root = Path(__file__).parent.parent
    load_env(repo_root)

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = repo_root / input_path
    if not input_path.exists():
        sys.exit(f"ERROR: input file not found: {input_path}")

    profile_path = Path(args.profile)
    if not profile_path.is_absolute():
        profile_path = repo_root / profile_path
    if not profile_path.exists():
        sys.exit(f"ERROR: profile file not found: {profile_path}")

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo_root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load inputs
    full_text = input_path.read_text(encoding="utf-8")
    if args.section:
        input_text = extract_section(full_text, args.section)
        print(
            f"[apply-style-profile] Extracted section '{args.section}': "
            f"{len(input_text.split())} words",
            file=sys.stderr,
        )
    else:
        input_text = full_text
        print(
            f"[apply-style-profile] Input: {input_path.name} "
            f"({len(input_text.split())} words)",
            file=sys.stderr,
        )

    style_hypotheses = profile_path.read_text(encoding="utf-8")
    print(
        f"[apply-style-profile] Profile: {profile_path.name} "
        f"({len(style_hypotheses.split())} words)",
        file=sys.stderr,
    )

    # Apply
    print(
        f"[apply-style-profile] Applying style via {args.model}...",
        file=sys.stderr,
    )
    if args.model == "claude-opus-4-6":
        result = apply_style_opus(input_text, style_hypotheses)
    else:
        bedrock_client = make_bedrock_client()
        result = apply_style_bedrock(input_text, style_hypotheses, bedrock_client)

    output_path.write_text(result, encoding="utf-8")
    print(
        f"[apply-style-profile] Styled output written to {output_path} "
        f"({len(result.split())} words)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
