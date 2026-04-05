"""Download a YouTube video's audio, transcribe it, and create a radar note.

Usage::

    python scripts/transcribe-youtube.py <url> \\
        [--slug my-slug] \\
        [--relevance "why this matters"] \\
        [--transcript-dir /tmp/transcripts] \\
        [--model mlx-community/whisper-base.en-mlx]

Output:
  literature/radar/<slug>.md          — structured radar note
  <transcript-dir>/<slug>.txt         — raw transcript (default: literature/radar/transcripts/)

Requires: yt-dlp, mlx-whisper, boto3 (all in unisa-phd-proposal conda env)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RADAR_DIR = REPO_ROOT / "literature" / "radar"
DEFAULT_TRANSCRIPT_DIR = RADAR_DIR / "transcripts"

BEDROCK_MODEL_ID = "arn:aws:bedrock:eu-west-1:557116085116:application-inference-profile/vb6ydtnx7fbs"

RESEARCH_CONTEXT = """
PhD research: Design and Evaluation of a Retrieval-Augmented Generation (RAG) System
for Supporting Self-Directed Learning in Open Distance e-Learning (ODeL) Environments.
Methodology: Design Science Research (Hevner et al. 2004).
Core topics: RAG architecture, BM25 vs dense retrieval, student self-directed learning,
ODeL infrastructure, LLM hallucination, educational chatbots, formative feedback,
UNISA (University of South Africa) context.
"""


# ---------------------------------------------------------------------------
# yt-dlp helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert a string to a lowercase hyphen-separated slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text.strip())
    return text[:80]


def fetch_video_metadata(url: str) -> dict:
    """Fetch video metadata via yt-dlp without downloading audio."""
    yt_dlp_bin = _find_yt_dlp()
    result = subprocess.run(
        [yt_dlp_bin, "--dump-json", "--no-playlist", url],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    upload_date = data.get("upload_date", "")
    if upload_date and len(upload_date) == 8:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    return {
        "title": data.get("title", "Unknown"),
        "uploader": data.get("uploader") or data.get("channel", ""),
        "channel": data.get("channel") or data.get("uploader", ""),
        "upload_date": upload_date,
        "duration_string": data.get("duration_string", ""),
        "platform": "YouTube",
    }


def download_audio(url: str, output_template: Path) -> Path:
    """Download audio-only stream as MP3 to output_template path."""
    yt_dlp_bin = _find_yt_dlp()
    print(f"Downloading audio ...")
    subprocess.run(
        [
            yt_dlp_bin,
            "--no-playlist",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--output", str(output_template),
            url,
        ],
        check=True,
    )
    mp3 = output_template.with_suffix(".mp3")
    if mp3.exists():
        return mp3
    return output_template


def _find_yt_dlp() -> str:
    """Return path to yt-dlp binary, preferring the current env."""
    env_bin = Path(sys.executable).parent / "yt-dlp"
    if env_bin.exists():
        return str(env_bin)
    # Fall back to PATH
    result = subprocess.run(["which", "yt-dlp"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    print("ERROR: yt-dlp not found. Run: make setup", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# MLX Whisper transcription
# ---------------------------------------------------------------------------

def transcribe_audio(audio_path: Path, model: str) -> str:
    """Transcribe audio file using mlx_whisper; return plain text."""
    try:
        from mlx_whisper import transcribe
    except ImportError:
        print("ERROR: mlx-whisper not installed. Run: make setup", file=sys.stderr)
        sys.exit(1)

    print(f"Transcribing with {model} ...")
    result = transcribe(str(audio_path), path_or_hf_repo=model, verbose=False)
    return result["text"].strip()


# ---------------------------------------------------------------------------
# Claude (Bedrock) transcript formatting
# ---------------------------------------------------------------------------

def format_transcript(title: str, raw: str) -> str:
    """Format a raw Whisper transcript into readable Markdown via Claude (Bedrock).

    The transcript is kept 100% verbatim — every word is preserved exactly as
    spoken. Claude only adds paragraph breaks at natural topic shifts and
    inserts lightweight Markdown headings where a clear new section begins.
    No words are added, removed, corrected, or paraphrased.

    Falls back to the raw text if Bedrock is unavailable.
    """
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        return raw

    prompt = f"""You are formatting a raw speech-to-text transcript for human readability.

Video title: "{title}"

Rules — read carefully:
1. VERBATIM ONLY. Every single word in the output must appear in the input, in the
   same order, with identical spelling. Do not correct, paraphrase, add, or remove
   any words — not even filler words like "okay", "so", "now", "basically", "right".
