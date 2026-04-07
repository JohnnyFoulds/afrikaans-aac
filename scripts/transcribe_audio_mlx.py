"""Transcribe audio files to plain text using local MLX Whisper.

Usage::

    python scripts/transcribe_audio_mlx.py --input-audio /tmp/video.mp3

Adapted from brainstorm-tts/topics/tts/src/transcribe_audio_mlx.py (OpenTelemetry removed).
"""

from __future__ import annotations

import argparse
from pathlib import Path


def resolve_output_path(input_audio: Path, output_path: Path | None) -> Path:
    """Resolve transcript output path and ensure parent directories exist."""
    if output_path is None:
        destination = input_audio.with_suffix(".txt")
    elif output_path.suffix:
        destination = output_path
    else:
        destination = output_path.with_suffix(".txt")

    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def transcribe_audio(
    input_audio: Path,
    output_path: Path | None = None,
    model: str = "mlx-community/whisper-base.en-mlx",
    language: str | None = None,
    task: str = "transcribe",
) -> Path:
    """Transcribe an audio file and write plain text output.

    :param input_audio: Source audio file path.
    :param output_path: Optional output path for transcript text.
    :param model: MLX Whisper model identifier or local model path.
        Recommended: ``mlx-community/whisper-base.en-mlx`` for English.
        Note: use the ``-mlx`` suffix; plain ``whisper-base`` returns 401.
    :param language: Optional language code. ``None`` enables auto-detection.
    :param task: Whisper task, either ``transcribe`` or ``translate``.
    :returns: Path to written transcript text file.
    :raises FileNotFoundError: If input audio file does not exist.
    :raises RuntimeError: If ``mlx_whisper`` dependency is unavailable.
    """
    if not input_audio.exists():
        raise FileNotFoundError(f"Audio file not found: {input_audio}")

    try:
        from mlx_whisper import transcribe
    except ImportError as exc:
        raise RuntimeError(
            "mlx-whisper is not installed. Run: make setup  (or conda env create -f environment.yml)"
        ) from exc

    destination = resolve_output_path(input_audio=input_audio, output_path=output_path)

    print(f"Transcribing {input_audio} with model {model} ...")
    result = transcribe(
        str(input_audio),
        path_or_hf_repo=model,
        verbose=False,
        language=language,
        task=task,
    )

    text = result["text"].strip()
    destination.write_text(f"{text}\n", encoding="utf-8")
    print(f"Transcript written: {destination} ({len(text)} chars)")
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe audio to text with MLX Whisper")
    parser.add_argument("--input-audio", required=True, type=Path, help="Input audio file path")
    parser.add_argument("--output", type=Path, default=None, help="Output text file path")
    parser.add_argument(
        "--model",
        default="mlx-community/whisper-base.en-mlx",
        help="MLX Whisper model id (default: mlx-community/whisper-base.en-mlx)",
    )
    parser.add_argument("--language", default=None, help="Language code, e.g. en")
    parser.add_argument(
        "--task",
        default="transcribe",
        choices=["transcribe", "translate"],
        help="Whisper task mode",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    transcribe_audio(
        input_audio=args.input_audio,
        output_path=args.output,
        model=args.model,
        language=args.language,
        task=args.task,
    )


if __name__ == "__main__":
    main()
