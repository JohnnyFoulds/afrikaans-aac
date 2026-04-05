"""Convert Markdown papers into MP3 audio using Edge TTS.

Usage::

    python topics/tts/src/edge_tts_markdown.py \
        --input-markdown topics/tts/outputs/paper.md \
        --output topics/tts/outputs/paper.mp3
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from edge_tts_pipeline import (
    DEFAULT_TABLE_LLM_MODEL,
    DEFAULT_TABLE_LOCAL_ENDPOINT,
    DEFAULT_TABLE_LOCAL_MODEL,
    DEFAULT_MAX_CHARS,
    DEFAULT_RATE,
    DEFAULT_VOICE,
    DEFAULT_VOLUME,
    resolve_id3_tags_from_bib,
    synthesize_markdown_file,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for Markdown-to-speech conversion.

    example::

        args = parse_args()
        print(args.input_markdown)

    :returns: Parsed CLI namespace.
    """
    parser = argparse.ArgumentParser(description="Convert Markdown files to MP3 with Edge TTS")
    parser.add_argument(
        "--input-markdown",
        required=True,
        type=Path,
        help="Input Markdown file",
    )
    parser.add_argument("--output", required=True, type=Path, help="Output MP3 path")
    parser.add_argument(
        "--markdown-profile",
        choices=["general", "paper", "paper-lean", "keshav-pass1", "keshav-pass2", "keshav-pass3"],
        default="paper-lean",
        help="Markdown preprocessing profile",
    )
    parser.add_argument(
        "--math-mode",
        choices=["strip", "placeholder", "keep", "verbalize"],
        default="strip",
        help="How to handle LaTeX/equation content",
    )
    parser.add_argument(
        "--table-mode",
        choices=["drop", "label-only", "script", "llm-summary", "local-llm-summary"],
        default="script",
        help="How to process markdown tables",
    )
    parser.add_argument(
        "--table-text-ratio-threshold",
        default=0.45,
        type=float,
        help="Script mode threshold for keeping text-heavy table rows",
    )
    parser.add_argument(
        "--table-llm-model",
        default=DEFAULT_TABLE_LLM_MODEL,
        help="LLM model name for table summaries when table-mode=llm-summary",
    )
    parser.add_argument(
        "--table-local-model",
        default=DEFAULT_TABLE_LOCAL_MODEL,
        help="Local model name for table summaries when table-mode=local-llm-summary",
    )
    parser.add_argument(
        "--table-local-endpoint",
        default=DEFAULT_TABLE_LOCAL_ENDPOINT,
        help="Local endpoint for table summaries when table-mode=local-llm-summary",
    )
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="Edge voice name")
    parser.add_argument("--rate", default=DEFAULT_RATE, help="Speaking rate, e.g. +10%")
    parser.add_argument("--volume", default=DEFAULT_VOLUME, help="Volume, e.g. +0%")
    parser.add_argument(
        "--max-chars",
        default=DEFAULT_MAX_CHARS,
        type=int,
        help="Max characters per synthesis chunk",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Print OpenTelemetry spans to stdout",
    )
    parser.add_argument(
        "--bib",
        type=Path,
        default=None,
        help="Path to a BibTeX .bib file for ID3 tag lookup",
    )
    parser.add_argument(
        "--cite-key",
        default=None,
        help="BibTeX cite key to look up (defaults to input markdown stem)",
    )
    return parser.parse_args()


def main() -> None:
    """Run Markdown-to-audio conversion.

    example::

        # python topics/tts/src/edge_tts_markdown.py --input-markdown paper.md --output paper.mp3

    :returns: ``None``.
    """
    args = parse_args()

    id3_tags = None
    if args.bib is not None:
        cite_key = args.cite_key or args.input_markdown.stem
        id3_tags = resolve_id3_tags_from_bib(args.bib, cite_key)
        if id3_tags is None:
            print(f"Warning: cite key '{cite_key}' not found in {args.bib}", flush=True)

    output_file = synthesize_markdown_file(
        markdown_path=args.input_markdown,
        output_path=args.output,
        markdown_profile=args.markdown_profile,
        math_mode=args.math_mode,
        table_mode=args.table_mode,
        table_text_ratio_threshold=args.table_text_ratio_threshold,
        table_llm_model=args.table_llm_model,
        table_local_model=args.table_local_model,
        table_local_endpoint=args.table_local_endpoint,
        voice=args.voice,
        rate=args.rate,
        volume=args.volume,
        max_chars=args.max_chars,
        console_trace=args.trace,
        id3_tags=id3_tags,
    )
    print(f"Generated: {output_file}")


if __name__ == "__main__":
    main()
