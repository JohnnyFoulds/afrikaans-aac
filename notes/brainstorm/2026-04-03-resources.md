# AAC Resources — Reference Links and Design Principles

**Date:** 2026-04-03
**Origin:** Migrated from brainstorm/topics/android/subtopics/aac/resources.md
**Note:** The paper/source listing from the original file is now in `literature/references.bib` and `literature/README.md`. This note preserves the reference links, TTS notes, and design principles.

---

## Off-the-shelf AAC apps (reference / prior art)

- **Cboard** — open source, web-based AAC, free. [cboard.io](https://www.cboard.io)
- **Grid Player** — free, symbol-based, Windows/iOS/Android
- **Proloquo2Go** — gold standard, expensive, iOS only
- **Snap Core First** — commercial, cross-platform
- **LetMeTalk** — free, Android, open source
- **SmallTalk Aphasia** (Lingraphica) — dedicated aphasia app; 8-category structure informed our design

Full evaluation of each tool is in [2026-04-03-tool-review.md](2026-04-03-tool-review.md). Verdict: none support Afrikaans TTS; custom PWA is the only viable path.

---

## TTS

- **Microsoft Edge TTS** — `af-ZA-WillemNeural` (male), `af-ZA-AdriNeural` (female). Free, no API key. Confirmed good Afrikaans quality.
- Python: `edge-tts` package (in `afrikaans-aac` conda env)
- eSpeak NG — has Afrikaans but poor quality; not used

---

## Afrikaans AAC research

- **University of Pretoria CAAC** — oldest AAC research centre in SA (est. 1990). Resources: up.ac.za/centre-for-augmentative-alternative-communication
- **SASLHA communication boards** — free download: saslha.co.za/communication-boards
- **Tobii Dynavox Afrikaans symbol set** (Bornman & Visser, 2025) — culturally adapted; within Tobii commercial platform, not yet public

---

## AAC design principles (quick reference)

These informed the v1 design decisions. Full sourcing in [2026-04-03-literature-review.md](2026-04-03-literature-review.md).

- Core vocabulary: ~200 words = 80% of all speech (Beukelman & Mirenda 2013)
- Button size: ≥20mm for motor-impaired; 25–30mm optimal (Chen et al. 2013)
- Grid density: 9 items/screen for moderate impairment (clinical consensus)
- Max navigation depth: 2 taps (clinical consensus)
- Unity principle: one symbol = one location, never moves
- Emergency: always visible, never behind a category
