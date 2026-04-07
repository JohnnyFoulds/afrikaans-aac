"""
verify-claims.py — Citation verification tool for the RAG-for-ODL PhD proposal.

Extracts every citation from --context files, resolves each against the
literature/mkv/ directory (converting missing papers from PDF/web if needed),
and performs STRONG verification: a claim is VERIFIED only when a specific,
quotable passage in the source directly supports it.

Usage:
    python scripts/verify-claims.py \\
        --context proposal/01-introduction.md proposal/02-research-questions.md \\
        --bib literature/references.bib \\
        --mkv-dir literature/mkv/ \\
        [--output-dir pipeline-outputs/] \\
        [--auto-fetch]   # try to fetch+convert missing papers via DOI/arXiv

Exit code 0 if all claims VERIFIED, 1 if any NEEDS_VERIFICATION or NO_SOURCE.

Output:
    <output-dir>/verification-report.md   — full report with PASS/FAIL per claim
    <output-dir>/verification-summary.md  — one-line status per citation key
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent

BEDROCK_REGION = "eu-west-1"
BEDROCK_MODEL_ARN = (
    "arn:aws:bedrock:eu-west-1:557116085116:"
    "application-inference-profile/vb6ydtnx7fbs"
)

DEFAULT_MODELS = {
    "bedrock": BEDROCK_MODEL_ARN,
    "openai":  "gpt-4o",
    "local":   "Qwen3.5-35B-A3B",
}
DEFAULT_LOCAL_URL = "http://dragon:8080"

# Mapping of known claim-bearing author+year patterns to bib cite keys.
# Built dynamically from the parsed .bib file.

VERIFICATION_PROMPT_TEMPLATE = """\
You are a rigorous academic fact-checker performing STRONG verification.

TASK: Determine whether the following CLAIM from a PhD proposal is DIRECTLY
supported by the SOURCE TEXT provided. Strong verification means: you must
identify a specific quotable passage in the source that directly supports the
claim. Logical inference, general consistency, or topic overlap is NOT
sufficient.

CLAIM:
{claim}

SOURCE TEXT (excerpts from: {source_title} by {source_authors}, {source_year}):
{source_text}

---

Respond with a JSON object ONLY (no prose before or after):

{{
  "verdict": "VERIFIED" | "NEEDS_VERIFICATION" | "NO_SOURCE",
  "confidence": 1-5,
  "supporting_quote": "<exact quote from source that supports the claim, or empty string>",
  "reasoning": "<1-2 sentences explaining your verdict>"
}}

Rules:
- VERIFIED: A specific, quotable passage in the source directly supports the claim.
- NEEDS_VERIFICATION: The source is relevant but no passage directly supports
  the exact claim being made.
- NO_SOURCE: The source text does not address the claim at all.
- confidence 5 = certain, 1 = very uncertain
- supporting_quote must be verbatim from the source text, or empty string.
"""

# ---------------------------------------------------------------------------
# Tier-aware prompt templates
# ---------------------------------------------------------------------------

CLASSIFICATION_PROMPT_TEMPLATE = """\
You are an academic claim classifier. Classify the following CLAIM into exactly
one of three tiers.

CLAIM:
{claim}

TIER DEFINITIONS:

T1_EMPIRICAL — The claim asserts specific numbers, measurements, percentages,
sample sizes, effect sizes, named benchmark scores, task success rates, or
explicitly causal results (e.g. "reduces X by Y%"). The claim is falsified if
any stated number is absent from or contradicted by the source.

OVERRIDE RULE: If a claim is framed as application or theory but embeds specific
numbers or causal assertions (e.g. "CLT explains the 43% load reduction"),
classify T1_EMPIRICAL regardless of the framing language.

T2_SYNTHESIS — The claim attributes a characterisation, framing, argument, or
thematic finding to the source without asserting specific numbers. Examples:
"Mouton documents learner support failures", "Hevner provides a methodology".

T3_APPLICATION — The claim attributes a theoretical or methodological framework
to the source and applies it to a new context not present in the source. The
source establishes the original theory; the connection to the new context is the
claimant's own inference. Example: "CLT (Sweller, 1994) explains why document
navigation imposes extraneous cognitive load".

Respond with a JSON object ONLY (no prose before or after):

{{
  "tier": "T1_EMPIRICAL" | "T2_SYNTHESIS" | "T3_APPLICATION",
  "reasoning": "<1 sentence explaining the classification>"
}}
"""

VERIFICATION_PROMPT_T1 = """\
You are a rigorous academic fact-checker performing STRONG verification of an
EMPIRICAL claim. The claim asserts specific numbers, measurements, or causal
results. Every stated number must appear verbatim in a quotable passage.

CLAIM:
{claim}

SOURCE TEXT (excerpts from: {source_title} by {source_authors}, {source_year}):
{source_text}

---

Respond with a JSON object ONLY (no prose before or after):

{{
  "verdict": "VERIFIED" | "NEEDS_VERIFICATION" | "NO_SOURCE",
  "confidence": 1-5,
  "supporting_quote": "<exact verbatim quote from source, or empty string>",
  "reasoning": "<1-2 sentences explaining your verdict>"
}}

T1_EMPIRICAL verdict criteria:
- VERIFIED: Every specific number or causal result in the claim appears verbatim
  or is directly calculable from a single quotable passage.
- NEEDS_VERIFICATION: The source addresses the topic and some numbers are present,
  but at least one specific number or result cannot be matched to a quotable passage.
- NO_SOURCE: One or more numbers are absent from the source entirely, or the source
  states a different number or result. Also NO_SOURCE if the source explicitly
  contradicts the claim.

Rules: supporting_quote must be verbatim from the source, or empty string.
confidence 5 = certain, 1 = very uncertain.
"""

VERIFICATION_PROMPT_T2 = """\
You are a rigorous academic fact-checker performing STRONG verification of a
SYNTHESIS claim. The claim attributes a characterisation, argument, or thematic
finding to the source.

CLAIM:
{claim}

SOURCE TEXT (excerpts from: {source_title} by {source_authors}, {source_year}):
{source_text}

---

Respond with a JSON object ONLY (no prose before or after):

{{
  "verdict": "VERIFIED" | "NEEDS_VERIFICATION" | "NO_SOURCE",
  "confidence": 1-5,
  "supporting_quote": "<exact verbatim quote from source, or empty string>",
  "reasoning": "<1-2 sentences explaining your verdict>"
}}

T2_SYNTHESIS verdict criteria:
- VERIFIED: A specific quotable passage directly supports the characterisation
  as stated.
- NEEDS_VERIFICATION: The source addresses the topic but no single passage
  directly supports the exact characterisation.
- NO_SOURCE: Any of the following apply:
  (a) The source does not address the claim at all.
  (b) The source is about a different country, institution, or domain than what
      the claim attributes to it (e.g. citing a paper about Tanzania for a claim
      about South African ODL institutions).
  (c) The source explicitly contradicts the characterisation (e.g. the source
      says both approaches are complementary but the claim says one is superior).

Rules: supporting_quote must be verbatim from the source, or empty string.
confidence 5 = certain, 1 = very uncertain.
"""

VERIFICATION_PROMPT_T3 = """\
You are a rigorous academic fact-checker performing verification of an
APPLICATION claim. The claim cites a theoretical or methodological framework
from the source and applies it to a new context. The application itself is the
claimant's own inference — not something the source paper states.

CLAIM:
{claim}

SOURCE TEXT (excerpts from: {source_title} by {source_authors}, {source_year}):
{source_text}

---

Respond with a JSON object ONLY (no prose before or after):

