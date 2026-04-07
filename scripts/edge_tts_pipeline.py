"""Convert paper text into MP3 audio using Edge TTS.

Usage::

    python topics/tts/src/edge_tts_pipeline.py \
        --input topics/tts/outputs/sample.txt \
        --output topics/tts/outputs/sample.mp3
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import socket
import time
from typing import Literal
from urllib import error, request

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

DEFAULT_VOICE = "en-US-AriaNeural"
DEFAULT_RATE = "+0%"
DEFAULT_VOLUME = "+0%"
DEFAULT_MAX_CHARS = 2000
DEFAULT_MATH_PLACEHOLDER = "equation omitted"
DEFAULT_TABLE_LLM_MODEL = "openai:gpt-4.1"
DEFAULT_TABLE_LOCAL_MODEL = "qwen2.5:3b"
DEFAULT_TABLE_LOCAL_ENDPOINT = "http://localhost:11434/api/generate"
PAPER_STOP_HEADINGS = {
    "references",
    "reference",
    "acknowledgements",
    "acknowledgments",
}
PAPER_LEAN_SKIP_HEADINGS = {
    "author information",
    "authors",
    "author contributions",
    "affiliations",
    "funding",
    "declarations",
    "conflicts of interest",
    "competing interests",
    "ethics statement",
    "data availability",
    "code availability",
    "supplementary material",
    "supplementary materials",
    "appendix",
}
DEFAULT_SRE_STYLE = "Fraction_Auto:Exponent_Ordinal:Roots_Auto:Functions_Auto"

# Tier-2 whitelist for keshav-pass1: known good terminal-section synonyms that
# are NOT caught by _KESHAV_CONCLUSIONS_RE but are still meaningful synthesis
# sections.  Checked against the normalised heading text (section numbers stripped,
# lowercased).  If a whitelist heading is found, it is preferred over the
# last-section fallback.
_KESHAV_WHITELIST_RE = re.compile(
    r"^(discussion|limitations?\s+and\s+future\s+work|limitations?|"
    r"future\s+work|future\s+directions?|design\s+implications?|"
    r"implications?\s+and\s+future\s+directions?)$",
    re.IGNORECASE,
)

# Regex to detect the conclusions section for keshav-pass1.
# Matches H1–H3 headings whose normalised text begins with a conclusion/summary
# keyword (after stripping optional leading section numbers).
# Examples matched: "Conclusion", "7 Conclusions and Future Work",
# "Discussion and Conclusion", "Summary", "Concluding Remarks", "Final Remarks".
_KESHAV_CONCLUSIONS_RE = re.compile(
    r"^(?:\d+\.?\s+)?"
    r"(conclusion|conclusions|concluding|summary|final\s+remarks|"
    r"closing\s+remarks|discussion\s+and\s+conclusion)",
    re.IGNORECASE,
)

# Regex to detect the introduction section for keshav-pass1 state machine.
_KESHAV_INTRO_RE = re.compile(
    r"^(?:\d+\.?\s+)?introduction\b",
    re.IGNORECASE,
)

# Sentinel used to carry heading level through the text pipeline.
# Format: \x00H<level>\x00<heading text>  — NUL never appears in prose.
HEADING_SENTINEL_RE = re.compile(r"^\x00H([1-6])\x00(.+)$")


#region SREBridge


class SREBridge:
    """Persistent Node.js Speech Rule Engine subprocess.

    Start once per document to amortise the 300–500 ms Node.js startup
    cost across all math expressions in the document.  Each call to
    :meth:`to_speech` sends one MathML string on stdin and reads one
    speech string from stdout.

    The Node.js script requires ``speech-rule-engine`` installed in the
    ``node_modules`` reachable from the working directory or globally::

        npm install -g speech-rule-engine

    example::

        bridge = SREBridge()
        speech = bridge.to_speech("<math><mfrac><mn>1</mn><mn>2</mn></mfrac></math>")
        bridge.close()

    :param domain: SRE domain; ``"clearspeak"`` is recommended for TTS.
    :param style: Colon-separated Clearspeak preference string.
    :raises FileNotFoundError: When ``node`` is not found on ``PATH``.
    """

    _NODE_SCRIPT = r"""
