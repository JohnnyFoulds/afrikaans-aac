"""
Generate MP3 audio files for all phrases in phrases.json using Microsoft Edge TTS.

Voice: af-ZA-WillemNeural (Afrikaans, male, neural)

Audio files are written to the ``audio/`` directory relative to this script.
The script runs on the Mac (internet required for Edge TTS); generated MP3s are
then deployed to the tablet via SCP.

Usage::

    # Generate only phrases that are missing an audio file (default):
    python3 generate_audio.py

    # Regenerate every phrase, overwriting existing files:
    python3 generate_audio.py --all

    # Preview what would be generated without writing any files:
    python3 generate_audio.py --dry-run

Example::

    conda run -n brainstorm-dev python3 generate_audio.py
    conda run -n brainstorm-dev python3 generate_audio.py --all
"""

#region imports

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

import edge_tts

#endregion

#region constants

VOICE = "af-ZA-WillemNeural"
PHRASES_FILE = Path(__file__).parent / "phrases.json"
AUDIO_DIR = Path(__file__).parent / "audio"

# TTS normalisation map — applied to spoken text before synthesis.
# Keys are exact substrings to replace; values are what the TTS should say.
# This does NOT affect the display label or the phrase field in phrases.json.
# Add entries here whenever a word or abbreviation sounds wrong.
TTS_SUBSTITUTIONS: dict[str, str] = {
    "TV": "Televisie",
    "Francisca": "Fransiska",
    "Elaine": "ielain",
    "Carey-Anne": "Karrie-Ann",
}

#endregion

#region phrase collection


def collect_phrases(data: dict) -> list[dict]:
    """
    Flatten all phrase entries from phrases.json into a single list.

    Traverses ``always_visible``, all ``categories[].phrases``, and all
    ``categories[].secondary.phrases`` (pain character screen).

    :param data: Parsed content of phrases.json.
    :return: List of phrase dicts, each containing ``id``, ``label``,
             ``phrase``, and ``audio`` fields.

    Example::

        with open("phrases.json") as f:
            data = json.load(f)
        phrases = collect_phrases(data)
        # [{"id": "noodgeval", "label": "NOODGEVAL", ...}, ...]
    """
    phrases = []

    for entry in data.get("always_visible", []):
        phrases.append(entry)

    for category in data.get("categories", []):
        for entry in category.get("phrases", []):
            phrases.append(entry)
        secondary = category.get("secondary")
        if secondary:
            for entry in secondary.get("phrases", []):
                phrases.append(entry)

    return phrases


#endregion

#region deduplication


def deduplicate(phrases: list[dict]) -> list[dict]:
    """
    Remove phrases that share the same audio path.

    Some phrases reuse the same MP3 (e.g. "Praat stadiger" appears in both
    the communication-repair and the stroke-info categories). Deduplicating
    on audio path avoids regenerating the same file twice.

    :param phrases: Full phrase list, possibly containing duplicates.
    :return: List with one entry per unique audio path.

    Example::

        deduped = deduplicate(phrases)
    """
    seen: set[str] = set()
    result = []
    for p in phrases:
        audio_path = p["audio"]
        if audio_path not in seen:
            seen.add(audio_path)
            result.append(p)
    return result


#endregion

#region volume adjustment


def adjust_volume(path: Path, factor: float) -> None:
    """
    Re-encode an MP3 in-place with the given volume multiplier using ffmpeg.

    :param path: Absolute path to the MP3 file to adjust.
    :param factor: Volume multiplier (e.g. ``2.5`` = 2.5× louder).

    Example::

        adjust_volume(Path("audio/noodgeval.mp3"), 2.5)
    """
    tmp = path.with_suffix(".tmp.mp3")
    subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", f"volume={factor}", "-y", str(tmp)],
        check=True,
        capture_output=True,
    )
    tmp.replace(path)


#endregion

#region tts normalisation


def normalise_for_tts(text: str) -> str:
    """
    Apply TTS_SUBSTITUTIONS to a phrase before passing it to edge-tts.

    Substitutions are exact substring replacements applied in definition
    order. Only the spoken text is affected — display labels are unchanged.

    :param text: The phrase text as written in phrases.json.
    :return: Normalised text suitable for TTS synthesis.

    Example::

        normalise_for_tts("Skakel die TV aan, asseblief.")
        # "Skakel die Televisie aan, asseblief."

        normalise_for_tts("Roep vir Francisca, asseblief.")
        # "Roep vir Fransiska, asseblief."
    """
    for source, replacement in TTS_SUBSTITUTIONS.items():
        text = text.replace(source, replacement)
    return text