2. Add paragraph breaks (blank lines) where the speaker shifts to a new thought or
   topic. A paragraph break is the ONLY structural change you may make to the text.
3. Where you identify a clear, distinct section boundary (a major topic shift, not
   just a new sentence), you may insert a Markdown heading (## or ###) on its own
   line BEFORE the paragraph. The heading text must be a short label you invent —
   it does NOT need to be verbatim from the transcript. This is the only text you
   may add that was not in the original.
4. Do not add any introduction, conclusion, or commentary.
5. Output only the formatted transcript — nothing else.

Raw transcript:
{raw}"""

    try:
        client = boto3.client(
            "bedrock-runtime",
            region_name="eu-west-1",
            config=Config(read_timeout=120, connect_timeout=30),
        )
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 8192,
            "messages": [{"role": "user", "content": prompt}],
        })
        response = client.invoke_model(modelId=BEDROCK_MODEL_ID, body=body)
        raw_response = json.loads(response["body"].read())
        return raw_response["content"][0]["text"].strip()
    except Exception as exc:
        print(f"WARNING: Transcript formatting failed ({exc}) — saving raw text.")
        return raw


# ---------------------------------------------------------------------------
# Claude (Bedrock) synthesis
# ---------------------------------------------------------------------------

def generate_synthesis(title: str, transcript: str, relevance_hint: str) -> dict:
    """Use Claude via Bedrock to generate summary, key claims, and relevance analysis.

    Returns a dict with keys: relevance, summary, key_claims, source_quality.
    Falls back to placeholder text if Bedrock is unavailable.
    """
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        print("WARNING: boto3 not installed — skipping AI synthesis. Run: make setup")
        return _synthesis_placeholder(relevance_hint)

    prompt = f"""You are a research assistant helping a PhD student assess a source for their literature radar.

Research context:
{RESEARCH_CONTEXT.strip()}

Source: "{title}"
User's relevance hint: "{relevance_hint}"

Full transcript:
<transcript>
{transcript[:12000]}{"[transcript truncated]" if len(transcript) > 12000 else ""}
</transcript>

Produce a structured assessment in JSON with these exact keys:
{{
  "relevance": "One sentence: why is this source potentially relevant to the RAG-for-ODL research? Be specific about which aspect (retrieval, generation, ODeL context, SDL, evaluation, etc.).",
  "source_quality": "One sentence: what type of source is this (peer-reviewed, industry practitioner, tutorial, grey literature, opinion)? What is the credibility basis?",
  "summary": "2–4 sentences summarising the main argument or content of this source.",
  "key_claims": ["bullet point 1", "bullet point 2", "bullet point 3"]
}}

Return only the JSON object, no other text."""

    try:
        client = boto3.client(
            "bedrock-runtime",
            region_name="eu-west-1",
            config=Config(read_timeout=120, connect_timeout=30),
        )
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        })
        response = client.invoke_model(modelId=BEDROCK_MODEL_ID, body=body)
        raw = json.loads(response["body"].read())
        text = raw["content"][0]["text"].strip()
        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        return json.loads(text)
    except Exception as exc:
        print(f"WARNING: Bedrock synthesis failed ({exc}) — using placeholders.")
        return _synthesis_placeholder(relevance_hint)


def _synthesis_placeholder(relevance_hint: str) -> dict:
    return {
        "relevance": relevance_hint or "Not yet assessed.",
        "source_quality": "Not yet assessed.",
        "summary": "Not yet written — watch/read the source and update this section.",
        "key_claims": ["Fill in after watching/reading."],
    }


# ---------------------------------------------------------------------------
# Radar note writer
# ---------------------------------------------------------------------------

def write_radar_entry(
    slug: str,
    url: str,
    metadata: dict,
    transcript: str,
    transcript_path: Path,
    synthesis: dict,
    radar_dir: Path,
) -> Path:
    """Write the structured radar note and return its path."""
    radar_dir.mkdir(parents=True, exist_ok=True)
    output_path = radar_dir / f"{slug}.md"

    today = date.today().isoformat()
    title = metadata["title"]
    author = metadata["uploader"]
    site_name = metadata["channel"]
    date_published = metadata["upload_date"]
    duration = metadata["duration_string"]
    platform = metadata["platform"]

    # Repo-root-relative path for the frontmatter field (machine-readable)
    try:
        transcript_rel = transcript_path.relative_to(REPO_ROOT)
    except ValueError:
        transcript_rel = transcript_path

    # Radar-dir-relative path for the markdown link (so it works as a clickable link
    # from within literature/radar/<slug>.md)
    try:
        transcript_link = transcript_path.relative_to(radar_dir)
    except ValueError:
        transcript_link = transcript_rel

    key_claims_md = "\n".join(f"- {c}" for c in synthesis["key_claims"])

    content = f"""---
title: "{title}"
type: video
url: "{url}"
cite_key: ""

author: "{author}"
organisation: ""
site_name: "{site_name}"
date_published: "{date_published}"
date_accessed: "{today}"
duration: "{duration}"
platform: "{platform}"

date_added: "{today}"
status: processed
tags: []
priority: medium

relevance: "{synthesis['relevance']}"
transcript_path: "{transcript_rel}"
---

# {title}

## Why on radar
{synthesis['relevance']}

## Source quality
{synthesis['source_quality']}

## Summary
{synthesis['summary']}

## Key claims
{key_claims_md}

## Connections to research
<!-- Add links to related notes, proposal sections, or research questions -->

## Transcript
See [{transcript_link}]({transcript_link}) for the full verbatim transcript.
"""

    output_path.write_text(content, encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download, transcribe, and create a radar note for a YouTube video"
    )
    parser.add_argument("url", help="YouTube URL")
    parser.add_argument(
        "--slug",
        default=None,
        help="Output filename stem (default: derived from video title)",
    )
    parser.add_argument(
        "--relevance",
        default="",
        help="Hint for the AI synthesis: why is this potentially relevant?",
    )
    parser.add_argument(
        "--transcript-dir",
        type=Path,
        default=DEFAULT_TRANSCRIPT_DIR,
        help=f"Directory to save the raw transcript (default: {DEFAULT_TRANSCRIPT_DIR})",
    )
    parser.add_argument(
        "--radar-dir",
        type=Path,
        default=RADAR_DIR,
        help=f"Directory to save the radar note (default: {RADAR_DIR})",
    )
    parser.add_argument(
        "--model",
        default="mlx-community/whisper-base.en-mlx",
        help="MLX Whisper model (use mlx-community/whisper-large-v3-mlx for higher accuracy)",
    )
    parser.add_argument(
        "--no-synthesis",
        action="store_true",
        help="Skip Claude synthesis — write placeholders instead",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Fetch metadata (no download)
    print("Fetching video metadata ...")
    metadata = fetch_video_metadata(args.url)
    print(f"  Title:    {metadata['title']}")
    print(f"  Channel:  {metadata['channel']}")
    print(f"  Date:     {metadata['upload_date']}")
    print(f"  Duration: {metadata['duration_string']}")

    slug = args.slug or f"youtube-{slugify(metadata['title'])}"

    radar_dir = args.radar_dir
    radar_path = radar_dir / f"{slug}.md"
    if radar_path.exists():
        print(f"\nRadar entry already exists: {radar_path}")
        print("Use --slug to specify a different name, or delete the existing file.")
        sys.exit(1)

    # Download audio → transcribe → delete audio
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_template = Path(tmpdir) / "audio"
        audio_path = download_audio(args.url, audio_template)
        transcript = transcribe_audio(audio_path, model=args.model)

    # Format transcript for readability (verbatim — only paragraph breaks + headings added)
    if args.no_synthesis:
        formatted = transcript
    else:
        print("Formatting transcript via Claude (Bedrock) ...")
        formatted = format_transcript(title=metadata["title"], raw=transcript)

    # Save formatted transcript
    args.transcript_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = args.transcript_dir / f"{slug}.md"
    header = f"# Transcript: {metadata['title']}\n\nSource: {args.url}\n\n---\n\n"
    transcript_path.write_text(header + formatted + "\n", encoding="utf-8")
    print(f"Transcript saved: {transcript_path} ({len(formatted)} chars)")

    # Generate synthesis via Claude
    if args.no_synthesis:
        synthesis = _synthesis_placeholder(args.relevance)
    else:
        print("Generating synthesis via Claude (Bedrock) ...")
        synthesis = generate_synthesis(
            title=metadata["title"],
            transcript=formatted,
            relevance_hint=args.relevance,
        )

    # Write radar note
    entry_path = write_radar_entry(
        slug=slug,
        url=args.url,
        metadata=metadata,
        transcript=transcript,
        transcript_path=transcript_path,
        synthesis=synthesis,
        radar_dir=radar_dir,
    )

    print(f"\nRadar entry written: {entry_path}")
    print(f"\nSummary: {synthesis['summary'][:200]}...")
    print(f"\nNext steps:")
    print(f"  1. Review {entry_path}")
    print(f"  2. Update 'priority', 'tags', and 'organisation' in frontmatter")
    print(f"  3. When ready to cite: add a bib entry and set cite_key")


if __name__ == "__main__":
    main()
