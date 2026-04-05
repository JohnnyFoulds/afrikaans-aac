# Afrikaans AAC for Post-Stroke Aphasia

A custom Augmentative and Alternative Communication (AAC) tool built for a specific user: an Afrikaans-speaking man who lost his speech following a stroke. Comprehension is intact; he can read and use a touchscreen with large targets.

No commercial AAC app supports Afrikaans with sufficient TTS quality for a real user. This is a Progressive Web App (PWA) with pre-generated audio (Microsoft Edge TTS, `af-ZA-WillemNeural`) that runs fully offline on an Android tablet. It requires no app store, no account, and no internet connection. Phrases are maintained remotely over SSH by a family member.

The app is deployed and in active daily use. **v1 deployed 2026-04-03.**

---

## The user

| Property | Detail |
| --- | --- |
| Condition | Post-stroke expressive aphasia — no speech output; comprehension intact |
| Reading | Yes (word search puzzles) |
| Motor | Limited but functional fine motor; large touch targets required |
| Device | AWOW UTBook\_15, Android 15, 10-inch tablet |
| Setting | Home care; primary caregiver is spouse (Mom) |
| Language | Afrikaans |

---

## App architecture

```text
PWA (static HTML/JS/CSS — no framework, no build step)
├── src/
│   ├── index.html         — single-file app (category grid → phrase grid)
│   ├── phrases.json       — phrase bank (8 categories, 78 pre-generated phrases)
│   ├── manifest.json      — PWA manifest ("Pa se App", fullscreen, landscape)
│   ├── generate_audio.py  — Edge TTS audio generation script
│   └── audio/             — pre-generated MP3s (af-ZA-WillemNeural)
│
Deployment: Termux HTTP server (port 8080) on tablet → Chrome/Fully Kiosk Browser
Maintenance: SSH from Mac → edit phrases.json + run generate_audio.py → rsync
```

Always-visible bar: blue "Roep vir Francisca" + red "NOODGEVAL" (boosted volume).
Navigation: home (3×3 category grid) → phrase screen (3×4 grid + nav column). Max 2 taps to any phrase.

### Regenerate audio

```bash
conda activate afrikaans-aac
cd src
python3 generate_audio.py --all       # generate all missing MP3s
python3 generate_audio.py --dry-run   # preview what would be generated
```

### Sync to tablet

```bash
/sync-android   # rsync src/ to tablet over SSH
```

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
src/                      — PWA application source (index.html, phrases.json, audio/)
scripts/                  — research pipeline scripts (PDF conversion, writing pipeline, etc.)
literature/
  papers/                 — PDFs named <cite-key>.pdf
  mkv/                    — full-text Markdown conversions named <cite-key>.md
  img/                    — images extracted during OCR
  radar/                  — sources identified but not yet in formal pipeline
  references.bib          — BibTeX source of truth
proposal/
  research/               — PhD research proposal sections (guarded: citation rules apply)
  business/               — business case / stakeholder documents (guarded)
admin/
  outreach/               — outreach emails (guarded: citation rules apply)
docs/
  specifications/         — app specification and technical documentation
  standards/              — coding, logging, and research process standards
notes/
  brainstorm/             — origin notes from the initial build (2026-04-02/03)
  usage-log.md            — Phase 0 usage data collection
  participant-profile-dad.md — Participant 1 functional profile
  consent-record.md       — Phase 0 consent record
```

Key documents:
- [CLAUDE.md](CLAUDE.md) — AI assistant instructions, citation integrity rules, literature pipeline
- [docs/specifications/app-spec.md](docs/specifications/app-spec.md) — full PWA specification
- [literature/README.md](literature/README.md) — literature pipeline and current state
- [notes/brainstorm/2026-04-03-research-angle.md](notes/brainstorm/2026-04-03-research-angle.md) — PhD framing and gap analysis
- [notes/brainstorm/2026-04-03-data-collection-plan.md](notes/brainstorm/2026-04-03-data-collection-plan.md) — Phase 0 data collection plan
