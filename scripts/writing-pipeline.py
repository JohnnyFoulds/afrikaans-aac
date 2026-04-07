"""
Multi-model academic writing improvement pipeline.

Takes an existing proposal section (from proposal/*.md), runs it through:
  1. Critique (reviewer persona) — default: Bedrock Sonnet 4.6
  2. Claude Sonnet 4.6 (Bedrock) revision
  3. Repeat for N rounds with rotating personas
  4. Language polish — default: Bedrock Sonnet 4.6

All steps default to AWS Bedrock (no personal API cost). Use --reviewer-model
and --polisher-model to override to gpt-4o or claude-opus-4-6 when you want
a quality upgrade and are willing to pay for it.

Usage:
    python scripts/writing-pipeline.py \\
        --input proposal/01-introduction.md \\
        --section "1.2" \\
        --persona unisa \\
        --persona-r2 adversarial \\
        --rounds 2 \\
        --output-dir pipeline-outputs/

    # Override reviewer to GPT-4o and polisher to Opus:
        --reviewer-model gpt-4o --polisher-model claude-opus-4-6

See docs/standards/research/writing-pipeline-protocol.md for the full protocol and rationale.
"""
import argparse
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependency imports — fail fast with helpful messages
# ---------------------------------------------------------------------------
try:
    import boto3
    from botocore.config import Config as BotocoreConfig
except ImportError:
    sys.exit("ERROR: boto3 not installed. Run: pip install boto3")

# Local script imports — use importlib for hyphenated filenames
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util as _ilu

def _load_script(name: str, filename: str):
    spec = _ilu.spec_from_file_location(name, Path(__file__).parent / filename)
    assert spec is not None and spec.loader is not None, f"Cannot load {filename}"
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_asp = _load_script("apply_style_profile", "apply-style-profile.py")
apply_style_bedrock = _asp.apply_style_bedrock
apply_style_opus    = _asp.apply_style_opus

_vc = _load_script("verify_claims", "verify-claims.py")
run_verification = _vc.run_verification
LLMBackend = _vc.LLMBackend
DEFAULT_LOCAL_URL = _vc.DEFAULT_LOCAL_URL

