"""
Smoke test for the writing pipeline.

Verifies that a completed pipeline run produced correct output.
Run AFTER writing-pipeline.py has completed.

Usage:
    python scripts/test_pipeline_smoke.py \\
        --output-dir pipeline-outputs/ \\
        --section 1.2 \\
        --rounds 2 \\
        --input proposal/01-introduction.md

Exit code 0 if all criteria pass, 1 if any fail.
"""
import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test for writing-pipeline.py output.")
    parser.add_argument("--output-dir", default="pipeline-outputs", help="Output directory to check.")
    parser.add_argument("--section", required=True, help="Section ID that was processed (e.g. 1.2).")
    parser.add_argument("--rounds", type=int, default=2, help="Number of rounds that were run.")
    parser.add_argument(
        "--input", default=None,
        help="Original input file (used to extract text for diff comparison).",
    )
    return parser.parse_args()


def slug(section: str) -> str:
    return re.sub(r"[^\w.-]", "-", section)


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    line = f"  [{status}] {label}"
    if detail and not condition:
        line += f"\n         {detail}"
    print(line)
    return condition


def extract_section(text: str, section_id: str) -> str:
    """Minimal section extractor matching the pipeline's logic."""
    match = None
    hashes = None
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
        return ""
    start = match.start()
    level = len(hashes)
    after = text[start + level:]
    end_match = re.search(
        rf"^#{'{1,' + str(level) + '}'}(?!#)",
        after,
        re.MULTILINE,
    )
    end = start + level + end_match.start() if end_match else len(text)
    return text[start:end].strip()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    s = slug(args.section)
    rounds = args.rounds

    print(f"\nSmoke test: section='{args.section}', rounds={rounds}, dir={output_dir}\n")

    results = []

    # ------------------------------------------------------------------
    # Criterion 1: All expected output files exist
    # ------------------------------------------------------------------
    expected_files = []
    for r in range(1, rounds + 1):
        expected_files.append(f"{s}-critique-r{r}.md")
        expected_files.append(f"{s}-revised-r{r}.md")
    expected_files.append(f"{s}-polished.md")

    all_exist = True
    for fname in expected_files:
        fpath = output_dir / fname
        exists = fpath.exists()
        if not exists:
            all_exist = False
        results.append(check(f"file exists: {fname}", exists))

    if not all_exist:
        print("\nCannot run further checks — some files missing.\n")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Criterion 2: polished.md word count >= 200
    # ------------------------------------------------------------------
    polished_text = (output_dir / f"{s}-polished.md").read_text(encoding="utf-8")
    word_count = len(polished_text.split())
    results.append(check(
        f"polished.md word count >= 200 (actual: {word_count})",
        word_count >= 200,
        f"Only {word_count} words — Opus polish may have failed or truncated output.",
    ))

    # ------------------------------------------------------------------
    # Criterion 3: critique-r1.md contains a numbered item (^\d+\.)
    # ------------------------------------------------------------------
    critique_r1 = (output_dir / f"{s}-critique-r1.md").read_text(encoding="utf-8")
    has_numbered = bool(re.search(r"^\d+\.", critique_r1, re.MULTILINE))
    # Skip this check if round was skipped (early exit placeholder)
    is_skipped = "skipped" in critique_r1.lower()
    results.append(check(
        "critique-r1.md contains numbered critique items",
        has_numbered or is_skipped,
        "No lines matching '^\\d+.' found — GPT-4o may not have followed the output format.",
    ))

    # ------------------------------------------------------------------
    # Criterion 4: revised-r1.md differs from original input text
    # ------------------------------------------------------------------
    revised_r1 = (output_dir / f"{s}-revised-r1.md").read_text(encoding="utf-8")
    original_text = ""
    if args.input:
        repo_root = Path(__file__).parent.parent
        input_path = repo_root / args.input
        if input_path.exists():
            full = input_path.read_text(encoding="utf-8")
            original_text = extract_section(full, args.section) if args.section else full

    if original_text:
        differs_from_original = revised_r1.strip() != original_text.strip()
        results.append(check(
            "revised-r1.md differs from original input",
            differs_from_original,
            "Revision is identical to input — Bedrock reviser may have failed.",
        ))
    else:
        print("  [SKIP] revised-r1.md differs from original (no input file provided)")

    # ------------------------------------------------------------------
    # Criterion 5: polished.md differs from final revised draft
    # ------------------------------------------------------------------
    final_revised = (output_dir / f"{s}-revised-r{rounds}.md").read_text(encoding="utf-8")
    polished_differs = polished_text.strip() != final_revised.strip()
    results.append(check(
        "polished.md differs from final revised draft",
        polished_differs,
        "Polished output is identical to revised input — Opus polish may have been a no-op.",
    ))

    # ------------------------------------------------------------------
    # Criterion 6: No file starts with Error or Traceback
    # ------------------------------------------------------------------
    no_errors = True
    for fname in expected_files:
        content = (output_dir / fname).read_text(encoding="utf-8")
        first_line = content.splitlines()[0] if content.strip() else ""
        if re.match(r"^(Error|Traceback|OPENAI_ERROR|API_ERROR)", first_line, re.IGNORECASE):
            no_errors = False
            results.append(check(f"no API error in {fname}", False, f"First line: {first_line!r}"))
    if no_errors:
        results.append(check("no API errors in any output file", True))

    # ------------------------------------------------------------------
    # Criterion 7: revised-r1.md contains "Revision log"
    # ------------------------------------------------------------------
    has_revision_log = "Revision log" in revised_r1 or "revision log" in revised_r1.lower()
    is_r1_skipped = "skipped" in revised_r1.lower()
    results.append(check(
        "revised-r1.md contains 'Revision log'",
        has_revision_log or is_r1_skipped,
        "Reviser did not append a Revision log — it may have ignored the instruction.",
    ))

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\n{'=' * 40}")
    print(f"Result: {passed}/{total} criteria passed")
    print(f"{'=' * 40}\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
