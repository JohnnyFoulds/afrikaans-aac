# transcribe-audio

Transcribe an audio file to plain text using local MLX Whisper (runs entirely on-device, no API calls).

**Usage:** `/transcribe-audio <input.mp3> [options]`

**Options:**

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--output` | file path | input basename with `.txt` | Output transcript path |
| `--model` | any MLX Whisper model id | `mlx-community/whisper-large-v3-turbo` | Whisper model to use |
| `--language` | language code e.g. `en` | auto-detect | Force transcription language |
| `--task` | `transcribe` `translate` | `transcribe` | Whisper task mode |

**Examples:**

```
# Transcribe an MP3 to a .txt file alongside it
/transcribe-audio literature/mp3/pass1/lewis-2020-rag.mp3

# Specify output path
/transcribe-audio literature/mp3/pass1/lewis-2020-rag.mp3 --output literature/transcripts/lewis-2020-rag-pass1.txt

# Force English, use a larger model
/transcribe-audio literature/mp3/pass1/lewis-2020-rag.mp3 --language en --model mlx-community/whisper-large-v3-turbo
```

---

## Prerequisites

- `unisa-phd-proposal` conda environment with `mlx-whisper` installed

---

## Execute

Parse `$ARGUMENTS` as follows:
- The first positional argument (before any `--` flag) is the input audio path.
- All remaining `--key value` pairs are passed through as-is.

Run this command using the Bash tool, substituting the actual paths and options:

```bash
conda run -n unisa-phd-proposal python /Users/johannes/code/unisa/unisa-phd-proposal/scripts/transcribe_audio_mlx.py --input-audio <input_audio_path> [--output <path>] [--model <model>] [--language <lang>] [--task <task>]
```

Then read the output `.txt` file and display its contents to the user.
