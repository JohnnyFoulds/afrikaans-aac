# 2026-04-02 — Initial brainstorm

## Situation

Dad had a stroke or brain blockage (specifics unclear). He has lost the ability to speak. Comprehension is intact. He is mobile and can control his limbs and hands at an elderly-man level of fine motor control — he can do word search puzzles with a highlighter, so touch-screen interaction with large targets is viable.

He lives at home with Mom. No speech-language pathologist (SLP) assessment yet.

The goal is a custom AAC (Augmentative and Alternative Communication) solution running on the AWOW UTBook_15 Android tablet already set up in this topic.

## What we know so far

- Touch screen viable — large targets required
- TTS output — tablet must speak selected phrases aloud
- Offline — home use, no dependency on internet
- No typing as primary input — too slow and frustrating given motor limitations
- Fast path to most common phrases is critical — navigation depth must be minimal
- Custom solution preferred over off-the-shelf (full control over vocabulary and layout)

## Key unknowns to resolve next

- What language(s)? Afrikaans, English, or both?
- What are the highest-priority phrases? (yes/no, pain, needs, family names, greetings)
- Can he handle two-tap navigation (category → phrase) or does everything need to be one tap?
- Pictures + words, or words only?
- Web app (easy remote updates via SSH) vs native Android app?
- Who maintains the phrase library going forward?

## Initial architecture sketch

```
Tablet screen
└── Category grid (6–9 large buttons)
    ├── Yes / No / Maybe
    ├── I need...
    ├── I feel...
    ├── Family
    ├── Food & drink
    └── [more...]
        └── Phrase grid (large buttons)
            └── Tap → TTS speaks phrase aloud
```

Two-level hierarchy keeps navigation shallow. A "back" button and a "home" button are always visible.

## Next steps

1. Decide: web app (PWA) vs native Android app
2. Gather phrase list from Mom — what does Dad try to communicate most?
3. Decide on language(s)
4. Prototype a minimal phrase board and test with Dad