#endregion

#region audio generation


async def generate_one(phrase: dict, audio_dir: Path, overwrite: bool, dry_run: bool) -> str:
    """
    Generate the MP3 for a single phrase entry.

    :param phrase: Phrase dict with ``phrase`` (spoken text) and ``audio``
                   (relative path from app root, e.g. ``audio/ja.mp3``).
    :param audio_dir: Absolute path to the ``audio/`` output directory.
    :param overwrite: If ``True``, regenerate even if the file exists.
    :param dry_run: If ``True``, print what would be done without writing.
    :return: One of ``"generated"``, ``"skipped"``, or ``"dry-run"``.

    Example::

        status = await generate_one(phrase, audio_dir, overwrite=False, dry_run=False)
    """
    filename = Path(phrase["audio"]).name
    output_path = audio_dir / filename

    if dry_run:
        action = "WOULD GENERATE" if (overwrite or not output_path.exists()) else "would skip"
        print(f"  {action}: {filename}")
        return "dry-run"

    if output_path.exists() and not overwrite:
        return "skipped"

    spoken = normalise_for_tts(phrase["phrase"])
    communicate = edge_tts.Communicate(text=spoken, voice=VOICE)
    await communicate.save(str(output_path))

    if "volume" in phrase:
        adjust_volume(output_path, phrase["volume"])

    return "generated"


async def generate_all(phrases: list[dict], audio_dir: Path, overwrite: bool, dry_run: bool) -> None:
    """
    Generate MP3 files for all phrases, printing a progress summary.

    :param phrases: Deduplicated phrase list.
    :param audio_dir: Absolute path to the ``audio/`` output directory.
    :param overwrite: Passed through to :func:`generate_one`.
    :param dry_run: Passed through to :func:`generate_one`.

    Example::

        await generate_all(phrases, audio_dir, overwrite=False, dry_run=False)
    """
    n_generated = 0
    n_skipped = 0
    n_errors = 0

    for phrase in phrases:
        try:
            status = await generate_one(phrase, audio_dir, overwrite, dry_run)
        except Exception as exc:
            print(f"  ERROR {phrase['audio']}: {exc}", file=sys.stderr)
            n_errors += 1
            continue

        if status == "generated":
            print(f"  ✓ {phrase['audio']}")
            n_generated += 1
        elif status == "skipped":
            n_skipped += 1

    if not dry_run:
        print(f"\nDone: {n_generated} generated, {n_skipped} skipped, {n_errors} errors.")
    else:
        print(f"\nDry run complete: {len(phrases)} phrases checked.")


#endregion

#region entry point


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    :return: Parsed namespace with ``all`` and ``dry_run`` flags.

    Example::

        args = parse_args()
    """
    parser = argparse.ArgumentParser(
        description="Generate Afrikaans MP3 audio for all phrases in phrases.json.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Regenerate all audio files, overwriting existing ones.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be generated without writing any files.",
    )
    return parser.parse_args()


def main() -> None:
    """
    Main entry point.

    Loads phrases.json, collects and deduplicates all phrases, creates the
    audio/ directory if needed, then generates MP3 files via Edge TTS.

    Example::

        python3 generate_audio.py
        python3 generate_audio.py --all
        python3 generate_audio.py --dry-run
    """
    args = parse_args()

    if not PHRASES_FILE.exists():
        print(f"ERROR: {PHRASES_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    with PHRASES_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    phrases = collect_phrases(data)
    phrases = deduplicate(phrases)

    print(f"Voice: {VOICE}")
    print(f"Phrases: {len(phrases)} unique audio files")
    print(f"Output: {AUDIO_DIR}")
    if args.all:
        print("Mode: regenerate all")
    elif args.dry_run:
        print("Mode: dry run")
    else:
        print("Mode: new only (use --all to regenerate)")
    print()

    if not args.dry_run:
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    asyncio.run(generate_all(phrases, AUDIO_DIR, overwrite=args.all, dry_run=args.dry_run))


#endregion

if __name__ == "__main__":
    main()
