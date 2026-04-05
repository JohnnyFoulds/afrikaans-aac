# transcribe-youtube

Download a YouTube video's audio, transcribe it locally, and create a structured
`literature/radar/` note with AI-generated summary and relevance analysis.

**Usage:** `/transcribe-youtube <url> [options]`

**Options:**
- `--relevance "<hint>"` — hint for the AI: why is this potentially relevant? (improves synthesis quality)
- `--slug <slug>` — output filename stem (default: derived from video title)
- `--transcript-dir <path>` — where to save the raw transcript (default: `literature/radar/transcripts/`)
- `--radar-dir <path>` — where to save the radar note (default: `literature/radar/`)
- `--model <id>` — MLX Whisper model (default: `mlx-community/whisper-base.en-mlx`; use `mlx-community/whisper-large-v3-mlx` for higher accuracy on long or technical videos)
- `--no-synthesis` — skip Claude synthesis, write placeholders instead

## What it produces

**`literature/radar/<slug>.md`** — structured radar note containing:
- Full frontmatter (title, author, channel, date, duration, status, relevance, transcript path)
- `## Why on radar` — AI-generated relevance assessment against the RAG-for-ODL research
- `## Source quality` — AI assessment of source type and credibility basis
- `## Summary` — AI-generated 2–4 sentence summary
- `## Key claims` — bullet list of main points
- `## Connections to research` — placeholder for manual linking
- Link to raw transcript file

**`literature/radar/transcripts/<slug>.txt`** — raw transcript text (kept separate from the note)

## Pipeline

1. `yt-dlp --dump-json` → fetch metadata (title, channel, date, duration)
2. `yt-dlp --extract-audio` → download MP3 to temp dir
3. `mlx_whisper` → transcribe locally on Apple Silicon (private, no API cost)
4. Save raw transcript to `--transcript-dir`
5. Claude (Bedrock Sonnet) → generate relevance, source quality, summary, key claims from transcript
6. Write radar note to `--radar-dir`

## Execute

```bash
/opt/homebrew/Caskroom/miniconda/base/envs/unisa-phd-proposal/bin/python \
  /Users/johannes/code/personal/afrikaans-aac/scripts/transcribe-youtube.py $ARGUMENTS
```

After completion, read the created radar note and report:
1. The file path
2. The AI-generated summary
3. The relevance assessment
4. Any fields the user should review/fill in manually (organisation, tags, priority)

## Status vocabulary

The created note starts at `status: processed` (transcript exists, synthesis written).
Manually update to `integrated` once a bib entry is created and `cite_key` is set.

| Status | Meaning |
| --- | --- |
| `unread` | Identified, not yet watched |
| `skimmed` | Briefly scanned |
| `watched` | Fully watched, no notes yet |
| `processed` | Summary and synthesis written (default after this pipeline) |
| `integrated` | Cite key added; bib entry exists |
| `archived` | Reviewed, decided not relevant |

## Notes

- Audio is downloaded to a temp directory and deleted after transcription
- The transcript is the only large artefact kept on disk; the radar note references it
- For non-English videos add `--model mlx-community/whisper-large-v3-mlx` (multilingual)
- The Bedrock synthesis uses the same model ARN as the rest of the repo's pipeline
