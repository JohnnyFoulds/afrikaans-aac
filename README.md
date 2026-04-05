# Afrikaans AAC for Post-Stroke Aphasia

A custom Augmentative and Alternative Communication (AAC) tool built for a specific user: an Afrikaans-speaking man who lost his speech following a stroke. Comprehension is intact; he can read and use a touchscreen with large targets.

No commercial AAC app supports Afrikaans with sufficient TTS quality for a real user. This is a Progressive Web App (PWA) with pre-generated audio (Microsoft Edge TTS, `af-ZA-WillemNeural`) that runs fully offline on an Android tablet. It requires no app store, no account, and no internet connection. Phrases are maintained remotely over SSH by a family member.

The app is deployed and in active daily use.

---

## Quick start

```bash
# Create and activate the conda environment
make setup
conda activate afrikaans-aac

# Run tests
make test

# Lint and format
make lint
make format
```

---

## Repository layout

```text
src/           — PWA application source
scripts/       — research pipeline scripts (PDF conversion, writing pipeline, etc.)
literature/    — papers, Markdown conversions, radar notes, BibTeX references
proposal/
  research/    — PhD research proposal sections (guarded: citation rules apply)
  business/    — business case / stakeholder documents (guarded)
admin/
  outreach/    — outreach emails (guarded: citation rules apply)
docs/
  standards/   — coding, logging, and research process standards
notes/         — working notes and research scratchpad
```

See [CLAUDE.md](CLAUDE.md) for AI assistant instructions, citation integrity rules, and the full literature pipeline workflow.