from reviewer_personas import (
    build_reviewer_system_prompt,
    get_persona_for_round,
    PERSONAS,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BEDROCK_REGION = "eu-west-1"
BEDROCK_MODEL_ARN = (
    "arn:aws:bedrock:eu-west-1:557116085116:"
    "application-inference-profile/vb6ydtnx7fbs"
)
# Haiku ARN resolved at runtime from .env (same env var used by run_experiment.py)
_HAIKU_ARN: str = ""  # filled in main() after load_env()

# Default models — all Bedrock (no personal API cost).
# Override via CLI: --reviewer-model gpt-4o, --polisher-model claude-opus-4-6
DEFAULT_REVIEWER_MODEL = "bedrock"   # Sonnet 4.6 via Bedrock
DEFAULT_POLISHER_MODEL = "bedrock"   # Sonnet 4.6 via Bedrock

MAX_TOKENS_REVIEWER = 8000
MAX_TOKENS_REVISER = 16000
MAX_TOKENS_POLISHER = 16000

EARLY_EXIT_THRESHOLD = 3  # skip remaining rounds if critique items < this


# ---------------------------------------------------------------------------
# .env loader (no python-dotenv dependency)
# ---------------------------------------------------------------------------
def load_env(repo_root: Path) -> None:
    """Load .env from repo root into os.environ (does not overwrite existing vars)."""
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
# Section extraction
# ---------------------------------------------------------------------------
def extract_section(text: str, section_id: str) -> str:
    """
    Extract text under a heading matching section_id from markdown text.

    Matches headings like:
        ## 1.2
        ## 1.2 Problem Statement
        ### 3.4.1 Sub-section

    Searches all heading levels (## through #####) for a heading whose
    numbering starts with section_id. Extracts from that heading up to
    (but not including) the next heading at the same or higher level.

    Returns the full heading + body text, or raises ValueError if not found.
    """
    match = None
    hashes = None

    # Try all heading levels 2–5
    for d in range(2, 6):
        h = "#" * d
        p = re.compile(
            rf"^{re.escape(h)}\s+{re.escape(section_id)}(\s+\S.*)?$",
            re.MULTILINE,
        )
        m = p.search(text)
        if m:
            match = m
            hashes = h
            break

    if not match:
        raise ValueError(
            f"Section '{section_id}' not found in file. "
            f"Available headings:\n" + _list_headings(text)
        )

    start = match.start()
    level = len(hashes)

    # Find end: next heading at the same level or higher (fewer #)
    # i.e. a line starting with between 1 and `level` hashes
    after_start = text[start + len(hashes):]
    end_match = re.search(
        rf"^#{'{1,' + str(level) + '}'}(?!#)",
        after_start,
        re.MULTILINE,
    )
    if end_match:
        end = start + len(hashes) + end_match.start()
    else:
        end = len(text)

    extracted = text[start:end].strip()
    return extracted


def _list_headings(text: str) -> str:
    lines = [l for l in text.splitlines() if l.startswith("#")]
    return "\n".join(lines[:20]) or "(no headings found)"


def count_words(text: str) -> int:
    return len(text.split())


def count_critique_items(critique_text: str) -> int:
    """Count numbered critique items in reviewer output."""
    matches = re.findall(r"^\d+\.", critique_text, re.MULTILINE)
    return len(matches)


def load_bib_author_years(bib_path: Path) -> set[tuple[str, str]]:
    """
    Parse references.bib and return a set of (lastname, year) tuples for
    every author of every entry, normalised to lowercase.

    Handles:
      - Multiple authors separated by ' and '
      - 'Lastname, Firstname' and 'Firstname Lastname' formats
      - LaTeX escapes (e.g. {backslash"u} -> u)
    """
    if not bib_path.exists():
        return set()

    text = bib_path.read_text(encoding="utf-8")
    pairs: set[tuple[str, str]] = set()

    # Find each @entry block (raw text — no stripping, to preserve field delimiters)
    for entry_match in re.finditer(
        r"@\w+\{[^,]+,(.+?)(?=\n@|\Z)", text, re.DOTALL
    ):
        body = entry_match.group(1)

        # Extract year
        year_m = re.search(r"\byear\s*=\s*\{?\s*(\d{4})\s*\}?", body, re.IGNORECASE)
        if not year_m:
            continue
        year = year_m.group(1)

        # Extract author field value (content between the outermost braces)
        author_m = re.search(r"\bauthor\s*=\s*\{([^}]+)\}", body, re.IGNORECASE)
        if not author_m:
            continue
        # Strip LaTeX escapes from the author value only
        author_field = re.sub(r"\{\\[^}]*\}", "", author_m.group(1))
        author_field = re.sub(r"[{}]", "", author_field)

        for author in re.split(r"\s+and\s+", author_field, flags=re.IGNORECASE):
            author = author.strip()
            if not author:
                continue
            # 'Lastname, Firstname' → lastname
            if "," in author:
                lastname = author.split(",")[0].strip()
            else:
                # 'Firstname Lastname' → last token
                parts = author.split()
                lastname = parts[-1] if parts else author
            lastname = re.sub(r"[^a-zA-Z]", "", lastname).lower()
            if lastname:
                pairs.add((lastname, year))

    return pairs


def parse_cited_papers_section(critique_text: str) -> list[str]:
    """
    Extract entries from the structured 'PAPERS CITED IN THIS REVIEW' section
    that the reviewer is required to emit.

    Returns a list of raw citation strings exactly as the reviewer wrote them,
    e.g. ['Brown et al. (2025): systematic review of RAG evaluations',
          'Thakur et al. (2021): BEIR benchmark corpus-type dependence'].

    Returns an empty list if the section is absent or contains only 'none'.
    """
    # Locate the section header
    marker = "PAPERS CITED IN THIS REVIEW:"
    idx = critique_text.find(marker)
    if idx == -1:
        return []

    section = critique_text[idx + len(marker):].strip()

    entries = []
    for line in section.splitlines():
        line = line.strip()
        # Each entry starts with '- '; stop at an empty line after entries begin,
        # or at the next all-caps section header
        if line.startswith("- "):
            entry = line[2:].strip()
            if entry.lower() != "none":
                entries.append(entry)
        elif entries and (not line or re.match(r"^[A-Z ]{4,}:", line)):
            # Blank line or next section header — end of this section
            break

    return entries


def check_critique_citations(
    cited_entries: list[str],
    bib_pairs: set[tuple[str, str]],
    round_num: int,
) -> list[str]:
    """
    Cross-reference a list of citation strings (from the structured
    PAPERS CITED section) against bib_pairs.

    Each entry is expected to start with an author-year token like:
      'Brown et al. (2025): ...'
      'Lang and Gürpinar (2025): ...'
      'Hevner (2004): ...'

    Returns warning strings for any entry whose first-author lastname + year
    is not found in bib_pairs.
    """
    # Match the leading author-year token: everything up to the first ':'
    # or end of line, containing a 4-digit year in parentheses.
    author_year_re = re.compile(r"^(.+?)\s*\((\d{4})\)", re.UNICODE)

    warnings = []
    for entry in cited_entries:
        m = author_year_re.match(entry)
        if not m:
            continue
        raw_names = m.group(1).strip()
        year = m.group(2)

        # First token of the author string is the first lastname
        first_token = raw_names.split()[0]
        lastname = re.sub(r"[^a-zA-ZÀ-ÖØ-öø-ÿ]", "", first_token).lower()
        lastname_ascii = "".join(
            c for c in unicodedata.normalize("NFD", lastname)
            if unicodedata.category(c) != "Mn"
        )
        if (lastname_ascii, year) not in bib_pairs:
            warnings.append(
                f"  [round {round_num}] reviewer cited {raw_names} ({year}) "
                f"— not in references.bib"
            )

    return warnings


def build_proposal_context(context_paths: list[Path], input_path: Path, current_section: str | None) -> str:
    """
    Assemble the proposal context from a caller-supplied list of files.

    Each file is included in the order provided. If a context file is the
    same as the input file being revised, only the remainder (excluding the
    target section) is included — so the reviser never sees the exact text
    it is revising as part of its constraint context.

    Returns a single labelled string suitable for inclusion in a prompt.
    """
    parts = []
    input_path_resolved = input_path.resolve()

    for ctx_path in context_paths:
        file_text = ctx_path.read_text(encoding="utf-8")

        if ctx_path.resolve() == input_path_resolved and current_section:
            # Same file as the draft — include everything except the target section
            try:
                section_text = extract_section(file_text, current_section)
                remainder = file_text.replace(section_text, "").strip()
                if remainder:
                    parts.append(
                        f"# From {ctx_path.name} (excluding §{current_section}):\n\n{remainder}"
                    )
            except ValueError:
                parts.append(f"# From {ctx_path.name}:\n\n{file_text}")
        else:
            parts.append(f"# From {ctx_path.name}:\n\n{file_text}")

    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Generic Bedrock helpers — converse (small outputs) and streaming (large outputs)
# ---------------------------------------------------------------------------
def _bedrock_converse(
    bedrock_client,
    system_prompt: str,
    user_message: str,
    max_tokens: int,
    temperature: float,
) -> str:
    """Call Bedrock converse() and return the text response."""
    response = bedrock_client.converse(
        modelId=BEDROCK_MODEL_ARN,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_message}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
    )
    return response["output"]["message"]["content"][0]["text"]