{{
  "verdict": "VERIFIED" | "NEEDS_VERIFICATION" | "NO_SOURCE",
  "confidence": 1-5,
  "supporting_quote": "<exact verbatim quote from source, or empty string>",
  "reasoning": "<1-2 sentences explaining your verdict>"
}}

T3_APPLICATION verdict criteria:
- VERIFIED: The source establishes the cited framework AND explicitly connects
  it to the applied context stated in the claim (not merely implies it).
- NEEDS_VERIFICATION: The source establishes the framework but the connection
  to the applied context is the claimant's own inference. THIS IS THE NORMAL
  AND EXPECTED OUTCOME for well-formed T3 application claims — it is not a
  failure signal.
- NO_SOURCE: The source does not establish the cited framework, or it
  contradicts the characterisation of the framework as described in the claim.

Rules: For T3 NEEDS_VERIFICATION, leave supporting_quote as empty string.
supporting_quote must be verbatim from the source, or empty string.
confidence 5 = certain, 1 = very uncertain.
"""

VERIFICATION_PROMPT_OPTION_B = """\
You are a rigorous academic fact-checker performing STRONG verification. Your task
has two phases: (1) classify the claim type, then (2) apply the appropriate tier
criteria to produce a verdict. Both phases occur in your reasoning before you emit
the final JSON.

CLAIM:
{claim}

SOURCE TEXT (excerpts from: {source_title} by {source_authors}, {source_year}):
{source_text}

PHASE 1 — CLASSIFY THE CLAIM TIER

T1_EMPIRICAL — The claim asserts specific numbers, measurements, percentages,
sample sizes, effect sizes, named benchmark scores, task success rates, or
explicitly causal results. The claim is falsified if any stated number is absent
from or contradicted by the source.

OVERRIDE RULE: If a claim is framed as application or theory but embeds specific
numbers or causal assertions, treat the entire claim as T1_EMPIRICAL.

T2_SYNTHESIS — The claim attributes a characterisation, framing, argument, or
thematic finding to the source without asserting specific numbers.

T3_APPLICATION — The claim attributes a theoretical or methodological framework
to the source and applies it to a new context not present in the source. The
source establishes the original theory; the connection to the new context is the
claimant's own inference.

PHASE 2 — APPLY TIER-APPROPRIATE VERIFICATION CRITERIA

T1_EMPIRICAL criteria:
- VERIFIED: Every specific number or causal result appears verbatim or is directly
  calculable from a quotable passage.
- NEEDS_VERIFICATION: Topic addressed, some numbers present, but at least one
  specific number cannot be matched to a quotable passage.
- NO_SOURCE: One or more numbers are absent from the source entirely, or the source
  states a different number/result.

T2_SYNTHESIS criteria:
- VERIFIED: A specific quotable passage directly supports the characterisation.
- NEEDS_VERIFICATION: Source addresses the topic but no single passage directly
  supports the exact characterisation as stated.
- NO_SOURCE: Any of: (a) source does not address the claim; (b) source is about a
  different country, institution, or context than the claim attributes to it;
  (c) source explicitly contradicts the characterisation.

T3_APPLICATION criteria:
- VERIFIED: Source establishes the framework AND explicitly connects it to the
  applied context in the claim (not merely implies it).
- NEEDS_VERIFICATION: Source establishes the framework but the connection to the
  applied context is the claimant's own inference. THIS IS THE NORMAL AND EXPECTED
  OUTCOME FOR T3 CLAIMS — it is not a failure signal.
- NO_SOURCE: Source does not establish the cited framework, or contradicts the
  characterisation of the framework.

ADDITIONAL RULE: For all tiers, if the source explicitly contradicts the claim,
the verdict is NO_SOURCE, not NEEDS_VERIFICATION.

Respond with a JSON object ONLY (no prose before or after):

{{
  "claim_tier": "T1_EMPIRICAL" | "T2_SYNTHESIS" | "T3_APPLICATION",
  "verdict": "VERIFIED" | "NEEDS_VERIFICATION" | "NO_SOURCE",
  "confidence": 1-5,
  "supporting_quote": "<exact verbatim quote from source, or empty string>",
  "reasoning": "<1-2 sentences naming the tier and explaining the verdict>"
}}

