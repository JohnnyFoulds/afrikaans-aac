"""CLI wrapper for md-to-audio skill.

Handles preset expansion and delegates to edge_tts_markdown.py.

Usage::

    python md_to_audio.py <input.md> <output.mp3> [options]
    python md_to_audio.py paper.md paper.mp3 --preset research
    python md_to_audio.py notes.md notes.mp3 --preset paper --math strip
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "edge_tts_markdown.py"

PRESETS: dict[str, dict[str, str]] = {
    "research": {
        "profile": "paper-lean",
        "math": "verbalize",
        "tables": "llm-summary",
        "table_model": "openai:gpt-4.1",
    },
    "paper": {
        "profile": "paper-lean",
        "math": "placeholder",
        "tables": "script",
    },
    # Keshav three-pass presets
    "keshav-pass1": {
        "profile": "keshav-pass1",
        "math": "strip",
        "tables": "script",
        "rate": "+30%",
    },
    "keshav-pass2": {
        "profile": "keshav-pass2",
        "math": "placeholder",
        "tables": "label-only",
        "rate": "+30%",
    },
    "keshav-pass3": {
        "profile": "keshav-pass3",
        "math": "verbalize",
        "tables": "llm-summary",
        "table_model": "openai:gpt-4.1",
    },
}


def main() -> None:
    """Parse arguments, expand preset, and run edge_tts_markdown.py."""
    parser = argparse.ArgumentParser(description="Convert Markdown to MP3 audio")
    parser.add_argument("input", type=Path, help="Input Markdown file")
    parser.add_argument("output", type=Path, help="Output MP3 file")
    parser.add_argument("--preset", choices=list(PRESETS), help="Named preset")
    parser.add_argument(
        "--profile",
        choices=["general", "paper", "paper-lean", "keshav-pass1", "keshav-pass2", "keshav-pass3"],
    )
    parser.add_argument("--math", choices=["strip", "placeholder", "keep", "verbalize"])
    parser.add_argument("--tables", choices=["drop", "label-only", "script", "llm-summary", "local-llm-summary"])
    parser.add_argument("--table-model", default=None)
    parser.add_argument("--local-model", default=None)
    parser.add_argument("--local-endpoint", default=None)
    parser.add_argument("--voice", default=None)
    parser.add_argument("--rate", default=None)
    parser.add_argument("--bib", type=Path, default=None, help="BibTeX .bib file for ID3 tags")
    parser.add_argument("--cite-key", default=None, help="Cite key (defaults to input stem)")
    args = parser.parse_args()

    # Base defaults
    resolved = {
        "profile": "general",
        "math": "strip",
        "tables": "script",
        "table_model": "openai:gpt-4.1",
        "local_model": "qwen2.5:3b",
        "local_endpoint": "http://localhost:11434/api/generate",
        "voice": "en-US-AriaNeural",
        "rate": "+0%",
    }

    # Preset expansion
    if args.preset:
        resolved.update(PRESETS[args.preset])

    # Explicit overrides
    if args.profile:
        resolved["profile"] = args.profile
    if args.math:
        resolved["math"] = args.math
    if args.tables:
        resolved["tables"] = args.tables
    if args.table_model:
        resolved["table_model"] = args.table_model
    if args.local_model:
        resolved["local_model"] = args.local_model
    if args.local_endpoint:
        resolved["local_endpoint"] = args.local_endpoint
    if args.voice:
        resolved["voice"] = args.voice
    if args.rate:
        resolved["rate"] = args.rate

    cmd = [
        sys.executable,
        str(SCRIPT),
        "--input-markdown", str(args.input),
        "--output", str(args.output),
        "--markdown-profile", resolved["profile"],
        "--math-mode", resolved["math"],
        "--table-mode", resolved["tables"],
    ]

    if resolved["tables"] == "llm-summary":
        cmd += ["--table-llm-model", resolved["table_model"]]
    elif resolved["tables"] == "local-llm-summary":
        cmd += ["--table-local-model", resolved["local_model"]]
        cmd += ["--table-local-endpoint", resolved["local_endpoint"]]

    if resolved["voice"] != "en-US-AriaNeural":
        cmd += ["--voice", resolved["voice"]]
    if resolved["rate"] != "+0%":
        cmd += ["--rate", resolved["rate"]]

    if args.bib is not None:
        cmd += ["--bib", str(args.bib)]
        cite_key = args.cite_key or args.input.stem
        cmd += ["--cite-key", cite_key]

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