def _bedrock_stream(
    bedrock_client,
    system_prompt: str,
    user_message: str,
    max_tokens: int,
    temperature: float,
) -> str:
    """Call Bedrock invoke_model_with_response_stream() — avoids read timeout for large outputs."""
    import json, base64
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    })
    response = bedrock_client.invoke_model_with_response_stream(
        modelId=BEDROCK_MODEL_ARN,
        body=body,
    )
    chunks = []
    for event in response["body"]:
        chunk = json.loads(event["chunk"]["bytes"])
        if chunk.get("type") == "content_block_delta":
            chunks.append(chunk["delta"].get("text", ""))
    return "".join(chunks)


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------
def call_reviewer(
    draft: str,
    persona_name: str,
    bedrock_client,
    round_num: int,
    proposal_context: str = "",
    model: str = "bedrock",
) -> str:
    """
    Call the reviewer model for structured critique.

    model='bedrock'  → Bedrock Sonnet 4.6 (default, no personal cost)
    model='gpt-4o'   → OpenAI GPT-4o (requires OPENAI_API_KEY in .env)
    """
    system_prompt = build_reviewer_system_prompt(persona_name)
    context_block = (
        f"\n\nFor reference, the rest of the proposal (other chapters/sections) "
        f"is provided below. Do NOT critique content that is adequately addressed "
        f"elsewhere in the proposal — only critique gaps within the section itself.\n\n"
        f"REST OF PROPOSAL:\n---\n{proposal_context}\n---\n\n"
        if proposal_context else ""
    )
    user_message = (
        f"Please review the following section of a PhD proposal "
        f"(Design Science Research methodology, Information Systems, "
        f"open distance e-learning context):{context_block}\n\n"
        f"SECTION TO REVIEW:\n---\n{draft}\n---"
    )

    if model == "gpt-4o":
        try:
            import openai as _openai
        except ImportError:
            sys.exit("ERROR: openai not installed. Run: pip install openai")
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            sys.exit("ERROR: --reviewer-model gpt-4o requires OPENAI_API_KEY in .env")
        log(f"[round {round_num}] calling GPT-4o reviewer (persona: {persona_name})...")
        client = _openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=MAX_TOKENS_REVIEWER,
            temperature=0.3,
        )
        return response.choices[0].message.content
    else:
        log(f"[round {round_num}] calling Bedrock (Sonnet 4.6) reviewer (persona: {persona_name})...")
        return _bedrock_converse(
            bedrock_client, system_prompt, user_message,
            MAX_TOKENS_REVIEWER, 0.3,
        )


def call_reviser(
    draft: str,
    critique: str,
    bedrock_client,
    round_num: int,
    proposal_context: str = "",
    target_words: int = 0,
) -> str:
    """Call Claude Sonnet 4.6 (Bedrock) to revise draft against critique."""
    system_prompt = (
        "You are a PhD-level academic writing editor. Your task is to revise "
        "a section of a PhD proposal based on a structured peer review critique. "
        "British Academic English, PhD level. Design Science Research methodology."
    )
    context_block = (
        f"\n\nCRITICAL — PROPOSAL CONSISTENCY CONTEXT:\n"
        f"The rest of the proposal is provided below. You MUST NOT introduce any "
        f"claim, term, metric, method, or assertion that contradicts or diverges "
        f"from what is stated in the other sections. If a critique item asks you "
        f"to add something (e.g. evaluation metrics, methodology details) that is "
        f"already covered in another section, do NOT duplicate it here — instead, "
        f"add a brief forward-reference (e.g. 'as detailed in §4.4') or note in "
        f"your Revision log that the item is addressed elsewhere.\n\n"
        f"REST OF PROPOSAL:\n---\n{proposal_context}\n---\n\n"
        if proposal_context else ""
    )
    word_budget_rule = (
        f"- WORD BUDGET: Your revised output (excluding the Revision log) must not "
        f"exceed {target_words} words. Address the most impactful critique items first. "
        f"Where content is already covered in another section, use a forward-reference "
        f"(e.g. 'as detailed in §4.4') instead of full elaboration. Prefer tightening "
        f"existing prose to adding new paragraphs. Quality over quantity.\n"
        if target_words > 0 else ""
    )
    user_message = (
        "Revise the following draft to address all numbered CRITIQUE ITEMS below.\n\n"
        "Rules:\n"
        "- Address every numbered critique item.\n"
        "- Do NOT change anything listed under ITEMS ACCEPTABLE AS-IS.\n"
        "- Do NOT change the citation style or introduce new citations not already present.\n"
        "- Preserve the overall section structure and heading.\n"
        "- FABRICATION PREVENTION: If a critique item asks you to add, strengthen, or "
        "specify a claim that you cannot ground in a cited source already present in the "
        "draft or the proposal context, you MUST mark the addition with "
        "[NEEDS VERIFICATION] immediately after the sentence. Do NOT invent metrics, "
        "statistics, findings, or assertions not supported by the existing citations. "
        "It is better to flag a gap than to fill it with unsupported content.\n"
        f"{word_budget_rule}"
        "- After the revised text, append a section headed 'Revision log' that lists "
        "each critique item number and a one-sentence description of how you addressed it.\n\n"
        f"{context_block}"
        f"DRAFT:\n---\n{draft}\n---\n\n"
        f"CRITIQUE:\n---\n{critique}\n---"
    )
    log(f"[round {round_num}] calling Bedrock (Sonnet 4.6) reviser...")
    return _bedrock_stream(
        bedrock_client, system_prompt, user_message, MAX_TOKENS_REVISER, 0.2,
    )