const sre = require('speech-rule-engine');
const readline = require('readline');
const domain = process.env.SRE_DOMAIN || 'clearspeak';
const style  = process.env.SRE_STYLE  || 'default';
(async () => {
    await sre.setupEngine({ domain, style, locale: 'en' });
    await sre.engineReady();
    process.stdout.write('__SRE_READY__\n');
    const rl = readline.createInterface({ input: process.stdin });
    rl.on('line', (line) => {
        try {
            process.stdout.write(sre.toSpeech(line.trim()) + '\n');
        } catch(e) {
            process.stdout.write('__SRE_ERROR__\n');
        }
    });
})();
"""

    def __init__(
        self,
        domain: str = "clearspeak",
        style: str = DEFAULT_SRE_STYLE,
    ) -> None:
        """Start the persistent Node.js SRE subprocess.

        :param domain: SRE speech domain.
        :param style: Clearspeak preference string.
        :raises FileNotFoundError: When ``node`` executable is not found.
        """
        import subprocess
        import os

        env = os.environ.copy()
        env["SRE_DOMAIN"] = domain
        env["SRE_STYLE"] = style

        # Ensure the global npm node_modules directory is on NODE_PATH so that
        # `require('speech-rule-engine')` resolves when installed globally.
        try:
            npm_root = subprocess.check_output(
                ["npm", "root", "-g"], stderr=subprocess.DEVNULL
            ).decode().strip()
            existing = env.get("NODE_PATH", "")
            env["NODE_PATH"] = f"{npm_root}:{existing}" if existing else npm_root
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass  # npm not available — rely on whatever NODE_PATH is already set

        self._proc = subprocess.Popen(
            ["node", "-e", self._NODE_SCRIPT],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        # Block until the engine signals it is ready to accept expressions.
        ready = self._proc.stdout.readline().decode().strip()
        if ready != "__SRE_READY__":
            self._proc.terminate()
            raise RuntimeError(
                f"SRE subprocess failed to start (got {ready!r} instead of __SRE_READY__)"
            )

    def to_speech(self, mathml: str) -> str | None:
        """Send one MathML string to SRE and return the spoken form.

        :param mathml: W3C Presentation MathML string (single expression).
        :returns: Natural English speech string, or ``None`` on SRE error.
        """
        line = mathml.replace("\n", " ").strip() + "\n"
        self._proc.stdin.write(line.encode())
        self._proc.stdin.flush()
        result = self._proc.stdout.readline().decode().strip()
        return None if (not result or result == "__SRE_ERROR__") else result

    def close(self) -> None:
        """Terminate the underlying Node.js process.

        :returns: ``None``.
        """
        self._proc.terminate()


def _latex_to_speech(latex: str, sre_bridge: SREBridge) -> str:
    """Convert a LaTeX math expression to natural spoken English.

    Uses the ``latex2mathml`` → :class:`SREBridge` pipeline.  Falls back
    silently to :data:`DEFAULT_MATH_PLACEHOLDER` on any failure.

    example::

        bridge = SREBridge()
        spoken = _latex_to_speech(r"\\frac{1}{2}", bridge)
        # "one half"
        bridge.close()

    :param latex: Raw LaTeX expression string (without surrounding ``$``).
    :param sre_bridge: Active :class:`SREBridge` instance.
    :returns: Spoken English string, or :data:`DEFAULT_MATH_PLACEHOLDER`
        on conversion failure.
    """
    try:
        import latex2mathml.converter
        mathml = latex2mathml.converter.convert(latex, display="block")
        result = sre_bridge.to_speech(mathml)
        if result:
            return result
    except Exception:
        pass
    return DEFAULT_MATH_PLACEHOLDER


#endregion


#region Tracing

def _setup_tracing(console_trace: bool = False) -> trace.Tracer:
    """Configure OpenTelemetry tracing for this script.

    example::

        tracer = _setup_tracing(console_trace=True)
        with tracer.start_as_current_span("example"):
            pass

    :param console_trace: Whether to emit spans to stdout.
    :returns: A configured tracer for this module.
    """
    resource = Resource.create({"service.name": "paper-tts-edge"})
    provider = TracerProvider(resource=resource)

    if console_trace or os.environ.get("OTEL_TRACE_CONSOLE") == "1":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
        )

    trace.set_tracer_provider(provider)
    return trace.get_tracer("edge_tts_pipeline")

#endregion


#region Chunking and paths

def _is_markdown_table_line(line: str) -> bool:
    """Check whether a line looks like a Markdown pipe-table row.

    :param line: Raw line from markdown text.
    :returns: ``True`` when line appears to be a pipe-table row.
    """
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def _is_markdown_table_separator(line: str) -> bool:
    """Check whether a line is a Markdown table separator row.

    :param line: Raw line from markdown text.
    :returns: ``True`` when line is a separator row like ``| --- | --- |``.
    """
    return re.fullmatch(r"\|?[\s:-]+\|[\s|:-]*", line.strip() or " ") is not None


def _split_markdown_table_cells(line: str) -> list[str]:
    """Split a pipe-table line into trimmed cell values.

    :param line: Markdown table row.
    :returns: Ordered list of cell values.
    """
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _looks_like_table_label(line: str) -> bool:
    """Check whether a line looks like a table label/caption line.

    :param line: Raw line from markdown text.
    :returns: ``True`` when line starts with a table label like ``Table 7:``.
    """
    stripped = line.strip()
    if not stripped:
        return False
    return re.match(
        r"^(table|tab\.?)[\s]*([A-Za-z0-9]+|[IVXLCMivxlcm]+)([:.)\-]|\s|$)",
        stripped,
        flags=re.IGNORECASE,
    ) is not None


def _is_figure_description_start(line: str) -> bool:
    """Check whether a line starts a figure description details block.

    :param line: Raw line from markdown text.
    :returns: ``True`` when line starts a figure-description ``<details>`` block.
    """
    stripped = line.strip().lower()
    return (
        stripped.startswith("<details")
        and "<summary>" in stripped
        and "figure description" in stripped
    )


def _looks_like_figure_label(line: str) -> bool:
    """Check whether a line looks like a figure label/caption line.

    :param line: Raw line from markdown text.
    :returns: ``True`` when line starts with a figure label like ``Fig. 1:``.
    """
    stripped = line.strip()
    if not stripped:
        return False
    return re.match(
        r"^(fig\.?|figure)[\s]+([A-Za-z0-9]+|[IVXLCMivxlcm]+)([:.)\-]|\s)",
        stripped,
        flags=re.IGNORECASE,
    ) is not None


def _extract_figure_label(
    lines: list[str],
    details_start: int,
    details_end: int,
) -> tuple[str, int | None]:
    """Extract nearby figure label around a figure description block.

    :param lines: All markdown lines.
    :param details_start: Start index of ``<details>`` line.
    :param details_end: End index of details block (exclusive).
    :returns: Tuple of ``(label, line_index)`` when found, else ``("", None)``.
    """
    for offset in range(1, 4):
        previous_index = details_start - offset
        if previous_index < 0:
            break
        candidate = lines[previous_index].strip()
        if not candidate:
            continue
        if _looks_like_figure_label(candidate):
            return candidate, previous_index
        break

    for offset in range(0, 3):
        next_index = details_end + offset
        if next_index >= len(lines):
            break
        candidate = lines[next_index].strip()
        if not candidate:
            continue
        if _looks_like_figure_label(candidate):
            return candidate, next_index
        break

    return "", None


def _combine_figure_label_and_description(figure_label: str, description: str) -> str:
    """Combine figure label and description into one spoken block.

    :param figure_label: Detected figure label/caption text.
    :param description: Figure description content.
    :returns: Combined figure label + description text.
    """
    cleaned_description = description.strip()
    if not cleaned_description:
        return ""
    if not figure_label:
        return cleaned_description

    normalized_label = figure_label.strip()
    if normalized_label.endswith(":"):
        normalized_label = normalized_label[:-1].rstrip()
    if normalized_label and normalized_label[-1] not in ".!?":
        normalized_label = f"{normalized_label}."

    if cleaned_description.lower().startswith(normalized_label.lower()):
        return cleaned_description

    return f"{normalized_label} {cleaned_description}".strip()


def _transform_markdown_figures(
    markdown_text: str,
    figure_mode: Literal["speak", "label-only", "drop"] = "speak",
) -> str:
    """Transform figure-description details blocks into TTS-friendly lines.

    :param markdown_text: Raw markdown content.
    :param figure_mode: ``"speak"`` converts figure labels and descriptions into
        spoken text; ``"label-only"`` keeps the label but drops the
        ``<details>`` description block; ``"drop"`` silently removes both.
    :returns: Markdown text with figure descriptions normalized or removed.
    """
    lines = markdown_text.splitlines()
    transformed: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if not _is_figure_description_start(line):
            transformed.append(line)
            index += 1
            continue

        details_start = index
        index += 1
        description_lines: list[str] = []
        while index < len(lines) and "</details>" not in lines[index].lower():
            candidate = lines[index].strip()
            if candidate:
                description_lines.append(candidate)
            index += 1

        if index < len(lines) and "</details>" in lines[index].lower():
            index += 1
        details_end = index

        figure_label, figure_label_index = _extract_figure_label(
            lines,
            details_start=details_start,
            details_end=details_end,
        )

        if figure_mode == "label-only":
            # Keep the label that was already appended (or advance past a post-details one),
            # but skip the <details> description block entirely.
            if (
                figure_label_index is not None
                and figure_label_index >= details_end
                and index <= figure_label_index
            ):
                transformed.append(lines[figure_label_index])
                index = figure_label_index + 1
            continue

        if figure_mode == "drop":
            # Remove the figure label line if it was already appended.
            if figure_label and transformed and transformed[-1].strip() == figure_label:
                transformed.pop()
            # Skip the post-details label line too.
            if (
                figure_label_index is not None
                and figure_label_index >= details_end
                and index <= figure_label_index
            ):
                index = figure_label_index + 1
            continue

        description = " ".join(description_lines).strip()
        combined = _combine_figure_label_and_description(figure_label, description)
        if combined:
            if transformed and transformed[-1].strip() == figure_label:
                transformed.pop()
            transformed.append(combined)

        if (
            figure_label_index is not None
            and figure_label_index >= details_end
            and index <= figure_label_index
        ):
            index = figure_label_index + 1

    return "\n".join(transformed)


def _extract_table_label(lines: list[str], table_start: int, table_end: int) -> tuple[str, int | None]:
    """Extract nearby table label text around a markdown table block.

    :param lines: All markdown lines.
    :param table_start: Start index of table block.
    :param table_end: End index of table block (exclusive).
    :returns: Tuple of ``(label, line_index)`` when found, else ``("", None)``.
    """
    for offset in range(1, 4):
        previous_index = table_start - offset
        if previous_index < 0:
            break
        candidate = lines[previous_index].strip()
        if not candidate:
            continue
        if _looks_like_table_label(candidate):
            return candidate, previous_index
        break

    for offset in range(0, 3):
        next_index = table_end + offset
        if next_index >= len(lines):
            break
        candidate = lines[next_index].strip()
        if not candidate:
            continue
        if _looks_like_table_label(candidate):
            return candidate, next_index
        break

    return "", None


def _combine_table_label_and_summary(table_label: str, summary: str) -> str:
    """Combine table label and summary into one TTS-friendly spoken block.

    :param table_label: Detected table label/caption text.
    :param summary: Summarized table description.
    :returns: Combined label+summary text.
    """
    def _dedupe_label_mentions(text: str, label: str) -> str:
        """Remove repeated occurrences of the same table label after first mention.

        :param text: Combined text block.
        :param label: Table label/caption text.
        :returns: Text with duplicate same-label mentions removed.
        """
        cleaned_label = label.strip()
        if not cleaned_label:
            return text

        normalized = cleaned_label.rstrip(" .:")
        variants = [
            cleaned_label,
            normalized,
            f"{normalized}.",
            f"{normalized}:",
        ]
        deduped = text
        for variant in [value for value in variants if value]:
            seen = False

            def _replace_match(match: re.Match[str]) -> str:
                nonlocal seen
                if not seen:
                    seen = True
                    return match.group(0)
                return ""

            deduped = re.sub(
                re.escape(variant),
                _replace_match,
                deduped,
                flags=re.IGNORECASE,
            )

        table_ref_match = re.match(
            r"^(table|tab\.?)\s+([A-Za-z0-9]+|[IVXLCMivxlcm]+)",
            cleaned_label,
            flags=re.IGNORECASE,
        )
        if table_ref_match:
            table_ref = f"{table_ref_match.group(1)} {table_ref_match.group(2)}"
            ref_pattern = re.compile(
                rf"\b{re.escape(table_ref)}\b[^.!?]*[.!?]?",
                flags=re.IGNORECASE,
            )
            ref_seen = False

            def _replace_ref(match: re.Match[str]) -> str:
                nonlocal ref_seen
                if not ref_seen:
                    ref_seen = True
                    return match.group(0)
                return ""

            deduped = ref_pattern.sub(_replace_ref, deduped)

        deduped = re.sub(r"\s{2,}", " ", deduped)
        deduped = re.sub(r"\s+([,.;:!?])", r"\1", deduped)
        return deduped.strip()

    cleaned_summary = summary.strip()
    if not cleaned_summary:
        return ""
    if not table_label:
        return cleaned_summary

    if cleaned_summary.lower().startswith(table_label.lower()):
        return _dedupe_label_mentions(cleaned_summary, table_label)

    normalized_label = table_label.strip()
    if normalized_label.endswith(":"):
        normalized_label = normalized_label[:-1].rstrip()

    if normalized_label and normalized_label[-1] not in ".!?":
        normalized_label = f"{normalized_label}."

    combined = f"{normalized_label} {cleaned_summary}".strip()
    return _dedupe_label_mentions(combined, table_label)


def _row_text_ratio(cells: list[str]) -> float:
    """Compute alphabetic character ratio for a table row.

    :param cells: Row cell values.
    :returns: Alphabetic ratio in the row payload.
    """
    payload = " ".join(cells)
    compact = "".join(ch for ch in payload if not ch.isspace())
    if not compact:
        return 0.0
    alpha = sum(1 for ch in compact if ch.isalpha())
    return alpha / len(compact)


def _summarize_table_script(
    table_lines: list[str],
    text_ratio_threshold: float,
) -> str:
    """Summarize markdown table rows using deterministic row filtering.

    Keeps rows with higher text ratio and drops mostly numeric/symbolic rows.

    :param table_lines: Raw markdown table lines.
    :param text_ratio_threshold: Minimum alphabetic ratio for keeping a row.
    :returns: Short table summary text, or empty string when nothing is kept.
    """
    rows = [line for line in table_lines if not _is_markdown_table_separator(line)]
    if len(rows) < 2:
        return ""

    header = _split_markdown_table_cells(rows[0])
    data_rows = [_split_markdown_table_cells(line) for line in rows[1:]]

    kept: list[str] = []
    for row in data_rows:
        if _row_text_ratio(row) < text_ratio_threshold:
            continue
        if len(row) == len(header) and all(header):
            pairs = [f"{key}: {value}" for key, value in zip(header, row) if value]
            if pairs:
                kept.append("; ".join(pairs))
                continue
        compact = "; ".join(cell for cell in row if cell)
        if compact:
            kept.append(compact)

    if not kept:
        return ""

    limited = kept[:6]
    return "Table highlights: " + " ".join(f"{item}." for item in limited)


def _summarize_table_with_llm(
    table_lines: list[str],
    model: str,
) -> str:
    """Summarize a markdown table via configured cloud LLM provider.

    :param table_lines: Raw markdown table lines.
    :param model: Model identifier. Supports ``gemini-*`` or provider-prefixed
        values like ``openai:gpt-4o-mini`` and ``mistral:mistral-small-latest``.
    :returns: LLM-generated table summary.
    :raises RuntimeError: If API key is missing or request fails.
    """
    table_text = "\n".join(table_lines)
    prompt = (
        "Summarize this markdown table for text-to-speech in 2-4 concise sentences. "
        "Focus on meaningful textual takeaways and key comparisons. "
        "Do not read every numeric cell.\n\n"
        f"{table_text}"
    )

    if model.startswith("openai:"):
        openai_model = model.split(":", 1)[1].strip()
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAI llm-summary models")

        payload = {
            "model": openai_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 220,
        }
        req = request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:
            raise RuntimeError(f"Failed OpenAI table summary request: {exc}") from exc

        try:
            text = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("OpenAI response did not contain summary text") from exc

        if not text:
            raise RuntimeError("OpenAI table summary was empty")
        return text

    if model.startswith("mistral:"):
        mistral_model = model.split(":", 1)[1].strip()
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError("MISTRAL_API_KEY is required for Mistral llm-summary models")

        payload = {
            "model": mistral_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 220,
        }
        req = request.Request(
            "https://api.mistral.ai/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:
            raise RuntimeError(f"Failed Mistral table summary request: {exc}") from exc

        try:
            text = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Mistral response did not contain summary text") from exc

        if not text:
            raise RuntimeError("Mistral table summary was empty")
        return text

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required for Gemini llm-summary models")

    generation_config: dict[str, object] = {"temperature": 0.2, "maxOutputTokens": 220}
    # Gemini 2.5 Pro is thinking-only; cap thinking budget so response tokens are
    # available for the summary text.
    if model == "gemini-2.5-pro":
        generation_config = {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
            "thinkingConfig": {"thinkingBudget": 256},
        }

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    )
    request_timeout = 180 if model == "gemini-2.5-pro" else 60
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            with request.urlopen(req, timeout=request_timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except (error.URLError, socket.timeout, TimeoutError) as exc:
            last_exc = exc
            if attempt < 2:
                time.sleep(1.0 * (attempt + 1))
                continue
    else:
        raise RuntimeError(f"Failed Gemini table summary request: {last_exc}") from last_exc

    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        if "error" in data:
            raise RuntimeError(f"Gemini response error payload: {data['error']}") from exc
        finish_reason = None
        try:
            finish_reason = data.get("candidates", [{}])[0].get("finishReason")
        except (AttributeError, IndexError, KeyError, TypeError):
            finish_reason = None
        raise RuntimeError(
            "Gemini response did not contain summary text"
            + (f" (finishReason={finish_reason})" if finish_reason else "")
        ) from exc

    text = " ".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError("Gemini table summary was empty")
    return text


def _summarize_table_with_local_llm(
    table_lines: list[str],
    model: str,
    endpoint: str,
) -> str:
    """Summarize a markdown table via local Ollama-compatible endpoint.

    :param table_lines: Raw markdown table lines.
    :param model: Local model name.
    :param endpoint: Local HTTP endpoint.
    :returns: LLM-generated table summary text.
    :raises RuntimeError: If local request fails or returns no text.
    """
    table_text = "\n".join(table_lines)
    prompt = (
        "Summarize this markdown table for text-to-speech in 2-4 concise sentences. "
        "Focus on useful textual takeaways and key comparisons. "
        "Do not read every numeric cell.\n\n"
        f"{table_text}"
    )
    if endpoint.endswith("/v1/chat/completions"):
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "stream": False,
        }
    elif endpoint.endswith("/completion") or endpoint.endswith("/v1/completions"):
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": 0.2,
            "n_predict": 220,
            "stream": False,
        }
    else:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except error.URLError as exc:
        raise RuntimeError(f"Failed local LLM table summary request: {exc}") from exc

    text = data.get("response", "").strip()
    if not text:
        text = data.get("content", "").strip()
    if not text:
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                text = str(first.get("text", "")).strip()
                if not text:
                    message = first.get("message")
                    if isinstance(message, dict):
                        text = str(message.get("content", "")).strip()

    if text:
        text = re.sub(r"<think>.*?</think>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"\s+", " ", text).strip()

    if not text:
        raise RuntimeError("Local LLM table summary was empty")
    return text


def _transform_markdown_tables(
    markdown_text: str,
    table_mode: Literal["drop", "label-only", "script", "llm-summary", "local-llm-summary"] = "script",
    text_ratio_threshold: float = 0.45,
    table_llm_model: str = DEFAULT_TABLE_LLM_MODEL,
    table_local_model: str = DEFAULT_TABLE_LOCAL_MODEL,
    table_local_endpoint: str = DEFAULT_TABLE_LOCAL_ENDPOINT,
    fail_on_table_error: bool = False,
) -> str:
    """Transform markdown tables into TTS-friendly summaries.

    :param markdown_text: Raw markdown content.
    :param table_mode: Table handling strategy. ``"label-only"`` keeps the
        table label but drops the table rows. ``"drop"`` silently removes
        both the table block and its label line.
    :param text_ratio_threshold: Script mode row text-ratio threshold.
    :param table_llm_model: LLM model name for table summaries.
    :param table_local_model: Local LLM model name for table summaries.
    :param table_local_endpoint: Local LLM endpoint for table summaries.
    :param fail_on_table_error: If True, disables fallback to script summaries and
        raises on table-summary provider failures.
    :returns: Markdown text with table blocks transformed.
    """
    lines = markdown_text.splitlines()
    transformed: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if not _is_markdown_table_line(line):
            transformed.append(line)
            index += 1
            continue

        table_block = [line]
        table_start = index
        index += 1
        while index < len(lines) and _is_markdown_table_line(lines[index]):
            table_block.append(lines[index])
            index += 1
        table_end = index
        table_label, table_label_index = _extract_table_label(
            lines,
            table_start=table_start,
            table_end=table_end,
        )

        if table_mode == "label-only":
            # Keep the label (already in transformed if pre-table, or advance to it if post-table).
            # Strip trailing statistical annotations like "(N = 30; LIKERT SCALE: ...)" from
            # the caption so only the title portion is spoken, then ensure a sentence boundary.
            def _clean_label(raw: str) -> str:
                # Keep only the table title — strip everything after the first occurrence of:
                # "$(", "(N =", "equation omitted ;", or SRE-spoken "open paren N"
                cleaned = re.sub(
                    r"\s*([\$\(]|equation omitted\s*[;,]|open paren\s+[A-Z]|;LIKERT).*$",
                    "",
                    raw.strip(),
                ).strip()
                if not cleaned:
                    cleaned = raw.strip()
                return cleaned if cleaned[-1] in ".!?" else cleaned + "."

            if (
                table_label_index is not None
                and table_label_index >= table_end
                and index <= table_label_index
            ):
                transformed.append(_clean_label(lines[table_label_index]) + "\n")
                index = table_label_index + 1
            else:
                # Pre-table label already in transformed — clean and ensure period.
                if transformed:
                    transformed[-1] = _clean_label(transformed[-1]) + "\n"
                # The line before the label may be a prose fragment truncated mid-sentence
                # by the physical layout of the table (e.g. "...recorded the\n").
                # If short (< 60 chars) drop it; otherwise add a period so TTS
                # treats it as a standalone utterance rather than running into the label.
                if len(transformed) >= 2:
                    prev = transformed[-2].rstrip()
                    if prev and prev[-1] not in ".!?:":
                        if len(prev.strip()) < 60:
                            transformed.pop(-2)
                        else:
                            transformed[-2] = prev + ".\n"
            continue

        if table_mode == "drop":
            if table_label and transformed and transformed[-1].strip() == table_label:
                transformed.pop()
            if (
                table_label_index is not None
                and table_label_index >= table_end
                and index <= table_label_index
            ):
                index = table_label_index + 1
            continue

        if table_mode == "script":
            summary = _summarize_table_script(table_block, text_ratio_threshold=text_ratio_threshold)
        elif table_mode == "llm-summary":
            try:
                summary = _summarize_table_with_llm(
                    table_block,
                    model=table_llm_model,
                )
            except RuntimeError:
                if fail_on_table_error:
                    raise
                summary = _summarize_table_script(
                    table_block,
                    text_ratio_threshold=text_ratio_threshold,
                )
        else:
            try:
                summary = _summarize_table_with_local_llm(
                    table_block,
                    model=table_local_model,
                    endpoint=table_local_endpoint,
                )
            except RuntimeError:
                if fail_on_table_error:
                    raise
                summary = _summarize_table_script(
                    table_block,
                    text_ratio_threshold=text_ratio_threshold,
                )

        if summary:
            combined_summary = _combine_table_label_and_summary(table_label, summary)
            if transformed and transformed[-1].strip() == table_label:
                transformed.pop()
            transformed.append(combined_summary)

        if table_label_index is not None and table_label_index >= table_end and index <= table_label_index:
            index = table_label_index + 1

    return "\n".join(transformed)

_TRIVIALLY_SPEAKABLE_MAX_LEN = 30


def _is_trivially_speakable(latex: str) -> bool:
    """Return ``True`` if a LaTeX expression is short enough to attempt SRE verbalization.

    Expressions up to :data:`_TRIVIALLY_SPEAKABLE_MAX_LEN` characters are
    routed through SRE in ``placeholder`` and ``strip`` modes instead of being
    replaced with ``"equation omitted"`` or silently dropped.  SRE's own
    fallback handles any expression it cannot convert.

    :param latex: Inner content of a ``$...$`` expression (dollar signs
        already removed).
    :returns: ``True`` if the expression should be attempted via SRE.

    example::

        >>> _is_trivially_speakable("63\\%")
        True
        >>> _is_trivially_speakable("\\frac{x+y+z+a+b+c+d+e+f+g}{w}")
        False
    """
    try:
        return len(latex.strip()) <= _TRIVIALLY_SPEAKABLE_MAX_LEN
    except Exception:
        return False


def _normalize_latex_math(
    text: str,
    math_mode: Literal["strip", "placeholder", "keep", "verbalize"] = "strip",
    sre_bridge: SREBridge | None = None,
) -> str:
    """Normalize LaTeX math regions according to configured math mode.

    Supports four modes:

    ``strip``
        Remove all math expressions silently.
    ``placeholder``
        Replace math with :data:`DEFAULT_MATH_PLACEHOLDER`.
    ``keep``
        Leave math markers in the text unchanged.
    ``verbalize``
        Convert each expression to spoken English via :class:`SREBridge`.
        Requires *sre_bridge* to be provided.  Falls back to
        :data:`DEFAULT_MATH_PLACEHOLDER` on any failure.

    :param text: Source text potentially containing LaTeX math syntax.
    :param math_mode: Handling mode for math content.
    :param sre_bridge: Active :class:`SREBridge` instance; required when
        *math_mode* is ``"verbalize"``, ignored otherwise.
    :returns: Text with math content normalized.
    """
    if math_mode == "keep":
        return text

    if math_mode == "verbalize" and sre_bridge is not None:
        def _replace_math(match: re.Match) -> str:
            return " " + _latex_to_speech(match.group(1).strip(), sre_bridge) + " "

        without_block_math = re.sub(
            r"\$\$\s*(.*?)\s*\$\$",
            _replace_math,
            text,
            flags=re.DOTALL,
        )
        without_inline_math = re.sub(
            r"\$(?!\$)(.*?)(?<!\$)\$",
            _replace_math,
            without_block_math,
        )
    else:
        # Block math is never trivially speakable — always use static replacement.
        _block_replacement = " " if math_mode == "strip" else f" {DEFAULT_MATH_PLACEHOLDER} "
        without_block_math = re.sub(r"\$\$.*?\$\$", _block_replacement, text, flags=re.DOTALL)

        # Inline math: route short expressions through SRE when a bridge is available,
        # EXCEPT expressions that are purely variable names wrapped in \mathrm{},
        # \mathbf{}, \mathit{} etc. — SRE misreads these as physics units
        # (e.g. \mathrm{AT} → "amperes tons", \mathrm{BI} → "bytes I").
        _inline_fallback = " " if math_mode == "strip" else f" {DEFAULT_MATH_PLACEHOLDER} "
        # Matches bare or parenthesised \mathrm{XX}_n variable names.
        # SRE misreads these as physics units (e.g. \mathrm{AT} → "amperes tons").
        _MATHSTYLE_VAR_RE = re.compile(
            r"^(?:\\left\s*\(|[\(\[])?\s*"
            r"\\math(?:rm|bf|it|sf|tt|cal|bb|frak)\s*\{[^{}]+\}"
            r"(?:[_^]\{?[^{}]*\}?)?"
            r"\s*(?:\\right\s*[\)\]]|[\)\]])?\s*$"
        )

        def _replace_inline(match: re.Match) -> str:
            inner = match.group(1).strip()
            # Block \mathrm{AT}_2 style variable names — SRE misreads them as physics units.
            if _MATHSTYLE_VAR_RE.match(inner):
                return _inline_fallback
            # Drop lone superscripts with no base: these are footnote/citation markers
            # placed by the PDF converter, not mathematical exponents.
            if re.fullmatch(r"\^\{?\d{1,3}\}?", inner):
                return _inline_fallback
            # Drop broken display-math fragments: an expression ending with a bare
            # backslash is a split \\ line-break from a mangled \begin{array} block.
            if inner.endswith("\\"):
                return _inline_fallback
            # Strip outer parentheses for simple expressions (no LaTeX commands,
            # subscripts, or superscripts except \%).  Parens around sample sizes
            # and percentages add no audio value and produce unnatural spoken output.
            sre_inner = inner
            if (
                sre_inner.startswith("(")
                and sre_inner.endswith(")")
                and "\\" not in sre_inner.replace("\\%", "")
                and "_" not in sre_inner
                and "^" not in sre_inner
            ):
                sre_inner = sre_inner[1:-1].strip()
            # Normalise digit repeating decimals: 4.\bar{6} → "4.6 repeating".
            # SRE's verbose description is unnatural mid-prose; bypass SRE entirely.
            bar_match = re.fullmatch(r"(\d+\.?\d*)\\bar\{(\d)\}", sre_inner)
            if bar_match:
                return f" {bar_match.group(1)}{bar_match.group(2)} repeating "
            # Pass through prose accidentally captured inside $...$: no backslash,
            # no _ or ^, but contains 3+ consecutive lowercase letters (English words).
            # Replace unicode math symbols with spoken equivalents and return directly.
            if (
                "\\" not in sre_inner
                and "_" not in sre_inner
                and "^" not in sre_inner
                and re.search(r"[a-z]{3,}", sre_inner)
            ):
                plain = (
                    sre_inner
                    .replace("≈", " approximately ")
                    .replace("≤", " at most ")
                    .replace("≥", " at least ")
                )
                return " " + plain.strip() + " "
            if _is_trivially_speakable(sre_inner) and sre_bridge is not None:
                spoken = _latex_to_speech(sre_inner, sre_bridge)
                # SRE renders \% as "percent sign" (Unicode character name); fix to "percent".
                spoken = spoken.replace("percent sign", "percent")
                return " " + spoken + " "
            return _inline_fallback

        without_inline_math = re.sub(
            r"\$(?!\$)(.*?)(?<!\$)\$",
            _replace_inline,
            without_block_math,
        )

    lines: list[str] = []
    for line in without_inline_math.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if re.search(r"\\[A-Za-z]+", stripped):
            if re.search(r"\\(frac|sum|prod|int|sqrt|mathcal|theta|phi|alpha|beta|gamma)", stripped):
                if math_mode == "placeholder":
                    lines.append(DEFAULT_MATH_PLACEHOLDER)
                elif math_mode == "verbalize" and sre_bridge is not None:
                    lines.append(_latex_to_speech(stripped, sre_bridge))
                elif math_mode == "verbalize":
                    lines.append(DEFAULT_MATH_PLACEHOLDER)
                # strip: drop line silently
                continue
            cleaned_line = re.sub(r"\\[A-Za-z]+", " ", stripped)
            cleaned_line = re.sub(r"[{}^_]", " ", cleaned_line)
            cleaned_line = re.sub(r"\s+", " ", cleaned_line).strip()
            if cleaned_line:
                lines.append(cleaned_line)
            continue

        lines.append(stripped)

    return "\n".join(lines)


#region Abbreviation expansion


_ABBREVIATION_REPLACEMENTS: list[tuple[str, str]] = [
    # Academic cross-reference abbreviations (case-sensitive pairs)
    (r"\bEq\.",    "Equation"),
    (r"\beq\.",    "equation"),
    (r"\bEqs\.",   "Equations"),
    (r"\beqs\.",   "equations"),
    (r"\bFig\.",   "Figure"),
    (r"\bfig\.",   "figure"),
    (r"\bFigs\.",  "Figures"),
    (r"\bfigs\.",  "figures"),
    (r"\bSec\.",   "Section"),
    (r"\bsec\.",   "section"),
    (r"\bTab\.",   "Table"),
    (r"\btab\.",   "table"),
    (r"\bThm\.",   "Theorem"),
    (r"\bthm\.",   "theorem"),
    (r"\bDef\.",   "Definition"),
    (r"\bLem\.",   "Lemma"),
    (r"\bProp\.",  "Proposition"),
    (r"\bCor\.",   "Corollary"),
    (r"\bApp\.",   "Appendix"),
    # Common prose abbreviations
    (r"\bvs\.",           "versus"),
    (r"\bw\.r\.t\.",      "with respect to"),
    (r"\bw\.l\.o\.g\.",   "without loss of generality"),
    (r"\bi\.i\.d\.",      "i i d"),
    (r"\bi\.e\.",         "that is"),
    (r"\be\.g\.",         "for example"),
    # et al. — remove trailing dot only; prevents false sentence boundary
    (r" et al\.",         " et al"),
    # URLs — silently remove
    (r"https?://\S+",     ""),
    # Footnote digit markers: "training.4" → "training"
    (r"(\w)\.(\d+)\b",    r"\1"),
]


def _expand_abbreviations(text: str) -> str:
    """Expand common academic abbreviations to their spoken forms.

    Applied after the main line-processing loop in :func:`preprocess_markdown`
    so that abbreviations that cross pseudo-sentence boundaries (e.g. ``et al.``)
    are handled in the fully joined string rather than line by line.

    example::

        result = _expand_abbreviations("See Eq. 3 in Sec. 2.")
        assert "Equation" in result and "Section" in result

    :param text: Joined prose text (post line-processing, pre whitespace collapse).
    :returns: Text with abbreviations expanded and URLs/footnote markers removed.
    """
    for pattern, replacement in _ABBREVIATION_REPLACEMENTS:
        text = re.sub(pattern, replacement, text)
    return text


#endregion


#region ID3 tagging


def _parse_bib_file(bib_path: Path) -> dict[str, dict[str, str]]:
    """Parse a BibTeX file into a dict of cite-key → field dict.

    Supports one level of nested braces in field values and bare-integer
    fields (e.g. ``year = 2024``).

    example::

        entries = _parse_bib_file(Path("references.bib"))
        title = entries["lewis-2020-rag"]["title"]

    :param bib_path: Path to the ``.bib`` file.
    :returns: Dict mapping cite key to a field dict (keys lowercase).
        The special key ``"_type"`` holds the entry type (e.g. ``"article"``).
    """
    text = bib_path.read_text(encoding="utf-8")
    entries: dict[str, dict[str, str]] = {}
    for m in re.finditer(
        r"@(\w+)\s*\{([^,\s]+),\s*(.*?)(?=\n@|\Z)", text, re.DOTALL
    ):
        entry_type = m.group(1).lower()
        key = m.group(2).strip()
        body = m.group(3)
        fields: dict[str, str] = {"_type": entry_type}
        for fm in re.finditer(
            r"(\w+)\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", body
        ):
            fields[fm.group(1).lower()] = fm.group(2).strip()
        for fm in re.finditer(r"(\w+)\s*=\s*(\d{4})", body):
            if fm.group(1).lower() not in fields:
                fields[fm.group(1).lower()] = fm.group(2)
        entries[key] = fields
    return entries


def _format_bib_authors(raw_author: str) -> str:
    """Convert a BibTeX author string to a semicolon-separated display form.

    BibTeX uses ``Lastname, Firstname and Lastname2, Firstname2`` notation.
    This function normalises each name to ``Firstname Lastname`` and joins
    them with ``"; "``.

    example::

        result = _format_bib_authors("Lewis, Patrick and Perez, Ethan")
        assert result == "Patrick Lewis; Ethan Perez"

    :param raw_author: Raw ``author`` field value from a BibTeX entry.
    :returns: Display-form author string.
    """
    authors = []
    for part in re.split(r"\s+and\s+", raw_author, flags=re.IGNORECASE):
        part = part.strip()
        if "," in part:
            last, _, first = part.partition(",")
            authors.append(f"{first.strip()} {last.strip()}")
        else:
            authors.append(part)
    return "; ".join(authors)


def _strip_latex_braces(text: str) -> str:
    """Remove LaTeX grouping braces from a string.

    Handles constructs like ``{LLM}`` and ``{RAG}`` commonly found in BibTeX
    titles to preserve capitalisation.

    example::

        assert _strip_latex_braces("An {LLM}-Driven Chatbot") == "An LLM-Driven Chatbot"

    :param text: Raw BibTeX field value.
    :returns: Text with ``{`` and ``}`` removed.
    """
    return re.sub(r"[{}]", "", text)


def _write_id3_tags(
    mp3_path: Path,
    title: str,
    artists: str,
    album: str,
    year: str,
    comment: str = "",
) -> None:
    """Write ID3v2 tags to an MP3 file using mutagen.

    Tags written: TIT2 (title), TPE1 (artist), TALB (album), TDRC (year),
    COMM (comment).  Any existing ID3 header is replaced.

    example::

        _write_id3_tags(
            Path("paper.mp3"),
            title="Retrieval-Augmented Generation",
            artists="Patrick Lewis; Ethan Perez",
            album="NeurIPS 2020",
            year="2020",
            comment="Introduces RAG for open-domain QA.",
        )

    :param mp3_path: Path to the MP3 file to tag.
    :param title: Track title (paper title).
    :param artists: Semicolon-separated author names.
    :param album: Journal or conference name.
    :param year: Publication year string.
    :param comment: Short abstract or description (truncated to 500 chars).
    :returns: ``None``.
    :raises ImportError: When ``mutagen`` is not installed.
    """
    try:
        from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TDRC, COMM
    except ImportError as exc:
        raise ImportError(
            "mutagen is required for ID3 tagging. Install it with: pip install mutagen"
        ) from exc

    try:
        tags = ID3(str(mp3_path))
    except ID3NoHeaderError:
        tags = ID3()

    tags["TIT2"] = TIT2(encoding=3, text=title)
    tags["TPE1"] = TPE1(encoding=3, text=artists)
    tags["TALB"] = TALB(encoding=3, text=album)
    tags["TDRC"] = TDRC(encoding=3, text=year)
    if comment:
        tags["COMM"] = COMM(encoding=3, lang="eng", desc="", text=comment[:500])

    tags.save(str(mp3_path), v2_version=3)


def resolve_id3_tags_from_bib(
    bib_path: Path,
    cite_key: str,
) -> dict[str, str] | None:
    """Look up a cite key in a BibTeX file and return ID3 tag fields.

    Returns a dict with keys ``title``, ``artists``, ``album``, ``year``,
    ``comment``, ready to pass to :func:`_write_id3_tags`.  Returns ``None``
    when the cite key is not found.

    example::

        tags = resolve_id3_tags_from_bib(Path("references.bib"), "lewis-2020-rag")
        if tags:
            _write_id3_tags(Path("lewis-2020-rag.mp3"), **tags)

    :param bib_path: Path to the ``.bib`` file.
    :param cite_key: BibTeX cite key to look up.
    :returns: Dict of ID3 field values, or ``None`` when not found.
    """
    entries = _parse_bib_file(bib_path)
    entry = entries.get(cite_key)
    if entry is None:
        return None

    title = f"{cite_key} :: {_strip_latex_braces(entry.get('title', cite_key))}"
    raw_author = entry.get("author", "")
    artists = _format_bib_authors(raw_author) if raw_author else ""
    album = _strip_latex_braces(
        entry.get("journal")
        or entry.get("booktitle")
        or (
            "arXiv"
            if entry.get("archiveprefix", "").lower() == "arxiv"
            else entry.get("publisher", "")
        )
    )
    year = entry.get("year", "")
    comment = _strip_latex_braces(entry.get("abstract", ""))
    return {
        "title": title,
        "artists": artists,
        "album": album,
        "year": year,
        "comment": comment,
    }


#endregion


def _is_prose_line(line: str) -> bool:
    """Return True when a line looks like a genuine prose sentence.

    Used to detect the end of the front-matter zone.  A line qualifies when it
    is long enough to be a sentence (≥ 60 chars), starts with an uppercase
    letter, and contains at least two whitespace-separated words.

    example::

        assert _is_prose_line("Self-efficacy has emerged as a highly effective predictor of motivation.")
        assert not _is_prose_line("Barry J. Zimmerman")

    :param line: Stripped line of text.
    :returns: ``True`` when the line resembles a prose sentence.
    """
    if len(line) < 60:
        return False
    if not line[0].isupper():
        return False
    # Must have multiple words
    words = line.split()
    return len(words) >= 8


# Patterns that identify front-matter noise lines.
# Applied only within the front-matter zone (before the first prose line).
_FRONT_MATTER_STRIP_PATTERNS: list[re.Pattern[str]] = [
    # Affiliation superscripts: ^{1}, ^{1,2}, ^{†}, $^{1}$, ¹, ², ³ at line start
    re.compile(r"^\^?\{[0-9†‡∗♢,∗ ]+\}"),
    re.compile(r"^\$\^\{[^}]+\}\$"),
    re.compile(r"^[¹²³⁴⁵⁶⁷⁸⁹⁰]"),
    # Author-name lines with inline ^{N} superscripts (e.g. "Alice^{1,*}, Bob^{2}")
    re.compile(r"\^{[0-9†‡∗♢,∗ ]+}"),
    # Email addresses anywhere on the line (covers email-only lines and "Corresponding author:")
    re.compile(r"\b[A-Za-z0-9._%+\-{}]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    # DOI lines
    re.compile(r"^\s*(?:doi|DOI)\s*[:\.]?\s*10\.", re.IGNORECASE),
    # arXiv identifier lines
    re.compile(r"^\s*arXiv\s*:\s*\d{4}\.\d+", re.IGNORECASE),
    # ISSN / ISBN
    re.compile(r"\bISSN\b|\bISBN\b", re.IGNORECASE),
    # Volume/Issue/Page-range journal metadata: "Vol. 3, No. 4 (2009) 333-389"
    re.compile(r"\bVol(?:ume)?\.?\s*\d+\b", re.IGNORECASE),
    # Journal citation header: "Journal Name 25, 82-91, (2000)" — volume, page-range, year
    re.compile(r"\b\d+,\s*\d+[-–]\d+.*\(?[12]\d{3}\)?"),
    # Page-number-only line: "122" or "pp. 412-425"
    re.compile(r"^\s*(?:pp?\.\s*)?\d+[-–]\d+\s*$"),
    re.compile(r"^\s*\d{1,4}\s*$"),
    # Copyright lines: "© 2000 Academic Press", "Copyright © ..."
    re.compile(r"©|Copyright\s+©?", re.IGNORECASE),
    # Published/accepted/received date lines (line starts with keyword)
    re.compile(
        r"^\s*(?:Published|Accepted|Received|Review (?:began|ended)|Available online)\b",
        re.IGNORECASE,
    ),
    # Journal submission/publication header: "Journal Name; Vol X(Y) pp Received D-M-YYYY; ..."
    # Catches combined metadata lines like "Advances in AI... Research 4 (4) 3097-3113 Received 5-10-2024; Accepted..."
    re.compile(r"\bReceived\s+\d+[-/]\d+[-/]\d{4}\b", re.IGNORECASE),
    # Publisher labels: single-word/short known publisher names on their own line
    re.compile(
        r"^\s*(?:MDPI|Cureus|Pergamon|ELSEVIER|Routledge|SAGE|sciendo|ResearchGate|"
        r"now|the essence of knowledge|Check for updates|Open Access|"
        r"RESEARCH ESSAY|Research Article|Invited Paper|Article)\s*$",
        re.IGNORECASE,
    ),
    # ResearchGate artefacts
    re.compile(
        r"^\s*(?:SEE PROFILE|View project|CITATIONS|READS|"
        r"See discussions,\s*stats|Some of the authors|"
        r"All content following this page|The user has requested)\b",
        re.IGNORECASE,
    ),
    # "Follow this and additional works at:" / "Recommended Citation" / "Available at:"
    re.compile(
        r"^\s*(?:Follow this and additional works|Recommended Citation|"
        r"Part of the|Available at\s*:)\b",
        re.IGNORECASE,
    ),
    # "To cite this article:" / "To link to this article:"
    re.compile(r"^\s*To (?:cite|link to) this article\b", re.IGNORECASE),
    # "Submit your article" / "Article views:" / "View related articles"
    re.compile(
        r"^\s*(?:Submit your article|Article views|View related articles|"
        r"Full Terms|Cocktack|ARTICLE\s*$)",
        re.IGNORECASE,
    ),
    # Bracketed affiliation blocks: [ Inst email ]
    re.compile(r"^\[.*@.*\]$"),
    # [Equal contribution] / [equal advising]
    re.compile(r"^\[.*(?:contribution|advising|author).*\]$", re.IGNORECASE),
    # "^{*}Equal Contribution, ^{†}Equal Advising" inline patterns
    re.compile(r"\^\{[*†‡]\}Equal\s+(?:Contribution|Advising|Author)", re.IGNORECASE),
    # Single bare "d" artifact (dyantyi paper)
    re.compile(r"^\s*d\s*$"),
    # "ERROR" artifact
    re.compile(r"^\s*ERROR\s*$"),
    # Bare "." separator lines
    re.compile(r"^\s*\.\s*$"),
    # "2 authors:" ResearchGate
    re.compile(r"^\s*\d+\s+authors?:\s*$", re.IGNORECASE),
    # Image lines (already stripped later, but remove early to avoid confusing zone detection)
    re.compile(r"^!\["),
]

# Patterns applied globally (inside AND outside the front-matter zone).
# These catch metadata lines that appear after the abstract — e.g. DOIs,
# copyright notices, footnote-style affiliations, and submission dates that
# journals typeset at the bottom of the first page.
_GLOBAL_NOISE_PATTERNS: list[re.Pattern] = [
    # Journal running headers: "SMITH et al.: TITLE OF PAPER" or "SMITH et al: TITLE"
    # Typical IEEE/ACM format — UPPERCASE author(s) followed by colon and ALL-CAPS title
    re.compile(r"^[A-Z][A-Z\s]+\bet al[.:]?\s*:?\s+[A-Z][A-Z\s,\-]{10,}$"),
    # Journal volume header: "IEEE TRANSACTIONS ON X, VOL. N, NO. N, MONTH YEAR"
    re.compile(r"\bVOL\.\s*\d+\b.*\bNO\.\s*\d+\b", re.IGNORECASE),
    # Emails inline: "(e-mail: x@y)"
    re.compile(r"\(e-mail:\s*\S+@", re.IGNORECASE),
    # DOI line: "Digital Object Identifier 10.xxxx"
    re.compile(r"^\s*Digital Object Identifier\s+10\.", re.IGNORECASE),
    # Received/revised/accepted dates: "Received 13 November 2023"
    re.compile(r"^\s*Received\s+\d+\s+\w+\s+\d{4}", re.IGNORECASE),
    # Date of publication / current version
    re.compile(r"^\s*Date of (?:publication|current version)\b", re.IGNORECASE),
    # Footnote URL lines: "1 https://moodle.org"
    re.compile(r"^\s*\d+\s+https?://"),
    # Copyright / © lines
    re.compile(r"©|Copyright\s+©?", re.IGNORECASE),
    # Academic editor / handling editor
    re.compile(r"^\s*(?:Academic|Handling)\s+[Ee]ditor\s*:", re.IGNORECASE),
    # Publisher's Note
    re.compile(r"^\s*Publisher(?:'s)?\s*Note\s*:", re.IGNORECASE),
    # "Citation:" attribution lines
    re.compile(r"^\s*Citation\s*:", re.IGNORECASE),
    # Revised/published online date
    re.compile(r"^\s*(?:Revised|Published online)\s+\d+\s+\w+\s+\d{4}", re.IGNORECASE),
    # Corresponding author label
    re.compile(r"^\s*Corresponding [Aa]uthor\s*[:\.]"),
    # Superscript-numbered affiliation lines: "¹ University of..."
    re.compile(r"^\s*[¹²³⁴⁵⁶⁷⁸⁹]\s+\w"),
    # "How to cite this article"
    re.compile(r"^\s*How to cite this\b", re.IGNORECASE),
    # ACM-style permission block
    re.compile(r"^\s*Permission to make digital or hard copies\b", re.IGNORECASE),
    # "Revised: DD Month YYYY" (alternate form)
    re.compile(r"^\s*Revised:\s+\d+\s+\w+\s+\d{4}", re.IGNORECASE),
]


def _strip_paper_front_matter(markdown_text: str) -> str:
    """Remove bibliographic noise from the front-matter zone of a paper.

    The *front-matter zone* ends at the first prose line (≥ 60 chars, starts
    uppercase, ≥ 8 words).  Within that zone, lines matching known noise
    patterns (affiliations, DOIs, publisher labels, emails, copyright notices,
    etc.) are dropped.  Everything from the first prose line onwards is
    returned unchanged.

    This function is profile-agnostic: it is safe to call on any markdown
    profile because it never touches body text.

    example::

        md = (
            "Contemporary Educational Psychology 25, 82–91, (2000)\\n"
            "doi:10.1006/ceps.1999.1016\\n"
            "# Self-Efficacy: An Essential Motive to Learn\\n"
            "Barry J. Zimmerman\\n"
            "Graduate School and University Center of City University of New York\\n"
            "During the past two decades, self-efficacy has emerged as a highly "
            "effective predictor of students' motivation and learning.\\n"
        )
        result = _strip_paper_front_matter(md)
        assert "Self-Efficacy" in result
        assert "doi" not in result.lower()
        assert "Graduate School" not in result
        assert "During the past two decades" in result

    :param markdown_text: Raw markdown document string.
    :returns: Markdown with front-matter noise removed.
    """
    # Strip HTML comments (e.g. "<!-- Source PDF: ... -->") before line processing.
    # These must not be sent to TTS but must remain in the source Markdown.
    markdown_text = re.sub(r"<!--.*?-->", "", markdown_text, flags=re.DOTALL)
    lines = markdown_text.splitlines(keepends=True)
    result: list[str] = []
    in_front_matter = True

    for line in lines:
        stripped = line.strip()

        if not in_front_matter:
            # Even outside the front-matter zone, drop known global noise lines.
            # Guard: never drop headings or blank lines.
            if stripped and not re.match(r"^#{1,6}\s", stripped):
                if any(pat.search(stripped) for pat in _GLOBAL_NOISE_PATTERNS):
                    continue  # drop post-abstract noise
            result.append(line)
            continue

        # A heading line is always kept; headings cannot be noise
        if re.match(r"^#{1,6}\s", stripped):
            result.append(line)
            continue

        # Empty lines pass through (preserve structure)
        if not stripped:
            result.append(line)
            continue

        # Check against noise patterns BEFORE prose detection so that long
        # author-name lines with inline superscripts are stripped even though
        # they would otherwise pass the prose heuristic.
        if any(pat.search(stripped) for pat in _FRONT_MATTER_STRIP_PATTERNS):
            continue  # drop this line

        # Once we hit a genuine prose line, leave the front-matter zone
        if _is_prose_line(stripped):
            in_front_matter = False

        result.append(line)

    return "".join(result)


def _find_keshav_fallback_heading(text: str) -> str | None:
    """Return the normalised text of the last H2 section before stop headings.

    Used by the keshav-pass1 state machine as a fallback conclusions trigger
    when no standard conclusions heading (Conclusion, Summary, etc.) is found.
    The last major section of a paper — whatever it is named — is the closest
    available proxy for the paper's terminal synthesis.

    Three-tier selection:

    1. If a standard conclusions heading exists (matched by ``_KESHAV_CONCLUSIONS_RE``),
       return ``None`` — the main loop handles it without any fallback.
    2. Otherwise return the **last whitelist-matching heading** before stop headings
       (e.g. "Discussion", "Limitations", "Future Work").
    3. If no whitelist heading exists either, return the **last H1–H3 heading** before
       stop headings as a last-resort fallback.

    example::

        md = "## Introduction\\n\\n## Methods\\n\\n## Discussion\\n\\n## References\\n"
        assert _find_keshav_fallback_heading(md) == "Discussion"

    :param text: Preprocessed markdown text (after math/table transforms).
    :returns: Normalised heading text (section numbers stripped) of the selected
        fallback heading, or ``None`` if no fallback is needed or available.
    """
    last_whitelist: str | None = None
    last_heading: str | None = None
    has_conclusions_heading = False
    first_h1_seen = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading_match = re.match(r"^(#{1,3})\s+(.+?)\s*$", line)
        if not heading_match:
            continue
        is_h1 = len(heading_match.group(1)) == 1
        # Skip the first H1 — it is always the paper title, not a section.
        if is_h1 and not first_h1_seen:
            first_h1_seen = True
            continue
        first_h1_seen = True
        heading_text_raw = heading_match.group(2).strip().rstrip(".:")
        heading_text_norm = re.sub(r"^\d+\.?\s+", "", heading_text_raw).strip()
        if heading_text_norm.lower() in PAPER_STOP_HEADINGS:
            break
        if _KESHAV_CONCLUSIONS_RE.match(heading_text_norm):
            has_conclusions_heading = True
        elif _KESHAV_WHITELIST_RE.match(heading_text_norm):
            last_whitelist = heading_text_norm
            last_heading = heading_text_norm
        else:
            last_heading = heading_text_norm
    # Tier 1: standard conclusions heading found — main loop handles it.
    if has_conclusions_heading:
        return None
    # Tier 2: last whitelist-matching heading.
    if last_whitelist is not None:
        return last_whitelist
    # Tier 3: last section regardless of name.
    return last_heading


def preprocess_markdown(
    markdown_text: str,
    markdown_profile: Literal[
        "general",
        "paper",
        "paper-lean",
        "keshav-pass1",
        "keshav-pass2",
        "keshav-pass3",
    ] = "general",
    math_mode: Literal["strip", "placeholder", "keep", "verbalize"] = "strip",
    table_mode: Literal["drop", "label-only", "script", "llm-summary", "local-llm-summary"] = "script",
    figure_mode: Literal["speak", "label-only", "drop"] | None = None,
    table_text_ratio_threshold: float = 0.45,
    table_llm_model: str = DEFAULT_TABLE_LLM_MODEL,
    table_local_model: str = DEFAULT_TABLE_LOCAL_MODEL,
    table_local_endpoint: str = DEFAULT_TABLE_LOCAL_ENDPOINT,
    fail_on_table_error: bool = False,
) -> str:
    """Normalize markdown into speech-friendly plain text.

    example::

        text = preprocess_markdown("# Title\nA claim [1].")
        assert "Title" in text

    :param markdown_text: Raw Markdown document content.
    :param markdown_profile: Preprocessing profile. ``paper`` skips trailing
        sections such as references/acknowledgements. ``paper-lean`` also
        skips common paper front/back-matter sections.
        ``keshav-pass1`` implements Keshav's Pass 1 reading strategy: abstract,
        introduction, middle-section headings only (body dropped), and conclusions.
        ``keshav-pass2`` reads the full paper body with math placeholders; table
        and figure labels are kept but their content is dropped. ``keshav-pass3``
        reads the full paper body with full math verbalization and LLM table summaries.
    :param math_mode: Math handling mode for LaTeX/equation content.
        Use ``"verbalize"`` to convert equations to spoken English via
        :class:`SREBridge` (requires Node.js + ``speech-rule-engine``).
    :param table_mode: Table handling strategy.
    :param figure_mode: Figure handling strategy. ``"speak"`` converts figure
        labels and ``<details>`` descriptions to spoken text; ``"label-only"``
        keeps labels but drops descriptions (default for ``keshav-pass2``);
        ``"drop"`` silently removes both. ``None`` uses the profile default.
    :param table_text_ratio_threshold: Script table row text-ratio threshold.
    :param table_llm_model: LLM model name used for table summaries.
    :param table_local_model: Local LLM model used for table summaries.
    :param table_local_endpoint: Local LLM endpoint used for table summaries.
    :param fail_on_table_error: If True, disables fallback to script summaries and
        raises on table-summary provider failures.
    :returns: Cleaned plain text suitable for TTS chunking.
    """
    # keshav-pass2 and keshav-pass3 are aliases for paper-lean text extraction;
    # the difference is only in math/table defaults (applied by the CLI preset layer).
    # keshav-pass1 uses its own state machine but still needs paper-lean stop/skip logic.
    _effective_profile = markdown_profile
    if markdown_profile in {"keshav-pass1", "keshav-pass2", "keshav-pass3"}:
        _effective_profile = "paper-lean"

    if _effective_profile in {"paper", "paper-lean"}:
        markdown_text = _strip_paper_front_matter(markdown_text)

    without_code_blocks = re.sub(r"```.*?```", " ", markdown_text, flags=re.DOTALL)

    sre_bridge: SREBridge | None = None
    if math_mode != "keep":
        try:
            sre_bridge = SREBridge()
        except FileNotFoundError:
            if math_mode == "verbalize":
                import sys
                print(
                    "\nWarning: --math-mode verbalize requires Node.js and speech-rule-engine.\n"
                    "  Node.js was not found on PATH.\n"
                    "\n"
                    "  To install:\n"
                    "    1. Install Node.js >= 18: https://nodejs.org\n"
                    "    2. npm install -g speech-rule-engine\n"
                    "\n"
                    "  Falling back to --math-mode placeholder (equations will be read as 'equation omitted').\n"
                    "  Re-run with --math-mode placeholder to suppress this warning.",
                    file=sys.stderr,
                )
            # strip / placeholder: Node absent — silently fall back to default behaviour

    try:
        normalized_math = _normalize_latex_math(
            without_code_blocks,
            math_mode=math_mode,
            sre_bridge=sre_bridge,
        )
    finally:
        if sre_bridge is not None:
            sre_bridge.close()
    normalized_tables = _transform_markdown_tables(
        normalized_math,
        table_mode=table_mode,
        text_ratio_threshold=table_text_ratio_threshold,
        table_llm_model=table_llm_model,
        table_local_model=table_local_model,
        table_local_endpoint=table_local_endpoint,
        fail_on_table_error=fail_on_table_error,
    )
    # Resolve figure_mode: explicit argument wins; otherwise keshav-pass2 uses
    # label-only (keeps labels, drops descriptions), everything else speaks.
    _figure_mode: Literal["speak", "label-only", "drop"] = (
        figure_mode
        if figure_mode is not None
        else ("label-only" if markdown_profile == "keshav-pass2" else "speak")
    )
    normalized_figures = _transform_markdown_figures(normalized_tables, figure_mode=_figure_mode)

    # keshav-pass1: pre-scan to find the last H2 section before stop headings.
    # Used as a fallback conclusions trigger when no standard conclusions heading
    # is present (e.g. papers that use "Discussion" or "Design Implications").
    kp1_fallback_heading: str | None = None
    if markdown_profile == "keshav-pass1":
        kp1_fallback_heading = _find_keshav_fallback_heading(normalized_figures)

    lines: list[str] = []
    skipping_lean_section = False

    # keshav-pass1 state machine states:
    #   "intro"   — reading abstract/introduction in full
    #   "middle"  — past introduction; emit headings only, drop body text
    #   "concl"   — inside conclusions section; read in full again
    # Starts in "intro" because everything before the first non-intro H1/H2 is
    # treated as the introduction zone (handles papers without an explicit heading).
    kp1_state = "intro"
    kp1_reached_concl = False
    kp1_title_h1_seen = False  # tracks whether the paper-title H1 has been consumed

    for raw_line in normalized_figures.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading_match = re.match(r"^#{1,6}\s*(.+?)\s*$", line)
        if heading_match and _effective_profile in {"paper", "paper-lean"}:
            heading_text = heading_match.group(1).strip().lower().rstrip(".:")
            # Strip leading section numbers (e.g. "6. references" → "references")
            heading_text_norm = re.sub(r"^\d+[\d.]*\.?\s+", "", heading_text).strip()
            if heading_text_norm in PAPER_STOP_HEADINGS:
                break
            if _effective_profile == "paper-lean":
                if (
                    heading_text in PAPER_LEAN_SKIP_HEADINGS
                    or heading_text.startswith("appendix")
                ):
                    skipping_lean_section = True
                    continue
                skipping_lean_section = False

        if _effective_profile == "paper-lean" and skipping_lean_section:
            continue

        # keshav-pass1: update state on H1–H3 headings, then decide inclusion.
        # The very first H1 is the paper title — skip zone transitions for it only.
        # All subsequent H1s (sections like "# 2. Background") are treated as
        # normal section headings and may trigger the middle zone.
        if markdown_profile == "keshav-pass1" and heading_match:
            raw_heading_level_match = re.match(r"^(#{1,3})\s", line)
            is_h1 = raw_heading_level_match and len(raw_heading_level_match.group(1)) == 1
            # Only the very first H1 is the title; once seen, subsequent H1s are sections.
            is_title_h1 = is_h1 and not kp1_title_h1_seen
            if is_h1:
                kp1_title_h1_seen = True
            if raw_heading_level_match and not is_title_h1:
                heading_text_raw = heading_match.group(1).strip().rstrip(".:")
                # Strip leading section numbers for matching.
                heading_text_norm = re.sub(r"^\d+\.?\s+", "", heading_text_raw).strip()
                # Stop at references/acknowledgements.
                if heading_text_norm.lower() in PAPER_STOP_HEADINGS:
                    break
                # Transition into conclusions zone: standard match OR fallback.
                is_concl = _KESHAV_CONCLUSIONS_RE.match(heading_text_norm)
                is_fallback = (
                    kp1_fallback_heading is not None
                    and heading_text_norm.lower() == kp1_fallback_heading.lower()
                )
                if is_concl or is_fallback:
                    kp1_state = "concl"
                    kp1_reached_concl = True
                elif kp1_state == "intro":
                    # First H2/H3 that is not introduction or abstract → middle zone.
                    is_intro_or_abstract = (
                        _KESHAV_INTRO_RE.match(heading_text_norm)
                        or heading_text_norm.lower().startswith("abstract")
                    )
                    if not is_intro_or_abstract:
                        kp1_state = "middle"
                elif kp1_state == "concl":
                    # Another section after conclusions → we are past the paper body.
                    break

        heading_match = re.match(r"^(#{1,6})\s", line)
        is_heading = bool(heading_match)
        heading_level = len(heading_match.group(1)) if heading_match else 0

        # keshav-pass1: in middle state, only emit headings (drop body text).
        if markdown_profile == "keshav-pass1" and kp1_state == "middle" and not is_heading:
            continue

        line = re.sub(r"^#{1,6}\s*", "", line)
        # Strip leading section numbers from headings (e.g. "1 Intro", "7.2 Methods").
        if is_heading:
            line = re.sub(r"^\d+(\.\d+)*\.?\s+", "", line)
        line = re.sub(r"^>\s*", "", line)
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"^\d+\.\s+", "", line)

        line = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", line)
        line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        line = re.sub(r"\[(?:\d+(?:\s*,\s*\d+)*)\]", "", line)
        line = re.sub(r"\(([A-Za-z][^()]{0,80}?\b\d{4}[a-z]?[^()]*)\)", "", line)
        line = re.sub(r"[*_]{1,3}", "", line)

        if line.startswith("|") and line.endswith("|"):
            continue
        if re.fullmatch(r"\|?[\s:-]+\|[\s|:-]*", line):
            continue

        cleaned = line.strip()
        if cleaned:
            if is_heading and cleaned and cleaned[-1] not in ".!?:":
                cleaned = cleaned + "."
            if is_heading:
                cleaned = f"\x00H{heading_level}\x00{cleaned}"
            lines.append(cleaned)

    joined = _expand_abbreviations(" ".join(lines))
    return re.sub(r"\s+", " ", joined).strip()


def chunk_text(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[str]:
    """Split text into speech-safe chunks by sentence when possible.

    Heading sentinels (``\\x00H<level>\\x00<text>``) are always isolated into
    their own atomic chunk regardless of surrounding punctuation.  The input is
    first split on sentinel boundaries, then each non-sentinel segment is
    sentence-split within the character limit.

    example::

        parts = chunk_text("Hello world. This is a demo.", max_chars=12)
        assert parts == ["Hello world.", "This is a", "demo."]

    :param text: Source text to split.
    :param max_chars: Maximum number of characters per chunk.
    :returns: A non-empty list of cleaned text chunks.
    :raises ValueError: If ``max_chars`` is not positive.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be > 0")

    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    # Split on sentinel boundaries so headings are always atomic segments.
    # Sentinels are \x00H<n>\x00<heading text ending in .!?> — always end with
    # sentence-terminal punctuation added during preprocessing.  The capturing
    # group keeps sentinels in the result list.
    segments = re.split(r"(\x00H[1-6]\x00[^.!?\x00]*[.!?])", normalized)

    chunks: list[str] = []
    current = ""

    for segment in segments:
        seg = segment.strip()
        if not seg:
            continue

        # Heading sentinel: flush current buffer, emit sentinel as own chunk.
        if HEADING_SENTINEL_RE.match(seg):
            if current:
                chunks.append(current)
                current = ""
            chunks.append(seg)
            continue

        # Non-sentinel segment: sentence-split within max_chars.
        sentences = re.split(r"(?<=[.!?])\s+", seg)
        for sentence in sentences:
            candidate = sentence if not current else f"{current} {sentence}"
            if len(candidate) <= max_chars:
                current = candidate
                continue

            if current:
                chunks.append(current)
                current = ""

            if len(sentence) <= max_chars:
                current = sentence
                continue

            start = 0
            while start < len(sentence):
                end = start + max_chars
                chunks.append(sentence[start:end])
                start = end

    if current:
        chunks.append(current)

    return chunks


