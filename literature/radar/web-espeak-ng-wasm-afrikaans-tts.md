---
# IDENTITY
title: "eSpeak NG — open-source formant TTS with Afrikaans voice, compiled to WebAssembly"
type: web-article
url: "https://github.com/espeak-ng/espeak-ng"
cite_key: ""

# PROVENANCE
author: "Reece H. Dunn (maintainer); Jonathan Duddington (original eSpeak)"
organisation: "Open-source community / GitHub espeak-ng org"
site_name: "GitHub + F-Droid + npm"
date_published: "2015-12"
date_accessed: "2026-07-25"
duration: ""
platform: ""

# WORKFLOW
date_added: "2026-07-25"
status: processed
tags: [tts, espeak, wasm, afrikaans, offline, formant-synthesis, android, pwa, aac, low-resource]
priority: high

# TRIAGE
relevance: "eSpeak NG is the only production-quality offline TTS engine with a named Afrikaans voice ('af') that runs both as an Android system TTS engine (F-Droid APK) and as a WASM/JS module in the browser — making it the only viable Tier-2 fallback for the AAC PWA when Edge TTS is unavailable."
transcript_path: ""
---

# eSpeak NG — open-source formant TTS with Afrikaans voice, compiled to WebAssembly

## Why on radar

The AAC PWA architecture (documented in `notes/brainstorm/2026-07-25-the-boys/2026-07-25-the-boys.md`) uses Edge TTS (`af-ZA-WillemNeural`) as the primary speech path and requires an offline fallback for novel utterances when the device has no network access. eSpeak NG is the only free, open-source, fully offline TTS engine that:

1. Includes a named Afrikaans voice (`af`, voice variant `af+f2` for female presentation) built into the data bundle.
2. Runs as an Android TTS system engine via an F-Droid APK (`com.reecedunn.espeak`, v1.52.0, Dec 2024), satisfying the Web Speech API's `getVoices()` call from the PWA's WebView.
3. Runs directly in the browser as a WebAssembly module (`espeakng.js`, multiple npm packages), eliminating the Android TTS engine dependency for the pure-PWA path.

This source covers three deployable artefacts that are directly relevant to the tiered TTS dispatcher design: the Android system engine, the WASM browser module, and the npm package. The design decision of whether to include eSpeak NG as Tier 2 (robotic but intelligible offline fallback) is documented in the brainstorm session.

## Source quality

Primary source: the official eSpeak NG GitHub repository (`espeak-ng/espeak-ng`), maintained by a community of open-source contributors since 2015. Secondary sources: Wikipedia article on eSpeak (cites academic papers for several language implementations); F-Droid package page (reproducibly built and signed); npm package `espeak-ng` (WASM build, compiled via Emscripten); `steveseguin.github.io/espeakng.js` (browser wrapper). All sources are grey/open-source technical documentation, not peer-reviewed. The core formant synthesis method is grounded in established acoustic phonetics (Klatt 1979, cited in the Wikipedia article). The Afrikaans voice inclusion is documented in the Wikipedia language list, footnote citing Butgereit & Botha (2009).

## Summary

eSpeak NG is a compact, open-source formant speech synthesizer originally written for RISC OS in 1995, rewritten as eSpeak in 2007, and forked to eSpeak NG in December 2015 under active community maintenance. It uses additive formant synthesis for voiced sounds (vowels, sonorants) and recorded noise for unvoiced consonants (e.g. /s/), plus an optional Klatt synthesizer path. The C codebase compiles to <10 MB including all 100+ language voice data files. The most recent stable release is 1.52.0 (December 2024). The Afrikaans voice (`af`) is an included, production voice; voice variant `af+f2` applies female formant and pitch adjustments. An Emscripten-compiled WASM/JS port exists in multiple npm packages (`espeak-ng` v1.0.2; `steveseguin/espeakng.js`), enabling fully client-side synthesis in any browser supporting Web Workers and the Web Audio API. The Android F-Droid APK (`com.reecedunn.espeak`, 9 MiB, requires Android 5.0+, no permissions required) registers as a system TTS engine.

## Key claims

- **Afrikaans voice is included**: `af` is listed as a production voice in the eSpeak NG language list (Wikipedia, footnote 25 cites Butgereit & Botha 2009 as the implementation source); `af+f2` variant adjusts to a female voice via formant/pitch parameters.
- **Formant synthesis quality ceiling**: eSpeak NG's formant synthesis is "clear, and can be used at high speeds, but is not as natural or smooth as larger synthesizers which are based on human speech recordings" (README). For AAC, intelligibility (not naturalness) is the relevant criterion; the Tier-2 fallback role explicitly accepts this quality ceiling.
- **Word-level citation-form prosody**: when synthesising individual words (the per-word dispatch architecture), eSpeak NG and neural TTS produce acoustically similar outputs — both render each word in citation form. The prosody difference between the two engines is therefore irrelevant in the per-word-commit architecture described in the brainstorm.
- **Android deployment path**: install `com.reecedunn.espeak` from F-Droid → Android Settings → Accessibility → TTS output → set as Preferred engine. The PWA's `speechSynthesis.getVoices()` then returns an `af` voice. Provisioning time: ~5 minutes.
- **WASM/browser deployment path — use `steveseguin/espeakng.js` only**: three packages exist but only one is suitable for audio in the browser:
  - ✅ `steveseguin/espeakng.js` — **the correct package**. Web Worker + Web Audio API; outputs raw PCM samples for immediate playback. Total 3.3 MB (worker JS 760 KB + voice `.data` 2.5 MB, all languages). GPLv3. Hosted on jsDelivr CDN.
  - ❌ `espeak-ng` npm (ianmarmour, v1.0.2) — **not suitable for audio**. This is an Emscripten CLI port: it writes phoneme/IPA output to an in-memory filesystem (`espeak.FS.readFile("generated")`). No audio output API. 18.5 MB unpacked. Useful only for grapheme-to-phoneme (G2P) pipelines, not TTS playback.
  - ❌ `wide-video/espeakng-wasm` — **phonemizer only, no audio**. Built as `piper-wasm` for use with the Kokoro neural TTS pipeline; produces phoneme strings, not speech. Not a TTS fallback.