Rules: supporting_quote must be verbatim or empty string. For T3 NEEDS_VERIFICATION,
leave supporting_quote empty. confidence 5 = certain, 1 = very uncertain.
"""


# ---------------------------------------------------------------------------
# LLM backend adapter
# ---------------------------------------------------------------------------

class LLMBackend:
    """
    Thin adapter over three backends: bedrock, openai, local.

    All backends expose a single .complete(prompt, max_tokens, temperature) -> str
    interface. Backend-specific SDK calls are encapsulated here; imports are lazy
    so missing SDKs only raise at runtime when that backend is actually used.
    """

    def __init__(
        self,
        backend: str,
        model_id: str,
        local_url: str = DEFAULT_LOCAL_URL,
    ) -> None:
        self.backend = backend
        self.model_id = model_id
        self.local_url = local_url.rstrip("/")
        self._client = None

    def _init_client(self):
        if self._client is not None:
            return
        if self.backend == "bedrock":
            import boto3
            from botocore.config import Config as BotocoreConfig
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=BEDROCK_REGION,
                config=BotocoreConfig(read_timeout=600, connect_timeout=60),
            )
        elif self.backend == "openai":
            import openai
            self._client = openai.OpenAI()
        elif self.backend == "local":
            import openai
            self._client = openai.OpenAI(
                base_url=f"{self.local_url}/v1",
                api_key="dummy",
            )
        else:
            raise ValueError(f"Unknown backend: {self.backend!r}")

    def complete(
        self,
        prompt: str,
        max_tokens: int = 600,
        temperature: float = 0.1,
    ) -> str:
        """Send prompt and return the text response."""
        self._init_client()

        max_retries = 3
        delay = 10
        for attempt in range(max_retries):
            try:
                return self._complete_once(prompt, max_tokens, temperature)
            except Exception as e:
                err_str = str(e)
                is_rate_limit = "429" in err_str or "rate" in err_str.lower()
                is_conn_error = "ConnectionError" in type(e).__name__ or "connection" in err_str.lower()
                if (is_rate_limit or is_conn_error) and attempt < max_retries - 1:
                    print(f"  [backend] {type(e).__name__} on attempt {attempt+1}, retrying in {delay}s...", file=sys.stderr)
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise

    def _complete_once(self, prompt: str, max_tokens: int, temperature: float) -> str:
        if self.backend == "bedrock":
            response = self._client.converse(
                modelId=self.model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
            )
            return response["output"]["message"]["content"][0]["text"].strip()
        elif self.backend in ("openai", "local"):
            kwargs = {
                "model": self.model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if self.backend == "local":
                kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
            response = self._client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        else:
            raise ValueError(f"Unknown backend: {self.backend!r}")


class _BedrockClientProxy:
    """
    Backwards-compatibility wrapper: wraps a raw boto3 bedrock-runtime client
    and exposes .complete() so it can be used wherever LLMBackend is expected.
    """

    def __init__(self, boto3_client, model_arn: str = BEDROCK_MODEL_ARN) -> None:
        self._client = boto3_client
        self._model_arn = model_arn

    def complete(
        self,
        prompt: str,
        max_tokens: int = 600,
        temperature: float = 0.1,
    ) -> str:
        response = self._client.converse(
            modelId=self._model_arn,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
        )
        return response["output"]["message"]["content"][0]["text"].strip()


# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------

def load_env(env_path: Optional[Path] = None) -> None:
    """Load key=value pairs from .env file into os.environ (no extra deps)."""
    path = env_path or REPO_ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


# ---------------------------------------------------------------------------
# BibTeX parser (minimal — handles author, title, year, doi, url, eprint)
# ---------------------------------------------------------------------------

def parse_bib(bib_path: Path) -> dict[str, dict]:
    """
    Parse a .bib file and return a dict mapping cite_key -> fields dict.
    Fields extracted: type, author, title, year, doi, url, eprint.
    """
    text = bib_path.read_text(encoding="utf-8")
    entries: dict[str, dict] = {}

    # Match each @type{key, ... } block
    entry_pattern = re.compile(
        r"@(\w+)\s*\{\s*([^,\s]+)\s*,\s*(.*?)\n\}",
        re.DOTALL,
    )
    field_pattern = re.compile(
        r"(\w+)\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
        re.DOTALL,
    )

    for m in entry_pattern.finditer(text):
        entry_type = m.group(1).lower()
        cite_key = m.group(2).strip()
        body = m.group(3)

        fields: dict[str, str] = {"type": entry_type}
        for fm in field_pattern.finditer(body):
            fname = fm.group(1).lower().strip()
            fval = fm.group(2).strip()
            # Collapse whitespace and remove LaTeX braces
            fval = re.sub(r"\s+", " ", fval)
            fval = fval.replace("{", "").replace("}", "")
            fields[fname] = fval

        entries[cite_key] = fields

    return entries


# ---------------------------------------------------------------------------
# Citation extractor from markdown text
# ---------------------------------------------------------------------------

def extract_citations_from_text(text: str) -> list[dict]:
    """
    Extract every citation from a markdown document.

    Detects two formats:
    1. Pandoc [@cite-key] anchors — the primary format in all guarded files
       after the 2026-03-24 migration. These are extracted first and matched
       directly to bib keys (no fuzzy surname+year matching needed).
    2. APA prose patterns — retained as a fallback for any citations that lack
       a [@key] anchor (e.g. text written before the migration).

    Returns a list of dicts with:
        raw       — the raw citation text as found
        authors   — list of last names (normalised)
        year      — 4-digit string
        sentence  — the sentence containing the citation (claim context)
        cite_key  — bib cite key (only set for Pandoc anchors; "" for APA prose)
    """
    # Sentence splitter: split on ". " preceded by a lowercase letter or ")".
    # Excludes "et al. " and "e.g. " and similar abbreviations by requiring
    # the period to be preceded by a lowercase letter or closing paren,
    # and followed by an uppercase letter (start of a new sentence).
    sentences = re.split(r"(?<=[a-z\)])\. +(?=[A-Z])", text)

    results: list[dict] = []
    seen: set[str] = set()  # dedup key — cite_key for Pandoc, (authors, year) for APA prose

    # ------------------------------------------------------------------
    # Pass 1: Pandoc [@cite-key] anchors (primary format post-migration)
    # ------------------------------------------------------------------
    # Matches [@key], [@key1; @key2], [-@key], etc.
    # Each key is extracted individually and carries cite_key directly —
    # no surname+year fuzzy matching needed.
    pandoc_bracket_pattern = re.compile(r"\[([^\]]*@[^\]]*)\]")
    pandoc_key_pattern = re.compile(r"-?@([a-zA-Z][a-zA-Z0-9_:\-]+)")

    for bracket_match in pandoc_bracket_pattern.finditer(text):
        bracket_content = bracket_match.group(1)
        for key_match in pandoc_key_pattern.finditer(bracket_content):
            cite_key_raw = key_match.group(1)
            if cite_key_raw in seen:
                continue
            seen.add(cite_key_raw)

            # Find the sentence containing this anchor
            pos = bracket_match.start()
            para_start = text.rfind("\n\n", 0, pos)
            para_start = para_start + 2 if para_start >= 0 else 0
            para_end = text.find("\n\n", pos)
            para_end = para_end if para_end >= 0 else len(text)
            paragraph = text[para_start:para_end].replace("\n", " ").strip()

            para_sentences = re.split(r"(?<=[a-z\)])\. +(?=[A-Z])", paragraph)
            sentence = paragraph
            raw_anchor = bracket_match.group(0)
            for s in para_sentences:
                if raw_anchor in s or cite_key_raw in s:
                    sentence = s.strip()
                    break

            if len(sentence) > 500:
                rel_pos = sentence.find(cite_key_raw)
                if rel_pos >= 0:
                    start_idx = max(0, rel_pos - 100)
                    end_idx = min(len(sentence), rel_pos + 400)
                    sentence = ("..." if start_idx > 0 else "") + sentence[start_idx:end_idx].strip()

            results.append({
                "raw": raw_anchor,
                "authors": [],       # resolved from bib by cite_key
                "year": "",          # resolved from bib by cite_key
                "sentence": sentence,
                "cite_key": cite_key_raw,
            })

    # Track cite keys found via Pandoc anchors so APA prose pass doesn't double-count
    pandoc_keys_found: set[str] = {r["cite_key"] for r in results if r.get("cite_key")}


    # ------------------------------------------------------------------
    # Pass 2: APA prose patterns (fallback for citations without [@key])
    # ------------------------------------------------------------------
    # Pattern groups:
    # 1. (Author et al., YYYY)   — parenthetical "et al."
    # 2. Author et al. (YYYY)    — narrative "et al."
    # 3. (Author, YYYY)          — single author parenthetical
    # 4. Author (YYYY)           — single author narrative
    # 5. (Author1 and Author2, YYYY)  — two-author parenthetical
    # 6. Author1 and Author2 (YYYY)   — two-author narrative
    # 7. (Author1 & Author2, YYYY)    — two-author ampersand parenthetical
    # 8. Author1 & Author2 (YYYY)     — two-author ampersand narrative

    # Patterns ordered from most-specific to least-specific.
    # Multi-author / et-al patterns are processed first so their matched spans
    # can be excluded when single-author patterns run (prevents "Subban (2023)"
    # being extracted spuriously from "Mouton and Subban (2023)").
    citation_patterns = [
        # et al. parenthetical:  (Lastname et al., 2024)
        (re.compile(r"\(([A-Z][a-z]+(?:-[A-Z][a-z]+)?) et al\.,? ([0-9]{4}[a-z]?)\)"),
         "et_al_paren"),
        # et al. narrative:  Lastname et al. (2024)
        (re.compile(r"([A-Z][a-z]+(?:-[A-Z][a-z]+)?) et al\. \(([0-9]{4}[a-z]?)\)"),
         "et_al_narr"),
        # two-author "and" parenthetical:  (Lastname1 and Lastname2, 2024)
        (re.compile(r"\(([A-Z][a-z]+(?:-[A-Z][a-z]+)?) and ([A-Z][a-z]+(?:-[A-Z][a-z]+)?),? ([0-9]{4}[a-z]?)\)"),
         "two_and_paren"),
        # two-author "and" narrative:  Lastname1 and Lastname2 (2024)
        (re.compile(r"([A-Z][a-z]+(?:-[A-Z][a-z]+)?) and ([A-Z][a-z]+(?:-[A-Z][a-z]+)?) \(([0-9]{4}[a-z]?)\)"),
         "two_and_narr"),
        # two-author "&" parenthetical:  (Lastname1 & Lastname2, 2024)
        (re.compile(r"\(([A-Z][a-z]+(?:-[A-Z][a-z]+)?) & ([A-Z][a-z]+(?:-[A-Z][a-z]+)?),? ([0-9]{4}[a-z]?)\)"),
         "two_amp_paren"),
        # single-author parenthetical:  (Lastname, 2024)
        (re.compile(r"\(([A-Z][a-z]+(?:-[A-Z][a-z]+)?),? ([0-9]{4}[a-z]?)\)"),
         "single_paren"),
        # single-author narrative:  Lastname (2024)
        (re.compile(r"\b([A-Z][a-z]+(?:-[A-Z][a-z]+)?) \(([0-9]{4}[a-z]?)\)"),
         "single_narr"),
    ]

    # Collect all matched spans from multi-author / et-al patterns first.
    # Single-author patterns will skip any position overlapping these spans.
    multi_author_kinds = {"et_al_paren", "et_al_narr", "two_and_paren", "two_and_narr", "two_amp_paren"}
    occupied_spans: list[tuple[int, int]] = []
    for pattern, kind in citation_patterns:
        if kind in multi_author_kinds:
            for m in pattern.finditer(text):
                occupied_spans.append((m.start(), m.end()))

    def _overlaps_occupied(start: int, end: int) -> bool:
        return any(s <= start < e or s < end <= e for s, e in occupied_spans)

    for pattern, kind in citation_patterns:
        for m in pattern.finditer(text):
            # Skip single-author matches that fall inside a multi-author span
            if kind not in multi_author_kinds and _overlaps_occupied(m.start(), m.end()):
                continue

            if kind in ("et_al_paren", "et_al_narr"):
                last1, year = m.group(1), m.group(2)
                authors = [last1]
            elif kind in ("two_and_paren", "two_and_narr", "two_amp_paren"):
                last1, last2, year = m.group(1), m.group(2), m.group(3)
                authors = [last1, last2]
            else:
                last1, year = m.group(1), m.group(2)
                authors = [last1]

            year_clean = year[:4]

            # Filter out false positives: month names and common non-author words
            # that happen to be capitalised and precede a parenthesised year.
            FALSE_POSITIVE_WORDS = {
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december",
                "ethics", "figure", "table", "appendix", "chapter", "section",
                "note", "source", "see", "cf", "ibid",
            }
            if any(a.lower() in FALSE_POSITIVE_WORDS for a in authors):
                continue

            key = (tuple(a.lower() for a in authors), year_clean)
            if key in seen:
                continue
            seen.add(key)

            # Find the sentence that contains this exact match position.
            # Strategy: find the nearest sentence boundary before and after pos.
            pos = m.start()
            # Use the paragraph (newline-separated) containing this position
            # as a fallback, then find the sentence within it.
            para_start = text.rfind("\n\n", 0, pos)
            para_start = para_start + 2 if para_start >= 0 else 0
            para_end = text.find("\n\n", pos)
            para_end = para_end if para_end >= 0 else len(text)
            paragraph = text[para_start:para_end].replace("\n", " ").strip()

            # Find the sentence within the paragraph that contains the match.
            para_sentences = re.split(r"(?<=[a-z\)])\. +(?=[A-Z])", paragraph)
            sentence = paragraph  # fallback: use the whole paragraph
            for s in para_sentences:
                if m.group(0) in s or last1 in s:
                    sentence = s.strip()
                    break

            # If sentence is very long (>500 chars), trim to 300 chars around match
            if len(sentence) > 500:
                rel_pos = sentence.find(m.group(0))
                if rel_pos < 0:
                    rel_pos = sentence.find(last1)
                if rel_pos >= 0:
                    start_idx = max(0, rel_pos - 100)
                    end_idx = min(len(sentence), rel_pos + 400)
                    sentence = ("..." if start_idx > 0 else "") + sentence[start_idx:end_idx].strip()

            results.append({
                "raw": m.group(0),
                "authors": authors,
                "year": year_clean,
                "sentence": sentence,
                "cite_key": "",  # resolved later by resolve_cite_key()
            })

    # ------------------------------------------------------------------
    # Pass 3: Bare @key narrative form (post-migration pure Pandoc standard)
    # ------------------------------------------------------------------
    # Matches @key NOT preceded by '[' — i.e. narrative form used as:
    #   @lewis-2020-rag demonstrate that RAG reduces hallucination.
    # Keys already detected by Pass 1 ([@key]) are skipped to avoid duplication.
    bare_at_key_pattern = re.compile(
        r"(?<!\[)@([a-z][a-z]+-(?:19|20)\d{2}-[a-z][a-z0-9]+(?:-[a-z][a-z0-9]+)*)"
    )
    for m in bare_at_key_pattern.finditer(text):
        cite_key_raw = m.group(1)
        if cite_key_raw in seen:
            continue
        seen.add(cite_key_raw)

        # Find the sentence containing this anchor (same logic as Pass 1)
        pos = m.start()
        para_start = text.rfind("\n\n", 0, pos)
        para_start = para_start + 2 if para_start >= 0 else 0
        para_end = text.find("\n\n", pos)
        para_end = para_end if para_end >= 0 else len(text)
        paragraph = text[para_start:para_end].replace("\n", " ").strip()

        para_sentences = re.split(r"(?<=[a-z\)])\. +(?=[A-Z])", paragraph)
        sentence = paragraph
        raw_anchor = m.group(0)
        for s in para_sentences:
            if raw_anchor in s or cite_key_raw in s:
                sentence = s.strip()
                break

        if len(sentence) > 500:
            rel_pos = sentence.find(cite_key_raw)
            if rel_pos >= 0:
                start_idx = max(0, rel_pos - 100)
                end_idx = min(len(sentence), rel_pos + 400)
                sentence = ("..." if start_idx > 0 else "") + sentence[start_idx:end_idx].strip()

        results.append({
            "raw": raw_anchor,
            "authors": [],
            "year": "",
            "sentence": sentence,
            "cite_key": cite_key_raw,
        })

    return results


# ---------------------------------------------------------------------------
# Cite-key resolver: match extracted citation to a bib entry
# ---------------------------------------------------------------------------

def resolve_cite_key(citation: dict, bib_entries: dict[str, dict]) -> Optional[str]:
    """
    Try to match a citation dict (authors, year) to a bib cite key.

    Strategy (in priority order):
    1. Exact first-author match + year: the first author in the bib entry's
       author field must start with (or match) the citation's first author name.
    2. Fallback: any author in the bib entry field contains the name + year.

    This prevents Karpukhin (2020) resolving to lewis-2020-rag just because
    Karpukhin is a co-author on that paper.
    """
    first_author_lower = citation["authors"][0].lower()
    all_authors_lower = [a.lower() for a in citation["authors"]]
    year = citation["year"]

    # Pass 1: first-author match
    for cite_key, fields in bib_entries.items():
        if fields.get("year", "") != year:
            continue
        author_field = fields.get("author", "").lower()
        # The bib author field starts with "Lastname, Firstname and ..." or
        # "Firstname Lastname and ...". We extract the first surname token.
        first_bib_author = author_field.split(",")[0].split(" and ")[0].strip()
        # Check if the first bib author contains the citation's first author name
        if first_author_lower in first_bib_author:
            # For two-author citations, also verify the second author is present
            if len(all_authors_lower) == 1 or all(a in author_field for a in all_authors_lower[1:]):
                return cite_key

    # Pass 2: fallback — any author match (for cases like "Es et al." where
    # first author is a short name that might not be first in the bib)
    for cite_key, fields in bib_entries.items():
        if fields.get("year", "") != year:
            continue
        author_field = fields.get("author", "").lower()
        if all(a in author_field for a in all_authors_lower):
            return cite_key

    return None


# ---------------------------------------------------------------------------
# mkv file finder
# ---------------------------------------------------------------------------

def find_mkv_file(cite_key: str, bib_entry: dict, mkv_dir: Path) -> Optional[Path]:
    """
    Find the markdown conversion for a cite key.

    All files in literature/mkv/ must be named <cite-key>.md (enforced by
    the project naming convention — see literature/README.md). This function
    therefore does an exact cite-key lookup only. No fuzzy fallback: a fuzzy
    match could silently return the wrong paper's content, which is worse than
    a clean miss that the caller handles explicitly.
    """
    exact = mkv_dir / f"{cite_key}.md"
    return exact if exact.exists() else None


# ---------------------------------------------------------------------------
# Auto-fetch: download PDF and convert via Anthropic API
# ---------------------------------------------------------------------------

def fetch_paper_via_doi(cite_key: str, bib_entry: dict, mkv_dir: Path) -> Optional[Path]:
    """
    Try to download a paper PDF (via DOI/arXiv) and convert it to markdown
    using the Anthropic API. Returns the mkv path on success, None on failure.

    Tries in order: arXiv eprint, arXiv URL, DOI via Sci-Hub.

    On success, saves:
      literature/papers/<cite-key>.pdf  — the downloaded PDF
      literature/mkv/<cite-key>.md      — the Markdown conversion
    Both use the cite key as the filename stem, consistent with the project
    naming convention (see literature/README.md).
    """
    import base64

    title = bib_entry.get("title", cite_key)
    doi = bib_entry.get("doi", "")
    url = bib_entry.get("url", "")
    eprint = bib_entry.get("eprint", "")

    arxiv_id = None
    if eprint:
        arxiv_id = eprint.strip()
    elif url and "arxiv.org" in url:
        m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]+)", url)
        if m:
            arxiv_id = m.group(1)

    pdf_path = None
    tmp_pdf = Path(f"/tmp/{cite_key}.pdf")

    # Try arXiv PDF first
    if arxiv_id:
        arxiv_pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        print(f"  [fetch] Downloading arXiv PDF: {arxiv_pdf_url}", file=sys.stderr)
        result = subprocess.run(
            ["curl", "-L", "-s", "-o", str(tmp_pdf), arxiv_pdf_url],
            capture_output=True, timeout=60,
        )
        if result.returncode == 0 and tmp_pdf.stat().st_size > 10000:
            pdf_path = tmp_pdf
        else:
            print(f"  [fetch] arXiv download failed or too small", file=sys.stderr)

    # Try Sci-Hub via DOI if arXiv failed
    if not pdf_path and doi:
        scihub_url = f"https://sci-hub.se/{doi}"
        print(f"  [fetch] Trying Sci-Hub: {scihub_url}", file=sys.stderr)
        result = subprocess.run(
            ["curl", "-L", "-s", "-o", str(tmp_pdf), scihub_url],
            capture_output=True, timeout=60,
        )
        if result.returncode == 0 and tmp_pdf.exists() and tmp_pdf.stat().st_size > 10000:
            content = tmp_pdf.read_bytes()
            if content[:4] == b"%PDF":
                pdf_path = tmp_pdf
            else:
                print(f"  [fetch] Sci-Hub returned HTML, not PDF", file=sys.stderr)

    if not pdf_path:
        print(f"  [fetch] Could not obtain PDF for {cite_key}", file=sys.stderr)
        return None

    # Save PDF to literature/papers/<cite-key>.pdf (completing the three-way link)
    papers_dir = REPO_ROOT / "literature" / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)
    permanent_pdf = papers_dir / f"{cite_key}.pdf"
    import shutil
    shutil.copy2(pdf_path, permanent_pdf)
    print(f"  [fetch] Saved PDF to {permanent_pdf}", file=sys.stderr)

    # Convert PDF to markdown via Bedrock streaming
    # (invoke_model_with_response_stream required — invoke_model times out on
    #  long PDFs; the application inference profile ARN is used directly)
    print(f"  [convert] Converting PDF to markdown via Bedrock streaming...", file=sys.stderr)
    try:
        import boto3
        from botocore.config import Config as BotocoreConfig

        bedrock = boto3.client(
            "bedrock-runtime",
            region_name=BEDROCK_REGION,
            config=BotocoreConfig(read_timeout=600, connect_timeout=60),
        )
        pdf_b64 = base64.standard_b64encode(pdf_path.read_bytes()).decode("ascii")
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 64000,
            "messages": [{"role": "user", "content": [
                {"type": "document", "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_b64,
                }},
                {"type": "text", "text": (
                    "Convert this academic paper to clean Markdown. "
                    "Preserve all sections and headings. Render equations in LaTeX. "
                    "Include all tables, figure captions, and footnotes. "
                    "Do not summarise — output the full paper text verbatim."
                )},
            ]}],
        })
        response = bedrock.invoke_model_with_response_stream(
            modelId=BEDROCK_MODEL_ARN, body=body
        )
        chunks = []
        for event in response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if chunk.get("type") == "content_block_delta":
                chunks.append(chunk["delta"].get("text", ""))
        converted = "".join(chunks)

        # Save mkv as <cite-key>.md — cite-key naming convention (literature/README.md)
        out_path = mkv_dir / f"{cite_key}.md"
        out_path.write_text(converted, encoding="utf-8")
        print(f"  [convert] Saved mkv to {out_path} ({len(converted)} chars)", file=sys.stderr)
        return out_path

    except Exception as e:
        print(f"  [convert] Failed: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Strong verifier — Bedrock Sonnet 4.6
# ---------------------------------------------------------------------------

def _parse_json_response(raw: str, fallback_verdict: str = "NEEDS_VERIFICATION") -> dict:
    """Parse a JSON response from the LLM, with fallback on parse failure."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return {
            "verdict": fallback_verdict,
            "confidence": 1,
            "supporting_quote": "",
            "reasoning": f"Failed to parse verifier response: {raw[:200]}",
        }