def ensure_output_path(output_path: Path) -> Path:
    """Create output parent directories and ensure an mp3 extension.

    example::

        target = ensure_output_path(Path("outputs/paper_audio"))
        assert target.suffix == ".mp3"

    :param output_path: Target file path from CLI input.
    :returns: Normalized output path with ``.mp3`` extension.
    """
    normalized = output_path if output_path.suffix else output_path.with_suffix(".mp3")
    normalized.parent.mkdir(parents=True, exist_ok=True)
    return normalized


def synthesize_markdown_file(
    markdown_path: Path,
    output_path: Path,
    markdown_profile: Literal["general", "paper", "paper-lean"] = "general",
    math_mode: Literal["strip", "placeholder", "keep", "verbalize"] = "strip",
    table_mode: Literal["drop", "label-only", "script", "llm-summary", "local-llm-summary"] = "script",
    table_text_ratio_threshold: float = 0.45,
    table_llm_model: str = DEFAULT_TABLE_LLM_MODEL,
    table_local_model: str = DEFAULT_TABLE_LOCAL_MODEL,
    table_local_endpoint: str = DEFAULT_TABLE_LOCAL_ENDPOINT,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    volume: str = DEFAULT_VOLUME,
    max_chars: int = DEFAULT_MAX_CHARS,
    console_trace: bool = False,
    id3_tags: dict[str, str] | None = None,
) -> Path:
    """Read a Markdown file, clean it, and synthesize to MP3.

    example::

        out = synthesize_markdown_file(
            markdown_path=Path("paper.md"),
            output_path=Path("paper.mp3"),
        )
        print(out)

    :param markdown_path: Source Markdown file path.
    :param output_path: Destination MP3 path.
    :param markdown_profile: Markdown preprocessing profile.
    :param math_mode: Math handling mode for LaTeX/equation content.
    :param table_mode: Table handling strategy.
    :param table_text_ratio_threshold: Script table row text-ratio threshold.
    :param table_llm_model: LLM model name used for table summaries.
    :param table_local_model: Local LLM model used for table summaries.
    :param table_local_endpoint: Local LLM endpoint used for table summaries.
    :param voice: Edge voice identifier.
    :param rate: Speaking rate value.
    :param volume: Output volume value.
    :param max_chars: Chunk size limit for each synthesis request.
    :param console_trace: Whether to print span data to stdout.
    :param id3_tags: Optional dict with keys ``title``, ``artists``, ``album``,
        ``year``, ``comment`` to embed as ID3 metadata.  When ``None``, no tags
        are written.
    :returns: Path to generated MP3 file.
    """
    markdown_text = markdown_path.read_text(encoding="utf-8")
    cleaned_text = preprocess_markdown(
        markdown_text,
        markdown_profile=markdown_profile,
        math_mode=math_mode,
        table_mode=table_mode,
        table_text_ratio_threshold=table_text_ratio_threshold,
        table_llm_model=table_llm_model,
        table_local_model=table_local_model,
        table_local_endpoint=table_local_endpoint,
    )
    return synthesize_to_mp3(
        input_text=cleaned_text,
        output_path=output_path,
        voice=voice,
        rate=rate,
        volume=volume,
        max_chars=max_chars,
        console_trace=console_trace,
        id3_tags=id3_tags,
    )