- **Android system requirements**: v1.52.0 requires Android 5.0+. v1.51.1 (2022) supports Android 4.0+. No permissions required (cannot write to shared storage).
- **Bundle size**: ~9 MiB for the Android APK (all languages). The `steveseguin/espeakng.js` WASM path is 3.3 MB cached by the service worker. The `.data` voice file must be added explicitly to the SW precache manifest (Workbox `additionalManifestEntries`) or it will not be available offline.
- **License**: GPL v3. Any PWA or application that links against `libespeak-ng` inherits the GPL; the WASM binary in a browser context is distributable under GPLv3 as long as source is available (a link to the GitHub repo in the app suffices for most interpretations).
- **NVDA and Android include eSpeak NG as default**: it is the default TTS engine in NVDA (Windows screen reader) and is bundled with some Android distributions, indicating it is considered production-grade for accessibility tooling.
- **History**: originally developed by Reece Dunn from a GitHub fork of eSpeak (Jonathan Duddington, last active 2015); eSpeak NG diverged significantly from October 2015; first release 1.49.0 September 2016. Wikipedia citation 25 attributes the Afrikaans and Swahili voices to Butgereit & Botha (2009, IST-Africa conference).

## Connections to research

- Directly relevant to the Tier-2 TTS fallback decision documented in `notes/brainstorm/2026-07-25-the-boys/2026-07-25-the-boys.md`.
- The per-word-dispatch TTS architecture (brainstorm) makes the prosody quality difference between eSpeak NG and Edge TTS irrelevant — both produce citation-form word audio; the only differentiator is timbre (voice quality).
- The Android provisioning path (F-Droid APK) is the documented Phase 1B deployment step.
- The WASM path is relevant if the app moves to a fully browser-based architecture without dependence on the Android system TTS service.
- See also: `web-presage-predictive-text-aac.md` — the predictive text layer that pairs with this TTS layer.
- Butgereit & Botha (2009) cited by Wikipedia as the Afrikaans voice implementation source — potential paper to add to the formal pipeline if language/voice quality claims need academic backing.

## Transcript / Notes

### Key URLs

| Artefact | URL |
| --- | --- |
| Main GitHub repo | https://github.com/espeak-ng/espeak-ng |
| F-Droid APK (`com.reecedunn.espeak`) | https://f-droid.org/packages/com.reecedunn.espeak/ |
| npm `espeak-ng` (Emscripten/WASM) | https://www.npmjs.com/package/espeak-ng |
| `steveseguin/espeakng.js` (**audio** WASM — use this) | <https://steveseguin.github.io/espeakng.js/> |
| `espeak-ng` npm / ianmarmour (CLI/G2P only — no audio) | <https://www.npmjs.com/package/espeak-ng> |
| `wide-video/espeakng-wasm` (phonemizer only — no audio) | <https://github.com/wide-video/espeakng-wasm> |
| Wikipedia article | https://en.wikipedia.org/wiki/ESpeak |

### Afrikaans voice invocation (Web Speech API)

```javascript
// After setting Android TTS preferred engine to eSpeak NG:
const voices = speechSynthesis.getVoices();
const afVoice = voices.find(v => v.lang.startsWith('af'));
const utt = new SpeechSynthesisUtterance(text);
utt.voice = afVoice;
speechSynthesis.speak(utt);
```

### WASM API (espeakng.js SimpleTTS)

```javascript
const tts = new SimpleTTS();
tts.onReady(() => {
  tts.speak('Goeie môre', {
    voice: 'af',   // Afrikaans
    rate: 200,     // wpm; range 80–450
    pitch: 75,     // 0–100
    volume: 1.2    // 0–2.0
  }, (audioData, sampleRate) => {
    SimpleTTS.playAudioData(audioData, sampleRate);
  });
});
```

Files needed: `espeakng-simple.js`, `espeakng.worker.js`, `espeakng.worker.data`.

### Voice variant for Afrikaans female

From Wikipedia: `"af" is the Afrikaans voice. "af+f2" is the Afrikaans voice modified with the "f2" voice variant which changes the formants and the pitch range to give a female sound.`

### F-Droid APK version history

| Version | Added | Min Android | Size |
| --- | --- | --- | --- |
| 1.52.0 (current) | 2024-12-17 | Android 5.0 | 9 MiB |
| 1.51.1 | 2022-06-30 | Android 4.0 | 5.8 MiB |
| 1.51-dev | 2021-04-09 | Android 4.0 | 5.3 MiB |

No permissions required in any version. Reproducibly built and signed by F-Droid.