def verify_claim(
    claim_sentence: str,
    cite_key: str,
    bib_entry: dict,
    mkv_text: str,
    llm_backend=None,
    model_arn: str = BEDROCK_MODEL_ARN,
    tier_aware: bool = False,
    tier_architecture: str = "C",
    bedrock_client=None,
) -> dict:
    """
    Verify a claim against source text. Returns a dict with:
    verdict, confidence, supporting_quote, reasoning, claim_tier (None if not tier-aware).

    Backends:
    - llm_backend: an LLMBackend (or _BedrockClientProxy) instance (preferred)
    - bedrock_client: legacy boto3 client (backwards compat — wrapped in _BedrockClientProxy)

    tier_aware=False (default): uses VERIFICATION_PROMPT_TEMPLATE (Phase 1 behaviour).
    tier_aware=True, tier_architecture="A": classify then verify with generic prompt.
    tier_aware=True, tier_architecture="B": single combined prompt (OPTION_B).
    tier_aware=True, tier_architecture="C": classify then verify with T1/T2/T3 template.
    """
    # Backwards compat: wrap old bedrock_client param
    if llm_backend is None:
        if bedrock_client is not None:
            llm_backend = _BedrockClientProxy(bedrock_client, model_arn)
        else:
            raise ValueError("Either llm_backend or bedrock_client must be provided")

    # Truncate source text to stay within token budget (~6000 words)
    words = mkv_text.split()
    if len(words) > 6000:
        mkv_text = " ".join(words[:6000]) + "\n\n[... text truncated ...]"

    title = bib_entry.get("title", cite_key)
    authors = bib_entry.get("author", "Unknown")
    year = bib_entry.get("year", "?")

    source_kwargs = dict(
        source_title=title,
        source_authors=authors,
        source_year=year,
        source_text=mkv_text,
    )

    claim_tier = None

    # --- No tier-awareness (Phase 1 default) ---
    if not tier_aware:
        prompt = VERIFICATION_PROMPT_TEMPLATE.format(claim=claim_sentence, **source_kwargs)
        raw = llm_backend.complete(prompt, max_tokens=600, temperature=0.1)
        result = _parse_json_response(raw)
        result["claim_tier"] = None
        v = result.get("verdict", "").upper()
        if v not in ("VERIFIED", "NEEDS_VERIFICATION", "NO_SOURCE"):
            result["verdict"] = "NEEDS_VERIFICATION"
        return result

    # --- Option B: single combined prompt ---
    if tier_architecture == "B":
        prompt = VERIFICATION_PROMPT_OPTION_B.format(claim=claim_sentence, **source_kwargs)
        raw = llm_backend.complete(prompt, max_tokens=800, temperature=0.1)
        result = _parse_json_response(raw)
        # Normalise tier field
        tier_raw = result.get("claim_tier", "")
        if tier_raw not in ("T1_EMPIRICAL", "T2_SYNTHESIS", "T3_APPLICATION"):
            result["claim_tier"] = "T2_SYNTHESIS"
        v = result.get("verdict", "").upper()
        if v not in ("VERIFIED", "NEEDS_VERIFICATION", "NO_SOURCE"):
            result["verdict"] = "NEEDS_VERIFICATION"
        return result

    # --- Options A and C: classify first, then verify ---
    classify_prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(claim=claim_sentence)
    classify_raw = llm_backend.complete(classify_prompt, max_tokens=150, temperature=0.01)
    classify_result = _parse_json_response(classify_raw, fallback_verdict="T2_SYNTHESIS")

    tier_raw = classify_result.get("tier", "")
    if tier_raw not in ("T1_EMPIRICAL", "T2_SYNTHESIS", "T3_APPLICATION"):
        claim_tier = "T2_SYNTHESIS"  # safe fallback
    else:
        claim_tier = tier_raw

    if tier_architecture == "A":
        # Option A: generic verification prompt after classification
        verify_prompt = VERIFICATION_PROMPT_TEMPLATE.format(claim=claim_sentence, **source_kwargs)
        max_tok = 600
    else:
        # Option C: tier-specific verification prompt
        tier_templates = {
            "T1_EMPIRICAL": VERIFICATION_PROMPT_T1,
            "T2_SYNTHESIS": VERIFICATION_PROMPT_T2,
            "T3_APPLICATION": VERIFICATION_PROMPT_T3,
        }
        verify_prompt = tier_templates[claim_tier].format(claim=claim_sentence, **source_kwargs)
        max_tok = 600

    raw = llm_backend.complete(verify_prompt, max_tokens=max_tok, temperature=0.1)
    result = _parse_json_response(raw)
    result["claim_tier"] = claim_tier
    v = result.get("verdict", "").upper()
    if v not in ("VERIFIED", "NEEDS_VERIFICATION", "NO_SOURCE"):
        result["verdict"] = "NEEDS_VERIFICATION"
    return result


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_report(
    results: list[dict],
    output_dir: Path,
    context_files: list[str],
) -> tuple[Path, Path]:
    """Write full report and summary to output_dir. Returns (report_path, summary_path)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Aggregate stats
    total = len(results)
    verified = sum(1 for r in results if r["verdict"] == "VERIFIED")
    needs_check = sum(1 for r in results if r["verdict"] == "NEEDS_VERIFICATION")
    no_source = sum(1 for r in results if r["verdict"] == "NO_SOURCE")
    skipped = sum(1 for r in results if r["verdict"] == "SKIPPED")

    lines: list[str] = []
    lines.append("# Citation Verification Report\n")
    lines.append(f"**Context files:** {', '.join(context_files)}\n")
    lines.append(f"**Total citations analysed:** {total}\n")
    lines.append(f"- VERIFIED: {verified}\n")
    lines.append(f"- NEEDS_VERIFICATION: {needs_check}\n")
    lines.append(f"- NO_SOURCE: {no_source}\n")
    lines.append(f"- SKIPPED (no mkv file + fetch disabled or failed): {skipped}\n")
    lines.append("\n---\n\n")

    # Group by verdict for scan-readability
    for verdict_label in ("NO_SOURCE", "NEEDS_VERIFICATION", "VERIFIED", "SKIPPED"):
        group = [r for r in results if r["verdict"] == verdict_label]
        if not group:
            continue
        emoji = {"VERIFIED": "✅", "NEEDS_VERIFICATION": "⚠️", "NO_SOURCE": "❌", "SKIPPED": "⏭️"}[verdict_label]
        lines.append(f"## {emoji} {verdict_label} ({len(group)})\n\n")
        for r in group:
            lines.append(f"### {r['cite_key']} — {r['raw_citation']}\n\n")
            lines.append(f"**Claim sentence:** {r['claim_sentence']}\n\n")
            if r["verdict"] == "SKIPPED":
                lines.append(f"**Reason:** {r.get('skip_reason', 'No mkv file found')}\n\n")
            else:
                lines.append(f"**Source:** {r.get('source_title', '?')} ({r.get('source_year', '?')})\n\n")
                lines.append(f"**Confidence:** {r.get('confidence', '?')}/5\n\n")
                if r.get("supporting_quote"):
                    lines.append(f"**Supporting quote:** \"{r['supporting_quote']}\"\n\n")
                lines.append(f"**Reasoning:** {r.get('reasoning', '')}\n\n")
            lines.append("---\n\n")

    report_path = output_dir / "verification-report.md"
    report_path.write_text("".join(lines), encoding="utf-8")

    # One-line summary
    summary_lines: list[str] = ["# Verification Summary\n\n"]
    summary_lines.append("| Cite Key | Raw Citation | Verdict | Confidence |\n")
    summary_lines.append("|----------|-------------|---------|------------|\n")
    for r in results:
        summary_lines.append(
            f"| {r['cite_key']} | {r['raw_citation']} | {r['verdict']} | {r.get('confidence', '-')} |\n"
        )
    summary_path = output_dir / "verification-summary.md"
    summary_path.write_text("".join(summary_lines), encoding="utf-8")

    return report_path, summary_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Strong citation verification for the PhD proposal."
    )
    p.add_argument(
        "--context", nargs="+", required=True,
        help="One or more markdown files to extract and verify citations from.",
    )
    p.add_argument(
        "--bib", default="literature/references.bib",
        help="Path to the BibTeX database. Default: literature/references.bib",
    )
    p.add_argument(
        "--mkv-dir", default="literature/mkv",
        help="Directory containing markdown conversions. Default: literature/mkv/",
    )
    p.add_argument(
        "--output-dir", default="pipeline-outputs",
        help="Output directory for the report. Default: pipeline-outputs/",
    )
    p.add_argument(
        "--auto-fetch", action="store_true",
        help=(
            "Auto-fetch and convert missing papers via DOI/arXiv using Bedrock streaming. "
            "Tries arXiv first, then Sci-Hub via DOI. "
            "NOTE: Sabinet/journals.co.za papers cannot be auto-fetched (Cloudflare) — "
            "download manually via Chrome and place in literature/papers/<cite-key>.pdf."
        ),
    )
    p.add_argument(
        "--env-file", default=None,
        help="Path to .env file. Default: <repo_root>/.env",
    )
    p.add_argument(
        "--model-arn", default=None,
        help=(
            "Override the Bedrock model ARN used for verification. "
            "Default: BEDROCK_MODEL_ARN (Sonnet 4.6 application inference profile). "
            "Use to switch to Haiku for cost comparison: pass the HAIKU_ARN value. "
            "Alias for --model when --backend bedrock."
        ),
    )
    p.add_argument(
        "--backend", choices=["bedrock", "openai", "local"], default="bedrock",
        help="LLM backend to use. Default: bedrock",
    )
    p.add_argument(
        "--model", default=None,
        help=(
            "Model ID for the selected backend. "
            "Defaults: bedrock=BEDROCK_MODEL_ARN, openai=gpt-4o, local=Qwen3.5-35B-A3B"
        ),
    )
    p.add_argument(
        "--local-url", default=DEFAULT_LOCAL_URL,
        help=f"Base URL for local backend. Default: {DEFAULT_LOCAL_URL}",
    )
    p.add_argument(
        "--tier-aware", action="store_true", default=True,
        help="Enable tier-aware verification (default: on). Pass --no-tier-aware to disable.",
    )
    p.add_argument(
        "--no-tier-aware", dest="tier_aware", action="store_false",
        help="Disable tier-aware verification (reverts to Phase 1 generic prompt).",
    )
    p.add_argument(
        "--tier-architecture", choices=["A", "B", "C"], default="C",
        help=(
            "Tier-aware architecture (only used when --tier-aware is set). "
            "A=two-pass generic, B=single combined prompt, C=two-pass tier-specific. Default: C"
        ),
    )
    p.add_argument(
        "--pipeline", choices=["single", "two-stage"], default="single",
        help=(
            "Verification pipeline mode. "
            "'single': one model for all claims (default). "
            "'two-stage': run local Qwen35 Arch C first (free); escalate NO_SOURCE to "
            "Haiku Arch C. Requires HAIKU_ARN in .env and --backend local reachable. "
            "Best cost/accuracy tradeoff for large corpora."
        ),
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Orchestration — callable by pipeline or CLI
# ---------------------------------------------------------------------------

def run_verification(
    context_files: list[str],
    output_dir: Path,
    bib_path: Path,
    mkv_dir: Path,
    auto_fetch: bool = False,
    model_arn: str = BEDROCK_MODEL_ARN,
    llm_backend=None,
    tier_aware: bool = False,
    tier_architecture: str = "C",
    bedrock_client=None,
    pipeline: str = "single",
) -> tuple[list[dict], Path, Path]:
    """
    Run the full citation verification pipeline.

    Returns (results, report_path, summary_path).
    results is a list of dicts with keys: cite_key, raw_citation,
    claim_sentence, verdict, confidence, supporting_quote, reasoning,
    source_title, source_year, claim_tier.

    llm_backend: an LLMBackend instance (preferred).
    bedrock_client: legacy boto3 client (backwards compat — wrapped automatically).
    pipeline: 'single' (default) or 'two-stage'.
      'two-stage': Stage 1 uses llm_backend (expected: local Qwen35 Arch C).
        Any NO_SOURCE result is re-verified with Haiku Arch C (HAIKU_ARN from env).
        Haiku verdict takes precedence over Qwen NO_SOURCE. Both verdicts recorded.

    Raises no SystemExit — callers decide what to do with the results.
    """
    # Backwards compat: old callers pass bedrock_client= positionally or as keyword
    if llm_backend is None:
        if bedrock_client is not None:
            llm_backend = _BedrockClientProxy(bedrock_client, model_arn)
        else:
            raise ValueError("Either llm_backend or bedrock_client must be provided")
    if not bib_path.exists():
        raise FileNotFoundError(f"BibTeX file not found: {bib_path}")
    if not mkv_dir.exists():
        raise FileNotFoundError(f"mkv directory not found: {mkv_dir}")

    # Parse bib
    print(f"[step 1] Parsing {bib_path.name}...", file=sys.stderr)
    bib_entries = parse_bib(bib_path)
    print(f"         {len(bib_entries)} entries loaded", file=sys.stderr)

    # Load and combine context files
    print(f"[step 2] Extracting citations from {len(context_files)} file(s)...", file=sys.stderr)
    all_citations: list[dict] = []
    seen_keys: set = set()

    for ctx_file in context_files:
        ctx_path = Path(ctx_file)
        if not ctx_path.exists():
            print(f"  WARNING: context file not found: {ctx_path}", file=sys.stderr)
            continue
        text = ctx_path.read_text(encoding="utf-8")
        cits = extract_citations_from_text(text)
        print(f"  {ctx_path.name}: {len(cits)} unique citations found", file=sys.stderr)
        for c in cits:
            # Pandoc anchors carry a direct cite_key — use it as the dedup key.
            # APA prose citations dedup on (authors, year) tuple.
            if c.get("cite_key"):
                dedup_key = ("__pandoc__", c["cite_key"])
            else:
                dedup_key = (tuple(a.lower() for a in c["authors"]), c["year"])
            if dedup_key not in seen_keys:
                seen_keys.add(dedup_key)
                all_citations.append(c)

    print(f"         {len(all_citations)} unique citations total", file=sys.stderr)

    if not all_citations:
        print("No citations found in context files.", file=sys.stderr)
        report_path, summary_path = write_report([], output_dir, context_files)
        return [], report_path, summary_path

    # Resolve each citation to a bib entry and mkv file, then verify
    print(f"\n[step 3] Resolving and verifying citations...\n", file=sys.stderr)
    results: list[dict] = []
    processed_cite_keys: set[str] = set()  # prevent double-verification if APA duplicates a Pandoc anchor

    for i, cit in enumerate(all_citations, 1):
        raw = cit["raw"]
        print(f"  [{i}/{len(all_citations)}] {raw}", file=sys.stderr)

        # Pandoc [@cite-key] anchors carry the key directly; APA prose citations
        # go through fuzzy surname+year matching.
        if cit.get("cite_key"):
            cite_key = cit["cite_key"]
            if cite_key not in bib_entries:
                print(f"           → [@{cite_key}] not found in references.bib", file=sys.stderr)
                results.append({
                    "cite_key": cite_key,
                    "raw_citation": raw,
                    "claim_sentence": cit["sentence"],
                    "verdict": "NO_SOURCE",
                    "confidence": 0,
                    "supporting_quote": "",
                    "reasoning": f"[@{cite_key}] not found in references.bib — possible missing or misspelled cite key",
                    "source_title": "",
                    "source_year": "",
                    "claim_tier": None,
                })
                continue
        else:
            cite_key = resolve_cite_key(cit, bib_entries)
            # Skip APA prose match if the same cite_key was already verified
            # via a Pandoc [@key] anchor (avoids duplicate Bedrock API calls).
            if cite_key and cite_key in processed_cite_keys:
                print(f"           → {cite_key}: already verified via [@key] anchor — skipping", file=sys.stderr)
                continue
        if not cite_key:
            print(f"           → No bib entry found", file=sys.stderr)
            results.append({
                "cite_key": "UNRESOLVED",
                "raw_citation": raw,
                "claim_sentence": cit["sentence"],
                "verdict": "NO_SOURCE",
                "confidence": 0,
                "supporting_quote": "",
                "reasoning": "Could not match citation to any entry in references.bib",
                "source_title": "",
                "source_year": "",
                "claim_tier": None,
            })
            continue

        bib_entry = bib_entries[cite_key]
        source_title = bib_entry.get("title", cite_key)
        source_year = bib_entry.get("year", "?")
        print(f"           → {cite_key}: {source_title[:60]}...", file=sys.stderr)

        mkv_file = find_mkv_file(cite_key, bib_entry, mkv_dir)
        if not mkv_file:
            if auto_fetch:
                print(f"           → No mkv file — attempting auto-fetch...", file=sys.stderr)
                mkv_file = fetch_paper_via_doi(cite_key, bib_entry, mkv_dir)
                if mkv_file:
                    time.sleep(65)
            if not mkv_file:
                print(f"           → SKIPPED (no source text available)", file=sys.stderr)
                results.append({
                    "cite_key": cite_key,
                    "raw_citation": raw,
                    "claim_sentence": cit["sentence"],
                    "verdict": "SKIPPED",
                    "confidence": 0,
                    "supporting_quote": "",
                    "reasoning": "",
                    "source_title": source_title,
                    "source_year": source_year,
                    "skip_reason": "No mkv file found and --auto-fetch not enabled or fetch failed",
                    "claim_tier": None,
                })
                continue

        mkv_text = mkv_file.read_text(encoding="utf-8")

        tier_label = f" [{tier_architecture}]" if tier_aware else ""
        print(f"           → Verifying against {mkv_file.name}{tier_label}...", file=sys.stderr)
        try:
            verdict = verify_claim(
                claim_sentence=cit["sentence"],
                cite_key=cite_key,
                bib_entry=bib_entry,
                mkv_text=mkv_text,
                llm_backend=llm_backend,
                tier_aware=tier_aware,
                tier_architecture=tier_architecture,
            )
        except Exception as e:
            print(f"           → Verifier error: {e}", file=sys.stderr)
            verdict = {
                "verdict": "NEEDS_VERIFICATION",
                "confidence": 0,
                "supporting_quote": "",
                "reasoning": f"API error during verification: {e}",
                "claim_tier": None,
            }

        v_symbol = {"VERIFIED": "✅", "NEEDS_VERIFICATION": "⚠️", "NO_SOURCE": "❌"}.get(
            verdict["verdict"], "?"
        )
        tier_info = f" tier={verdict.get('claim_tier')}" if tier_aware else ""
        print(f"           → {v_symbol} {verdict['verdict']} (confidence {verdict.get('confidence', '?')}/5){tier_info}", file=sys.stderr)

        processed_cite_keys.add(cite_key)
        results.append({
            "cite_key": cite_key,
            "raw_citation": raw,
            "claim_sentence": cit["sentence"],
            "verdict": verdict["verdict"],
            "confidence": verdict.get("confidence", 0),
            "supporting_quote": verdict.get("supporting_quote", ""),
            "reasoning": verdict.get("reasoning", ""),
            "source_title": source_title,
            "source_year": source_year,
            "claim_tier": verdict.get("claim_tier"),
        })

    # Two-stage escalation: re-verify NO_SOURCE claims with Haiku Arch C
    if pipeline == "two-stage":
        haiku_arn = os.environ.get("HAIKU_ARN", "")
        no_source_indices = [
            i for i, r in enumerate(results) if r["verdict"] == "NO_SOURCE"
        ]
        if no_source_indices and haiku_arn:
            print(
                f"\n[step 3b] Two-stage escalation: {len(no_source_indices)} NO_SOURCE claim(s) → Haiku Arch C...\n",
                file=sys.stderr,
            )
            haiku_backend = LLMBackend(
                backend="bedrock", model_id=haiku_arn, local_url=DEFAULT_LOCAL_URL
            )
            for idx in no_source_indices:
                r = results[idx]
                cite_key = r["cite_key"]
                if cite_key in ("UNRESOLVED",) or not r.get("source_title"):
                    continue  # skip unresolvable entries
                bib_entry = bib_entries.get(cite_key)
                if not bib_entry:
                    continue
                mkv_file = find_mkv_file(cite_key, bib_entry, mkv_dir)
                if not mkv_file:
                    continue
                mkv_text = mkv_file.read_text(encoding="utf-8")
                print(
                    f"  [{cite_key}] escalating to Haiku Arch C...", file=sys.stderr
                )
                try:
                    verdict2 = verify_claim(
                        claim_sentence=r["claim_sentence"],
                        cite_key=cite_key,
                        bib_entry=bib_entry,
                        mkv_text=mkv_text,
                        llm_backend=haiku_backend,
                        tier_aware=True,
                        tier_architecture="C",
                    )
                except Exception as e:
                    print(f"  [{cite_key}] Haiku escalation error: {e}", file=sys.stderr)
                    continue
                v2 = verdict2["verdict"]
                v_symbol = {"VERIFIED": "✅", "NEEDS_VERIFICATION": "⚠️", "NO_SOURCE": "❌"}.get(v2, "?")
                print(
                    f"  [{cite_key}] Haiku: {v_symbol} {v2} (confidence {verdict2.get('confidence', '?')}/5)",
                    file=sys.stderr,
                )
                # Record Stage 1 result, update with Stage 2
                results[idx]["stage1_verdict"] = "NO_SOURCE"
                results[idx]["stage1_reasoning"] = r["reasoning"]
                results[idx]["verdict"] = v2
                results[idx]["confidence"] = verdict2.get("confidence", 0)
                results[idx]["supporting_quote"] = verdict2.get("supporting_quote", "")
                results[idx]["reasoning"] = (
                    f"[Stage 2 — Haiku Arch C] {verdict2.get('reasoning', '')}"
                )
                results[idx]["claim_tier"] = verdict2.get("claim_tier")
        elif no_source_indices and not haiku_arn:
            print(
                f"\n[step 3b] WARNING: two-stage requested but HAIKU_ARN not set — skipping escalation",
                file=sys.stderr,
            )

    # Write reports
    print(f"\n[step 4] Writing reports to {output_dir}/...", file=sys.stderr)
    report_path, summary_path = write_report(results, output_dir, context_files)
    return results, report_path, summary_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    load_env(Path(args.env_file) if args.env_file else None)

    # Resolve model ID: --model-arn is a legacy alias for --model when --backend bedrock.
    # When backend=bedrock and tier_aware=True, prefer HAIKU_ARN from env (cheaper, same accuracy).
    haiku_arn = os.environ.get("HAIKU_ARN", "")
    bedrock_default = haiku_arn if (args.tier_aware and haiku_arn) else BEDROCK_MODEL_ARN
    model_id = args.model or args.model_arn or (
        bedrock_default if args.backend == "bedrock" else DEFAULT_MODELS.get(args.backend, BEDROCK_MODEL_ARN)
    )

    # Pre-flight check for local backend
    if args.backend == "local":
        import urllib.request
        ping_url = f"{args.local_url}/v1/models"
        try:
            with urllib.request.urlopen(ping_url, timeout=5):
                pass
        except Exception as e:
            sys.exit(f"ERROR: local backend not reachable at {ping_url}: {e}")

    backend = LLMBackend(
        backend=args.backend,
        model_id=model_id,
        local_url=args.local_url,
    )

    # For two-stage pipeline, --tier-aware is implicitly on (Stage 1 = Arch C)
    tier_aware = args.tier_aware or (args.pipeline == "two-stage")

    try:
        results, report_path, summary_path = run_verification(
            context_files=args.context,
            llm_backend=backend,
            output_dir=REPO_ROOT / args.output_dir,
            bib_path=REPO_ROOT / args.bib,
            mkv_dir=REPO_ROOT / args.mkv_dir,
            auto_fetch=args.auto_fetch,
            model_arn=model_id,
            tier_aware=tier_aware,
            tier_architecture=args.tier_architecture,
            pipeline=args.pipeline,
        )
    except FileNotFoundError as e:
        sys.exit(f"ERROR: {e}")

    total = len(results)
    verified = sum(1 for r in results if r["verdict"] == "VERIFIED")
    needs_check = sum(1 for r in results if r["verdict"] == "NEEDS_VERIFICATION")
    no_source = sum(1 for r in results if r["verdict"] == "NO_SOURCE")
    skipped = sum(1 for r in results if r["verdict"] == "SKIPPED")

    print(f"\n{'=' * 50}")
    print(f"CITATION VERIFICATION COMPLETE")
    print(f"{'=' * 50}")
    print(f"  Total:              {total}")
    print(f"  ✅ VERIFIED:         {verified}")
    print(f"  ⚠️  NEEDS_VERIFICATION: {needs_check}")
    print(f"  ❌ NO_SOURCE:        {no_source}")
    print(f"  ⏭️  SKIPPED:          {skipped}")
    print(f"\nReport: {report_path}")
    print(f"Summary: {summary_path}")
    print(f"{'=' * 50}\n")

    if needs_check > 0 or no_source > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