#endregion


#region Edge synthesis

async def _synthesize_chunks(
    chunks: list[str],
    output_path: Path,
    voice: str,
    rate: str,
    volume: str,
    tracer: trace.Tracer,
) -> None:
    """Synthesize all chunks and append them into one MP3 stream.

    :param chunks: Preprocessed text chunks.
    :param output_path: Destination MP3 path.
    :param voice: Edge voice name.
    :param rate: Speaking-rate value (e.g. ``+10%``).
    :param volume: Volume value (e.g. ``+0%``).
    :param tracer: OpenTelemetry tracer.
    :returns: ``None``.
    """
    try:
        import edge_tts
    except ImportError as exc:  # pragma: no cover - dependency/runtime concern
        raise RuntimeError(
            "edge-tts is not installed. Add it to requirements and install dependencies."
        ) from exc

    if output_path.exists():
        output_path.unlink()

    with tracer.start_as_current_span("synthesize") as span:
        span.set_attribute("tts.chunks", len(chunks))
        span.set_attribute("tts.voice", voice)

        for index, chunk in enumerate(chunks, start=1):
            with tracer.start_as_current_span("chunk") as chunk_span:
                chunk_span.set_attribute("chunk.index", index)
                chunk_span.set_attribute("chunk.length", len(chunk))

                heading_match = HEADING_SENTINEL_RE.match(chunk)
                if heading_match:
                    text = heading_match.group(2)
                    chunk_rate = rate
                    chunk_pitch = "-10Hz"
                    chunk_span.set_attribute("chunk.kind", "heading")
                    chunk_span.set_attribute("chunk.heading_level", int(heading_match.group(1)))
                else:
                    text = chunk
                    chunk_rate = rate
                    chunk_pitch = "+0Hz"
                    chunk_span.set_attribute("chunk.kind", "body")

                communicate = edge_tts.Communicate(
                    text=text,
                    voice=voice,
                    rate=chunk_rate,
                    pitch=chunk_pitch,
                    volume=volume,
                )

                async for item in communicate.stream():
                    if item["type"] == "audio":
                        with output_path.open("ab") as f_out:
                            f_out.write(item["data"])