def call_polisher(
    revised_text: str,
    bedrock_client,
    model: str = "bedrock",
    target_words: int = 0,
) -> str:
    """
    Language polish pass — style only, no substance changes.

    model='bedrock'        → Bedrock Sonnet 4.6 (default, no personal cost)
    model='claude-opus-4-6' → Anthropic direct API Opus (requires ANTHROPIC_API_KEY)
    """
    system_prompt = (
        "You are an expert academic writing editor specialising in British Academic "
        "English at doctoral level. Your task is a style-only polish pass — you must "
        "NOT change the substance, argument structure, citations, or content in any way."
    )
    trim_rule = (
        f"- TARGET LENGTH: The final output should be approximately {target_words} words. "
        f"If the current text significantly exceeds this, tighten prose by condensing "
        f"over-elaborated passages, collapsing redundant sentences, and shortening "
        f"verbose constructions — but do NOT remove any argument, claim, or citation. "
        f"Compress phrasing; do not delete substance.\n"
        if target_words > 0 else ""
    )
    user_message = (
        "Polish the following section of a PhD proposal for British Academic English "
        "at doctoral level.\n\n"
        "Style improvements to make:\n"
        "- Vary sentence length and rhythm naturally — avoid monotonous cadence.\n"
        "- Calibrate hedging language: use 'suggests', 'appears to', "
        "'is consistent with', 'the evidence indicates' rather than overclaiming "
        "or underclaiming.\n"
        "- Eliminate detectable LLM writing tells: no 'it is worth noting', "
        "'delve into', 'shed light on', 'in the realm of', 'it is important to', "
        "'underscore', 'robust' (overused).\n"
        "- Minimise em-dash overuse — use sparingly.\n"
        "- Balance passive and active voice appropriate to academic register.\n"
        "- Ensure the Revision log section (if present) is removed — it is an "
        "internal working note, not part of the final text.\n"
        f"{trim_rule}\n"
        "DO NOT:\n"
        "- Change any argument, claim, or factual statement.\n"
        "- Add, remove, or restructure any content.\n"
        "- Alter any in-text citation.\n\n"
        f"SECTION TO POLISH:\n---\n{revised_text}\n---"
    )

    if model == "claude-opus-4-6":
        try:
            import anthropic as _anthropic
        except ImportError:
            sys.exit("ERROR: anthropic not installed. Run: pip install anthropic")
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            sys.exit("ERROR: --polisher-model claude-opus-4-6 requires ANTHROPIC_API_KEY in .env")
        log("calling Anthropic direct API (Opus 4.6) for language polish...")
        client = _anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=MAX_TOKENS_POLISHER,
            messages=[{"role": "user", "content": user_message}],
            system=system_prompt,
        )
        return response.content[0].text
    else:
        log("calling Bedrock (Sonnet 4.6) for language polish...")
        return _bedrock_stream(
            bedrock_client, system_prompt, user_message, MAX_TOKENS_POLISHER, 0.3,
        )


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def log(msg: str) -> None:
    print(f"[pipeline] {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Step 5: Verify + resolve
# ---------------------------------------------------------------------------

def run_verify_and_resolve(
    polished_path: Path,
    output_dir: Path,
    slug: str,
    repo_root: Path,
    bedrock_client,
    context_paths: list[str],
    llm_backend=None,
) -> Path | None:
    """
    Run verify-claims on the polished section, then if any items are flagged,
    run a targeted resolution pass and re-verify.

    Returns the path to the resolved file, or None if verification passed
    without needing a resolution pass.
    """
    report_path = output_dir / f"{slug}-verification-report.md"
    summary_path = output_dir / f"{slug}-verification-summary.md"

    def run_verify(input_file: Path, label: str) -> tuple[int, str]:
        """Call run_verification directly. Returns (exit_code, report_text)."""
        log(f"--- {label} ---")
        log(f"running: verify-claims --context {input_file.name} --auto-fetch --tier-aware --architecture C")
        backend = llm_backend or LLMBackend(
            backend="bedrock", model_id=_HAIKU_ARN or BEDROCK_MODEL_ARN,
            local_url=DEFAULT_LOCAL_URL,
        )
        results, rpt, smy = run_verification(
            context_files=[str(input_file)],
            llm_backend=backend,
            output_dir=output_dir,
            bib_path=repo_root / "literature/references.bib",
            mkv_dir=repo_root / "literature/mkv",
            auto_fetch=True,
            tier_aware=True,
            tier_architecture="C",
        )
        # Rename to slug-prefixed names (verify-claims writes generic names)
        default_report = output_dir / "verification-report.md"
        default_summary = output_dir / "verification-summary.md"
        if default_report.exists():
            default_report.rename(report_path)
        if default_summary.exists():
            default_summary.rename(summary_path)
        has_failures = any(r["verdict"] in ("NEEDS_VERIFICATION", "NO_SOURCE") for r in results)
        report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
        return (1 if has_failures else 0), report_text

    # First verification pass
    exit_code, report_text = run_verify(polished_path, "step 5a: verify-claims (initial)")

    if exit_code == 0:
        log("verification passed — all claims verified, no resolution needed")
        return None

    # Parse flagged items from the report
    flagged = _parse_flagged_items(report_text)
    if not flagged:
        log("verification: non-zero exit but no actionable items found in report")
        return None

    log(f"verification: {len(flagged)} flagged item(s) — running resolution pass")

    # Resolution pass: targeted Bedrock call to fix only the flagged sentences
    polished_text = polished_path.read_text(encoding="utf-8")
    resolved_text = call_resolver(polished_text, flagged, report_text, bedrock_client)

    resolved_path = output_dir / f"{slug}-resolved.md"
    resolved_path.write_text(resolved_text, encoding="utf-8")
    log(f"resolved draft saved: {resolved_path}")

    # Re-verify the resolved file
    exit_code2, report_text2 = run_verify(resolved_path, "step 5b: verify-claims (post-resolution)")
    remaining = _parse_flagged_items(report_text2)
    if remaining:
        log(
            f"post-resolution verification: {len(remaining)} item(s) still flagged "
            f"— require human review (see {report_path.name})"
        )
    else:
        log("post-resolution verification: all claims now verified")

    return resolved_path


def _parse_flagged_items(report_text: str) -> list[dict]:
    """
    Extract NEEDS_VERIFICATION and NO_SOURCE items from a verification report.

    Matches the actual report format produced by verify-claims.py:
      ### <cite-key> — <raw citation>
      **Claim sentence:** ...
      **Source:** ...
      **Confidence:** N/5
      **Supporting quote:** ...
      **Reasoning:** ...

    Returns list of dicts with keys: verdict, cite_key, sentence, reasoning.
    """
    flagged = []

    # Determine which section(s) to parse — report has ## headings per verdict group
    # Split on section-level headings to find NEEDS_VERIFICATION and NO_SOURCE blocks
    needs_v_m = re.search(
        r"## ⚠️ NEEDS_VERIFICATION.+?(?=\n## |\Z)", report_text, re.DOTALL
    )
    no_src_m = re.search(
        r"## ❌ NO_SOURCE.+?(?=\n## |\Z)", report_text, re.DOTALL
    )

    for verdict, section_match in [
        ("NEEDS_VERIFICATION", needs_v_m),
        ("NO_SOURCE", no_src_m),
    ]:
        if not section_match:
            continue
        section = section_match.group(0)

        # Each entry starts with ### cite-key — raw citation
        for entry in re.split(r"\n### ", section):
            if not entry.strip() or entry.startswith("#"):
                continue

            # First line is "cite-key — raw citation"
            first_line = entry.splitlines()[0].strip()
            cite_key = first_line.split(" — ")[0].strip() if " — " in first_line else first_line

            sentence_m = re.search(
                r"\*\*Claim sentence:\*\*\s*(.+?)(?=\n\*\*|\Z)", entry, re.DOTALL
            )
            reasoning_m = re.search(
                r"\*\*Reasoning:\*\*\s*(.+?)(?=\n\*\*|\n---|\Z)", entry, re.DOTALL
            )
            flagged.append({
                "verdict": verdict,
                "cite_key": cite_key,
                "sentence": sentence_m.group(1).strip() if sentence_m else "",
                "reasoning": reasoning_m.group(1).strip() if reasoning_m else "",
            })

    return flagged


def call_resolver(
    polished_text: str,
    flagged_items: list[dict],
    verification_report: str,
    bedrock_client,
) -> str:
    """
    Targeted resolution pass: fix only the sentences flagged as
    NEEDS_VERIFICATION or NO_SOURCE by verify-claims.

    Strategy per item:
    - If the cite key resolves to an mkv file, the model is given the source
      text and asked to rewrite the sentence to match what the source actually says.
    - If no source is available, the model qualifies or scopes the claim rather
      than asserting it, and marks it [NEEDS VERIFICATION: <specific reason>].
    """
    repo_root = Path(__file__).parent.parent.resolve()
    mkv_dir = repo_root / "literature" / "mkv"

    # Build source context for flagged items that have mkv files
    source_blocks = []
    for item in flagged_items:
        mkv_path = mkv_dir / f"{item['cite_key']}.md"
        if mkv_path.exists():
            # Include only first 3000 chars to stay within token budget
            source_text = mkv_path.read_text(encoding="utf-8")[:3000]
            source_blocks.append(
                f"SOURCE for {item['cite_key']}:\n---\n{source_text}\n---"
            )

    sources_section = "\n\n".join(source_blocks) if source_blocks else "(no source files available)"

    flagged_list = "\n".join(
        f"{i+1}. [{item['verdict']}] cite_key={item['cite_key']}\n"
        f"   Sentence: {item['sentence']}\n"
        f"   Reason: {item['reasoning']}"
        for i, item in enumerate(flagged_items)
    )

    system_prompt = (
        "You are a PhD-level academic writing editor performing a targeted "
        "claim resolution pass. Fix only the specific flagged sentences listed "
        "below. Do not change anything else in the text."
    )
    user_message = (
        "The following section has been through verification. Some sentences "
        "were flagged as NEEDS_VERIFICATION or NO_SOURCE. Fix only those "
        "sentences using the rules below.\n\n"
        "RULES:\n"
        "- If a SOURCE is provided for the cite key: rewrite the sentence so "
        "it accurately reflects what the source actually says. You may quote "
        "or paraphrase directly from the source. Do not claim more than the "
        "source supports.\n"
        "- If NO SOURCE is available: qualify or scope the claim (e.g. 'to the "
        "author's knowledge', 'based on the literature reviewed', 'the available "
        "evidence suggests'). If the claim cannot be responsibly made without a "
        "source, mark it [NEEDS VERIFICATION: <one-sentence specific description "
        "of what source or evidence is needed>].\n"
        "- Do not remove any argument — qualify or scope it instead.\n"
        "- Do not change any sentence that was not flagged.\n"
        "- Do not add new citations not already present in the text.\n\n"
        f"FLAGGED ITEMS:\n{flagged_list}\n\n"
        f"AVAILABLE SOURCES:\n{sources_section}\n\n"
        f"SECTION TO RESOLVE:\n---\n{polished_text}\n---"
    )

    log("calling Bedrock (Sonnet 4.6) resolver...")
    return _bedrock_converse(bedrock_client, system_prompt, user_message, 4000, 0.2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-model academic writing improvement pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to the existing markdown file (e.g. proposal/01-introduction.md).",
    )
    parser.add_argument(
        "--section", default=None,
        help=(
            "Heading ID to extract, e.g. '1.2'. "
            "If omitted, the entire file is used."
        ),
    )
    parser.add_argument(
        "--persona", default="unisa",
        choices=list(PERSONAS.keys()),
        help="Reviewer persona for round 1 (default: unisa).",
    )
    parser.add_argument(
        "--persona-r2", default=None,
        dest="persona_r2",
        choices=list(PERSONAS.keys()),
        help=(
            "Reviewer persona for round 2. "
            "If omitted, uses the next persona in rotation after --persona."
        ),
    )
    parser.add_argument(
        "--rounds", type=int, default=2, choices=[1, 2, 3, 4],
        help="Number of critique-revision cycles (default: 2).",
    )
    parser.add_argument(
        "--context", nargs="+", metavar="FILE", default=None,
        help=(
            "One or more markdown files to use as proposal context, in order. "
            "The reviewer and reviser receive these files so they do not "
            "introduce claims that contradict the rest of the proposal. "
            "Typically all proposal files except the one being revised. "
            "If omitted, no context is provided (not recommended)."
        ),
    )
    parser.add_argument(
        "--output-dir", default="pipeline-outputs",
        help="Directory for output files (default: pipeline-outputs/).",
    )
    parser.add_argument(
        "--reviewer-model", default=DEFAULT_REVIEWER_MODEL,
        dest="reviewer_model",
        choices=["bedrock", "gpt-4o"],
        help=(
            "Model for the critique step. "
            "'bedrock' = Sonnet 4.6 via AWS Bedrock (default, no personal cost). "
            "'gpt-4o' = OpenAI GPT-4o (requires OPENAI_API_KEY in .env)."
        ),
    )
    parser.add_argument(
        "--polisher-model", default=DEFAULT_POLISHER_MODEL,
        dest="polisher_model",
        choices=["bedrock", "claude-opus-4-6"],
        help=(
            "Model for the language polish step. "
            "'bedrock' = Sonnet 4.6 via AWS Bedrock (default, no personal cost). "
            "'claude-opus-4-6' = Opus via Anthropic direct API (requires ANTHROPIC_API_KEY in .env)."
        ),
    )
    parser.add_argument(
        "--target-words", type=int, default=0, dest="target_words",
        metavar="N",
        help=(
            "Target word count ceiling for the revised and polished output. "
            "Default: omitted = unconstrained (the reviser addresses all critique items "
            "without a word budget; output may expand significantly). "
            "When set, the reviser prioritises forward-references over full elaboration "
            "and the polisher trims to target. "
            "Use when you know the section should stay within a fixed length. "
            "For PhD-level work, omit this flag and review the expanded output manually "
            "to decide which arguments to retain."
        ),
    )
    parser.add_argument(
        "--style-profile", default=None, dest="style_profile", metavar="FILE",
        help=(
            "Path to a .style-profile.md file produced by extract-style-profile.py. "
            "If provided, the language polish step is additionally constrained to match "
            "the specific stylistic hypotheses in the profile. "
            "If omitted, the polish step applies generic academic style rules only "
            "(existing behaviour, no change)."
        ),
    )
    return parser.parse_args()


def get_section_slug(args: argparse.Namespace) -> str:
    """Derive a filesystem-safe slug for output file names."""
    if args.section:
        return re.sub(r"[^\w.-]", "-", args.section)
    stem = Path(args.input).stem
    return re.sub(r"[^\w.-]", "-", stem)


def get_persona_sequence(args: argparse.Namespace) -> list[str]:
    """Build ordered list of persona names for all rounds."""
    personas = []
    for r in range(1, args.rounds + 1):
        if r == 1:
            personas.append(args.persona)
        elif r == 2 and args.persona_r2:
            personas.append(args.persona_r2)
        else:
            personas.append(get_persona_for_round(r, first_persona=args.persona))
    return personas


def main() -> None:
    args = parse_args()

    # Resolve repo root (scripts/ is one level below repo root)
    repo_root = Path(__file__).parent.parent.resolve()
    load_env(repo_root)

    # Validate env vars — only require keys for the models actually being used.
    # Bedrock uses AWS credentials from the environment (no extra key needed).
    required_keys = []
    if args.reviewer_model == "gpt-4o":
        required_keys.append("OPENAI_API_KEY")
    if args.polisher_model == "claude-opus-4-6":
        required_keys.append("ANTHROPIC_API_KEY")
    missing = [k for k in required_keys if not os.environ.get(k)]
    if missing:
        sys.exit(f"ERROR: missing environment variables: {', '.join(missing)}\n"
                 f"Add them to {repo_root / '.env'}")

    # Validate style profile path (optional — applied as subprocess after polish)
    if args.style_profile:
        profile_path = repo_root / args.style_profile
        if not profile_path.exists():
            sys.exit(f"ERROR: --style-profile file not found: {profile_path}")
        log(f"style profile: {profile_path} (will be applied after polish step)")

    # Prepare output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    slug = get_section_slug(args)
    persona_sequence = get_persona_sequence(args)

    log(f"input: {args.input}")
    log(f"section: {args.section or '(full file)'}")
    log(f"rounds: {args.rounds}")
    log(f"persona sequence: {persona_sequence}")
    log(f"output dir: {output_dir}")

    # ------------------------------------------------------------------
    # Step 1: Extract input text
    # ------------------------------------------------------------------
    input_path = repo_root / args.input
    if not input_path.exists():
        sys.exit(f"ERROR: input file not found: {input_path}")

    full_text = input_path.read_text(encoding="utf-8")
    if args.section:
        try:
            current_draft = extract_section(full_text, args.section)
        except ValueError as e:
            sys.exit(f"ERROR: {e}")
    else:
        current_draft = full_text

    word_count = count_words(current_draft)
    log(f"extracted {word_count} words")

    # Resolve effective target word count (0 = unconstrained)
    effective_target = args.target_words
    if effective_target > 0:
        log(f"target word count: {effective_target} (explicit)")
    else:
        log(
            f"warning: no --target-words set — output may expand significantly "
            f"(original: {word_count} words). Pass --target-words N to constrain length."
        )

    # ------------------------------------------------------------------
    # Load proposal context from caller-supplied --context files.
    # ------------------------------------------------------------------
    if args.context:
        context_paths = [repo_root / p for p in args.context]
        missing_ctx = [p for p in context_paths if not p.exists()]
        if missing_ctx:
            sys.exit(f"ERROR: context file(s) not found: {', '.join(str(p) for p in missing_ctx)}")
        proposal_context = build_proposal_context(context_paths, input_path, args.section)
        log(f"proposal context: {len(context_paths)} file(s), {count_words(proposal_context)} words")
    else:
        proposal_context = ""
        log("warning: no --context provided — reviewer and reviser have no proposal context")

    # ------------------------------------------------------------------
    # Initialise API clients
    # ------------------------------------------------------------------
    # Load .env so HAIKU_ARN is available for the verifier.
    _vc.load_env()
    global _HAIKU_ARN
    _HAIKU_ARN = os.environ.get("HAIKU_ARN", "")
    if not _HAIKU_ARN:
        log("warning: HAIKU_ARN not set — verifier will use Sonnet (higher cost)")

    # Bedrock is always needed (reviser always uses it; reviewer/polisher may too).
    bedrock_client = boto3.client(
        "bedrock-runtime",
        region_name=BEDROCK_REGION,
        config=BotocoreConfig(read_timeout=600, connect_timeout=60),
    )
    log(f"reviewer model: {args.reviewer_model}")
    log(f"polisher model: {args.polisher_model}")

    # Load bib for citation cross-checking
    bib_path = repo_root / "references" / "references.bib"
    bib_pairs = load_bib_author_years(bib_path)
    if bib_pairs:
        log(f"loaded {len(bib_pairs)} author-year pairs from references.bib")
    else:
        log("warning: references.bib not found or empty — citation checking disabled")

    # ------------------------------------------------------------------
    # Steps 2–3: Critique + Revise loop
    # ------------------------------------------------------------------
    for round_num in range(1, args.rounds + 1):
        persona_name = persona_sequence[round_num - 1]
        log(f"--- round {round_num}/{args.rounds} (persona: {persona_name}) ---")

        # Critique
        critique = call_reviewer(
            current_draft, persona_name, bedrock_client, round_num,
            proposal_context=proposal_context,
            model=args.reviewer_model,
        )
        critique_path = output_dir / f"{slug}-critique-r{round_num}.md"
        critique_path.write_text(
            f"# Critique — Round {round_num} (persona: {persona_name})\n\n{critique}",
            encoding="utf-8",
        )
        log(f"critique saved: {critique_path}")

        n_items = count_critique_items(critique)
        log(f"critique items found: {n_items}")

        # Citation cross-check: parse the structured PAPERS CITED section the
        # reviewer is required to emit, then cross-reference against the bib.
        if bib_pairs:
            cited_entries = parse_cited_papers_section(critique)
            if not cited_entries:
                log("citation check: no PAPERS CITED section found in critique output")
            else:
                unknown_citations = check_critique_citations(cited_entries, bib_pairs, round_num)
                if unknown_citations:
                    log(
                        f"CITATION ALERT — reviewer referenced {len(unknown_citations)} "
                        f"paper(s) not in references.bib (potential literature gaps):"
                    )
                    for w in unknown_citations:
                        log(w)
                else:
                    log(
                        f"citation check: all {len(cited_entries)} reviewer citation(s) "
                        f"found in references.bib"
                    )

        if n_items < EARLY_EXIT_THRESHOLD and round_num < args.rounds:
            log(
                f"fewer than {EARLY_EXIT_THRESHOLD} critique items — "
                f"early exit after round {round_num}"
            )
            # Write placeholder files for skipped rounds so smoke test
            # doesn't fail on missing files
            for skipped in range(round_num + 1, args.rounds + 1):
                placeholder = (
                    f"# Round {skipped} skipped (early exit — "
                    f"fewer than {EARLY_EXIT_THRESHOLD} critique items in round {round_num})\n"
                )
                (output_dir / f"{slug}-critique-r{skipped}.md").write_text(
                    placeholder, encoding="utf-8"
                )
                (output_dir / f"{slug}-revised-r{skipped}.md").write_text(
                    f"# Round {skipped} skipped\n\n{current_draft}", encoding="utf-8"
                )
            break

        # Revise
        revised = call_reviser(
            current_draft, critique, bedrock_client, round_num,
            proposal_context=proposal_context,
            target_words=effective_target,
        )
        revised_path = output_dir / f"{slug}-revised-r{round_num}.md"
        revised_path.write_text(revised, encoding="utf-8")
        log(f"revision saved: {revised_path}")

        current_draft = revised

    # ------------------------------------------------------------------
    # Step 4: Language polish
    # ------------------------------------------------------------------
    log(f"--- language polish ({args.polisher_model}) ---")
    polished = call_polisher(
        current_draft, bedrock_client,
        model=args.polisher_model,
        target_words=effective_target,
    )
    polished_path = output_dir / f"{slug}-polished.md"
    polished_path.write_text(polished, encoding="utf-8")
    log(f"polished draft saved: {polished_path}")

    # ------------------------------------------------------------------
    # Step 4b: Style anchoring (optional — only if --style-profile given)
    # ------------------------------------------------------------------
    if args.style_profile:
        log("--- style anchoring (apply-style-profile) ---")
        styled_path = output_dir / f"{slug}-styled.md"
        profile_text = (repo_root / args.style_profile).read_text(encoding="utf-8")
        polished_text = polished_path.read_text(encoding="utf-8")
        if args.polisher_model == "claude-opus-4-6":
            styled = apply_style_opus(polished_text, profile_text)
        else:
            styled = apply_style_bedrock(polished_text, profile_text, bedrock_client)
        styled_path.write_text(styled, encoding="utf-8")
        polished_path = styled_path
        log(f"styled draft saved: {polished_path}")

    # ------------------------------------------------------------------
    # Step 5: Verify claims + resolve flagged items
    # ------------------------------------------------------------------
    context_args = [str(repo_root / p) for p in args.context] if args.context else []

    resolved_path = run_verify_and_resolve(
        polished_path=polished_path,
        output_dir=output_dir,
        slug=slug,
        repo_root=repo_root,
        bedrock_client=bedrock_client,
        context_paths=context_args,
    )
    final_path = resolved_path if resolved_path else polished_path

    # ------------------------------------------------------------------
    # Step 6: Human review reminder
    # ------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"Pipeline complete.")
    print(f"  Final draft:    {final_path}")
    if resolved_path:
        print(f"  Verify report:  {output_dir / (slug + '-verification-report.md')}")
    print(f"{'=' * 60}")
    print("\nStep 7 (mandatory — do not skip):")
    print("  Open the final draft and make targeted human edits where:")
    print("  - Any remaining [NEEDS VERIFICATION] items require your judgement")
    print("  - Your intended argument was distorted during revision")
    print("  - Specific phrasings conflict with your voice or terminology")
    print("\nThe pipeline produces the substrate; your final review completes it.")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