def synthesize_to_mp3(
    input_text: str,
    output_path: Path,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    volume: str = DEFAULT_VOLUME,
    max_chars: int = DEFAULT_MAX_CHARS,
    console_trace: bool = False,
    id3_tags: dict[str, str] | None = None,
) -> Path:
    """Convert input text to MP3 using Edge TTS.

    example::

        out = synthesize_to_mp3(
            input_text="A short abstract from a paper.",
            output_path=Path("topics/tts/outputs/abstract.mp3"),
        )
        print(out)

    :param input_text: Full text to synthesize.
    :param output_path: Destination path for generated MP3.
    :param voice: Edge voice identifier.
    :param rate: Speaking rate value.
    :param volume: Output volume value.
    :param max_chars: Chunk size limit for each synthesis request.
    :param console_trace: Whether to print span data to stdout.
    :param id3_tags: Optional dict with keys ``title``, ``artists``, ``album``,
        ``year``, ``comment`` to embed as ID3 metadata.  When ``None``, no tags
        are written.
    :returns: Path to generated MP3 file.
    :raises ValueError: If the input text is empty after normalization.
    """
    tracer = _setup_tracing(console_trace=console_trace)

    with tracer.start_as_current_span("paper_to_audio") as span:
        chunks = chunk_text(input_text, max_chars=max_chars)
        if not chunks:
            raise ValueError("input text is empty after normalization")

        target = ensure_output_path(output_path)
        span.set_attribute("output.path", str(target))
        span.set_attribute("chunk.count", len(chunks))

        asyncio.run(
            _synthesize_chunks(
                chunks=chunks,
                output_path=target,
                voice=voice,
                rate=rate,
                volume=volume,
                tracer=tracer,
            )
        )

    if id3_tags:
        _write_id3_tags(target, **id3_tags)

    return target

#endregion


#region CLI

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the Edge TTS pipeline.

    example::

        args = parse_args()
        print(args.voice)

    :returns: Parsed CLI namespace.
    """
    parser = argparse.ArgumentParser(description="Convert text files to MP3 with Edge TTS")
    parser.add_argument("--input", required=True, type=Path, help="Input UTF-8 text file")
    parser.add_argument("--output", required=True, type=Path, help="Output MP3 file path")
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
    return parser.parse_args()


def main() -> None:
    """Run the CLI entry point for paper-to-audio conversion.

    example::

        # python topics/tts/src/edge_tts_pipeline.py --input paper.txt --output paper.mp3

    :returns: ``None``.
    """
    args = parse_args()
    input_text = args.input.read_text(encoding="utf-8")
    output_file = synthesize_to_mp3(
        input_text=input_text,
        output_path=args.output,
        voice=args.voice,
        rate=args.rate,
        volume=args.volume,
        max_chars=args.max_chars,
        console_trace=args.trace,
    )
    print(f"Generated: {output_file}")


if __name__ == "__main__":
    main()

#endregion
