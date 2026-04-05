# Specification: Afrikaans AAC Communication App for Dad

**Version:** 1.0
**Date:** 2026-04-03
**Author:** Johannes Foulds
**Status:** Draft — pending family input on D1, D3, D7

---

## Table of Contents

1. [Background and Purpose](#1-background-and-purpose)
2. [User Requirements](#2-user-requirements)
3. [Use Cases](#3-use-cases)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Functional Specification](#6-functional-specification)
7. [Technical Specification](#7-technical-specification)
8. [Phrase Bank](#8-phrase-bank)
9. [Out of Scope — v1](#9-out-of-scope--v1)
10. [Open Items](#10-open-items)
11. [Evidence Basis](#11-evidence-basis)

---

## 1. Background and Purpose

Dad suffered a stroke or brain blockage resulting in expressive aphasia — loss of the ability to speak. His comprehension is fully intact. He can read (confirmed: word search puzzles with a highlighter), and has limited but functional fine motor control sufficient for touch-screen interaction with large targets.

He lives at home with Mom (Francisca). No speech-language pathologist (SLP) assessment has been completed. The AWOW UTBook_15 Android 15 tablet is already set up and accessible remotely via SSH and scrcpy from Johannes's Mac.

**Purpose of this app:** Provide Dad with a reliable, dignified way to communicate essential needs, feelings, and preferences in Afrikaans — his primary language — using a pre-loaded phrase board on the tablet. The tablet speaks selected phrases aloud via pre-generated audio.

**Why custom-built:** No existing AAC app supports Afrikaans TTS with adequate quality. All reviewed commercial and open-source tools (TD Snap, SmallTalk Aphasia, Cboard, LetMeTalk) lack Afrikaans voice output. A custom PWA is the only viable path. See [notes/2026-04-03-tool-review.md](notes/2026-04-03-tool-review.md).

---

## 2. User Requirements

### 2.1 Primary user — Dad (person with aphasia)

| ID | Requirement |
|----|-------------|
| UR-01 | I can tap a button and have the tablet speak a phrase aloud in Afrikaans on my behalf. |
| UR-02 | I can navigate to any phrase in at most two taps from the home screen. |
| UR-03 | I can call for help or signal an emergency without any navigation — from wherever I am in the app. |
| UR-04 | All touch targets are large enough for me to tap accurately with my level of motor control. |
| UR-05 | The app works without an internet connection. |
| UR-06 | I can use the app independently without help from a caregiver for normal phrase selection. |
| UR-07 | I can communicate pain — general and body-specific — quickly and clearly. |
| UR-08 | I can express emotional states, not just physical needs. |
| UR-09 | I can explain my condition (aphasia) to visitors and strangers without caregiver assistance. |
| UR-10 | I can request conversation repair (slow down, repeat, write it down) during any interaction. |

### 2.2 Primary caregiver — Mom (Francisca)

| ID | Requirement |
|----|-------------|
| UR-11 | I can hear the tablet clearly when Dad taps a phrase. |
| UR-12 | I do not need technical skills to use the app day-to-day. |
| UR-13 | If Dad needs a phrase that is not in the app, I know what to do (write it down, tell Johannes). |
| UR-14 | The app is always on and accessible — I do not need to unlock, launch, or navigate to it before handing it to Dad. |

### 2.3 Remote maintainer — Johannes

| ID | Requirement |
|----|-------------|
| UR-15 | I can add or modify phrases remotely over SSH without rebuilding or redeploying an app. |
| UR-16 | Adding a phrase requires only editing a JSON file and running a script — no frontend code changes. |
| UR-17 | The audio for new phrases is generated automatically when the script runs. |
| UR-18 | The update is live on the tablet after a browser refresh — no APK installation or sideloading. |

---

## 3. Use Cases

### UC-01: Dad communicates a physical need

**Actor:** Dad
**Trigger:** Dad is hungry, thirsty, tired, cold, warm, or needs the toilet.
**Precondition:** Tablet is on, app is on home screen.

**Main flow:**
1. Dad picks up (or is handed) the tablet.
2. Dad taps the "Ek het iets nodig" category button.
3. Dad taps the relevant phrase button (e.g. "Ek is honger").
4. Tablet speaks: "Ek is honger."
5. Mom hears and responds.

**Alternative:** Dad uses the always-visible emergency bar to call Mom first, then navigates to needs.

---

### UC-02: Dad signals pain

**Actor:** Dad
**Trigger:** Dad is in pain.
**Precondition:** Tablet is accessible.

**Main flow:**
1. Dad taps "Pyn" category.
2. Dad taps the relevant body location (e.g. "My bors is seer").
3. Tablet speaks: "My bors is seer."
4. Mom uses IN–OUT–VERIFY to confirm and investigate severity.

**Alternative flow — pain character:**
2a. Dad taps "Meer oor die pyn" from the pain screen.
2b. Dad taps a pain character phrase (e.g. "Dit klop").
2c. Tablet speaks: "Die pyn klop."

---

### UC-03: Dad calls for Mom

**Actor:** Dad
**Trigger:** Dad needs Mom and she is not in the room.
**Precondition:** Tablet is accessible. This must work from any screen.

**Main flow:**
1. Dad taps the always-visible "Roep vir Francisca" button.
2. Tablet speaks: "Roep vir Francisca, asseblief."
3. Mom hears from another room and comes.

**Note:** This button is fixed on every screen. No navigation required.

---

### UC-04: Dad signals an emergency

**Actor:** Dad
**Trigger:** Dad needs urgent help — medical or safety.
**Precondition:** Tablet is accessible. This must work from any screen.

**Main flow:**
1. Dad taps the always-visible red "Noodgeval" button.
2. Tablet speaks: "Noodgeval! Kom asseblief!"
3. Mom responds immediately.

---

### UC-05: Dad explains his condition to a visitor

**Actor:** Dad, visitor
**Trigger:** A visitor (neighbour, doctor, friend) does not know about Dad's aphasia.
**Precondition:** Tablet is accessible.

**Main flow:**
1. Dad taps "Ek het 'n beroerte gehad" category.
2. Dad taps "Ek kan nie praat nie, maar ek verstaan alles."
3. Tablet speaks the phrase.
4. Visitor understands the situation.
5. Dad may continue with further context-setting phrases (e.g. "Wees asseblief geduldig met my").

---

### UC-06: Dad requests conversation repair

**Actor:** Dad
**Trigger:** Someone speaks too fast, Dad doesn't understand, or the communication has broken down.
**Precondition:** Tablet is accessible.

**Main flow:**
1. Dad taps "Praat met my" category.
2. Dad taps the relevant repair phrase (e.g. "Praat stadiger" or "Sê dit weer").
3. Tablet speaks the phrase.

---

### UC-07: Dad expresses a feeling or emotion

**Actor:** Dad
**Trigger:** Dad is experiencing an emotion he wants to communicate.
**Precondition:** Tablet is accessible.

**Main flow:**
1. Dad taps "Ek voel" category.
2. Dad taps the relevant emotion (e.g. "Ek is hartseer").
3. Tablet speaks the phrase.
4. Mom acknowledges and responds with empathy.

---

### UC-08: Dad requests an activity

**Actor:** Dad
**Trigger:** Dad wants to watch TV, listen to music, go outside, etc.
**Precondition:** Tablet is accessible.

**Main flow:**
1. Dad taps "Aktiwiteite" category.
2. Dad taps the activity (e.g. "Ek wil TV kyk").
3. Tablet speaks: "Ek wil TV kyk."
4. Mom or Johannes assists with the activity.

---

### UC-09: Johannes adds a new phrase remotely

**Actor:** Johannes (remote, Mac)
**Trigger:** Mom reports a phrase Dad needs but the app doesn't have.
**Precondition:** Tablet is on the home network. Johannes can SSH in.

**Main flow:**
1. Mom tells Johannes (via phone or WhatsApp) what phrase is needed.
2. Johannes SSHes into the tablet via Termux.
3. Johannes edits `phrases.json` to add the new phrase entry.
4. Johannes runs `generate_audio.py` — script calls edge-tts for the new phrase only and saves the MP3.
5. Johannes tells Mom to pull down to refresh in Chrome.
6. New phrase is immediately available.

---

### UC-10: Morning check-in routine

**Actor:** Dad, Mom
**Trigger:** Start of day.
**Precondition:** Tablet is on the bedside table or handed to Dad.

**Main flow:**
1. Mom asks: "Hoe voel jy vandag?"
2. Dad taps "Ek voel" category.
3. Dad taps a phrase expressing his current state.
4. Mom responds naturally to what the tablet says.
5. Mom asks "Het jy iets nodig?" — Dad uses Ek het iets nodig category if needed.

---

## 4. Functional Requirements

### 4.1 Phrase playback

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Tapping a phrase button plays the associated pre-generated audio file immediately. | Must |
| FR-02 | Audio plays through the tablet speaker at a volume audible across a room. | Must |
| FR-03 | Only one audio clip plays at a time; tapping a new phrase while audio is playing stops the current clip and plays the new one. | Must |
| FR-04 | If the audio file for a phrase is missing, the button is still visible but shows a silent indicator (no crash). | Should |

### 4.2 Navigation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-05 | The home screen displays a grid of category buttons. | Must |
| FR-06 | Tapping a category navigates to a phrase grid for that category. | Must |
| FR-07 | A "Terug" (back) button is always visible on phrase screens and returns to the home screen. | Must |
| FR-08 | A "Tuis" (home) button is always visible on all screens and returns to the home screen. | Must |
| FR-09 | Navigation depth from home screen to any phrase is exactly 2 taps (home → category → phrase). No 3-level hierarchies. | Must |
| FR-10 | Exception to FR-09: the pain character secondary screen is 3 taps deep (home → Pyn → phrase → Meer oor die pyn → character). This is acceptable because it is secondary and non-urgent. | Must |

### 4.3 Always-visible emergency controls

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-11 | A "Noodgeval" button is visible on every screen at all times, in a fixed position. | Must |
| FR-12 | A "Roep vir Francisca" button is visible on every screen at all times, in a fixed position. | Must |
| FR-13 | FR-11 and FR-12 are never obscured by other UI elements, overlays, or modal states. | Must |
| FR-14 | Tapping FR-11 plays the emergency audio immediately with no confirmation dialog. | Must |
| FR-15 | The Noodgeval audio file is volume-normalised to 0 dBFS peak (2.5× louder than default TTS output). This is applied automatically by `generate_audio.py` via ffmpeg post-processing whenever the file is regenerated. | Must |

### 4.4 Phrase management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-15 | All phrases are stored in a single `phrases.json` file. | Must |
| FR-16 | The app reads `phrases.json` at startup and renders the UI dynamically from its contents. | Must |
| FR-17 | Adding a phrase to `phrases.json` and placing the corresponding MP3 in `audio/` makes it available after a page refresh — no code changes required. | Must |
| FR-18 | A `generate_audio.py` script accepts phrases from `phrases.json` and generates MP3 files via edge-tts for any phrase that does not already have an audio file. | Must |

### 4.5 Offline operation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-19 | The app loads and operates fully without an internet connection. | Must |
| FR-20 | All audio files are served from `localhost` via the Termux HTTP server — no CDN or external audio calls. | Must |
| FR-21 | The app does not call any external API at runtime. | Must |

### 4.6 Display and accessibility

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-22 | All interactive buttons have a minimum touch target of 25mm × 25mm. | Must |
| FR-23 | Button labels use a minimum font size of 24pt. | Must |
| FR-24 | Category buttons are colour-coded (one colour per category, consistent across the app). | Should |
| FR-25 | All text has a contrast ratio of at least 4.5:1 against its background (WCAG AA). | Must |
| FR-26 | The display type is text-only (no symbol images required for v1). | Must |
| FR-27 | The layout is optimised for landscape orientation on a 10-inch tablet. | Must |

### 4.7 Kiosk / always-on behaviour

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-28 | The screen does not dim or turn off during use (Developer Options: Stay Awake, or PWA manifest keeps screen active). | Must |
| FR-29 | The app is pinned (Android app pinning) so Dad cannot accidentally leave the browser. | Should |
| FR-30 | The app launches automatically in Chrome when the tablet boots (or returns to the home screen). | Should |

---

## 5. Non-Functional Requirements

| ID | Requirement | Rationale |
|----|-------------|-----------|
| NFR-01 | **Latency:** Audio playback begins within 100ms of a button tap. | Delays feel broken; pre-generated MP3s served locally make this trivially achievable. |
| NFR-02 | **Reliability:** The app must not crash or enter an error state during normal use. | Dad may be alone; no recovery path if the app fails. |
| NFR-03 | **Zero dependencies at runtime:** No npm, no build step, no framework runtime, no CDN. The app is a single HTML file + JSON + MP3 files. | Eliminates deployment complexity; runs directly in Chrome without any server-side logic. |
| NFR-04 | **Maintainability:** A non-developer (Mom) can report what phrase is missing; a developer (Johannes) can add it in under 5 minutes over SSH. | Remote maintainability is a core constraint. |
| NFR-05 | **Portability:** The entire app (HTML + JSON + audio) can be copied to any Android device or served from any HTTP server without modification. | Future-proofing for device changes. |
| NFR-06 | **Audio quality:** The voice used must sound natural and clearly intelligible, not robotic. | Robotic TTS is a known barrier to adoption (Odendaal 2022). `af-ZA-WillemNeural` meets this threshold. |
| NFR-07 | **Security:** The HTTP server is bound to `localhost` only and is not accessible from outside the home network. | Tablets on home Wi-Fi; local-only is sufficient. |
| NFR-08 | **Volume:** Audio playback at system volume ≥ 70% must be audible 5 metres away in a quiet room. | Mom may not be in the same room. |
| NFR-09 | **Emergency volume:** The Noodgeval phrase must be perceptibly louder than all other phrases at the same system volume. Rationale: Dad may be alone; the emergency call must cut through background noise (TV, conversation) without requiring him to adjust volume first. Implementation: `noodgeval.mp3` is post-processed to 0 dBFS peak (2.5× gain via ffmpeg). The `"volume"` field in `phrases.json` makes this self-documenting and reproducible on every regeneration. |

---

## 6. Functional Specification

### 6.1 Screen structure

```
┌─────────────────────────────────────────────────────────┐
│  [Roep vir Francisca]              [NOODGEVAL]  ← always-visible bar
├─────────────────────────────────────────────────────────┤
│                                                         │
│   [Ja / Nee]      [Ek het iets nodig]    [Pyn]              │
│                                                         │
│   [Ek voel]       [Roep iemand]     [Praat met my]     │
│                                                         │
│   [Aktiwiteite]   [Beroerte-info]   [  (reserve)  ]    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

Home screen: 3×3 category grid. 8 categories in v1 (one reserve slot).

```
┌─────────────────────────────────────────────────────────┐
│  [Roep vir Francisca]              [NOODGEVAL]         │
├──────────────────────────────────────────────┬──────────┤
│                                              │          │
│   [Ek het pyn]     [My kop is seer]   [My bors]   [My maag] │
│                                              │          │
│   [My arm is seer] [My been is seer]  [My rug]    [My keel] │
│                                              │  [Terug] │
│   [Ek voel duiselig] [Meer oor die pyn]      │  [Tuis]  │
│                                              │          │
└──────────────────────────────────────────────┴──────────┘
```

Phrase screen: 3×3 or 3×4 grid of phrase buttons + fixed right-side navigation column (Terug / Tuis).

### 6.2 Always-visible bar

- Position: top of every screen, full width, fixed height (~60px / ~16mm).
- Left: "Roep vir Francisca" — blue/teal background, white text.
- Right: "NOODGEVAL" — red background, white text, bold.
- Both buttons are always active. They do not navigate — they play audio immediately.
- The bar is rendered outside the main content area so it cannot be scrolled out of view.

### 6.3 Category home screen

- Grid: 3 columns × 3 rows (9 slots, 8 used in v1).
- Each cell is a coloured button with a text label (Afrikaans).
- Tapping a category button navigates to that category's phrase screen.
- No audio plays on category button tap.
- Category colours (one per category, used consistently):

| Category | Colour |
|----------|--------|
| Ja / Nee | Green (`#2e7d32`) |
| Ek het iets nodig | Orange (`#e65100`) |
| Pyn | Red (`#c62828`) |
| Ek voel | Purple (`#6a1b9a`) |
| Roep iemand | Blue (`#1565c0`) |
| Praat met my | Teal (`#00695c`) |
| Aktiwiteite | Amber (`#f57f17`) |
| Beroerte-info | Grey (`#37474f`) |

### 6.4 Phrase screen

- Grid: 3 columns × 3 rows (maximum 9 phrases per screen, plus secondary screen if needed).
- Each cell is a button with the phrase label text.
- Tapping a phrase button plays the corresponding MP3 immediately.
- Navigation column (right edge, fixed): "Terug" (returns to home) and "Tuis" (returns to home — identical in v1 since there is no deeper nesting).
- Category colour is used as the header bar colour on the phrase screen for visual continuity.

### 6.5 Pain secondary screen

- Accessible from the "Pyn" phrase screen via a "Meer oor die pyn" button.
- Contains 7 pain-character phrases (klop, steek, druk, brand, prikkel, die heeltyd, kom en gaan).
- Navigation: "Terug" returns to the Pyn screen; "Tuis" returns to home.
- This is the only 3-level screen in the app.

### 6.6 Audio playback behaviour

- Each phrase has a corresponding MP3 file in the `audio/` directory.
- File naming: slugified phrase label, e.g. `ek_is_honger.mp3`.
- On tap: instantiate `new Audio(src)` and call `.play()`.
- If a clip is already playing: stop current clip (`.pause(); currentAudio.currentTime = 0`), play new clip.
- No visual "playing" indicator required in v1.
- Volume: controlled by Android system volume. No in-app volume control.

### 6.7 Data model (`phrases.json`)

```json
{
  "always_visible": [
    {
      "id": "noodgeval",
      "label": "NOODGEVAL",
      "phrase": "Noodgeval! Kom asseblief!",
      "audio": "audio/noodgeval.mp3"
    },
    {
      "id": "roep_franscisca",
      "label": "Roep vir Francisca",
      "phrase": "Roep vir Francisca, asseblief.",
      "audio": "audio/roep_franscisca.mp3"
    }
  ],
  "categories": [
    {
      "id": "ja_nee",
      "label": "Ja / Nee",
      "colour": "#2e7d32",
      "phrases": [
        {
          "id": "ja",
          "label": "Ja",
          "phrase": "Ja.",
          "audio": "audio/ja.mp3"
        }
      ]
    }
  ]
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique slug; also used as the MP3 filename stem |
| `label` | string | Text displayed on the button |
| `phrase` | string | Text spoken by TTS (may differ from label for naturalness) |
| `audio` | string | Relative path to MP3 file from app root |

### 6.8 Phrase addition workflow

1. Mom notices a phrase is missing; tells Johannes via phone/WhatsApp.
2. Johannes SSHes to tablet: `ssh user@<tablet-ip>`.
3. Johannes opens `phrases.json` and adds the new entry under the appropriate category (or creates a new category if needed).
4. Johannes runs: `python3 generate_audio.py --new-only`
   - Script reads `phrases.json`, finds entries where the audio file does not exist, generates MP3 via edge-tts.
5. Johannes tells Mom: "Trek af op Chrome om te herlaai."
6. Phrase is live.

### 6.9 Kiosk setup (Android)

1. **Screen always-on:** Developer Options → Stay Awake (while charging). Tablet is kept on charge.
2. **App pinning:** Settings → Security → App Pinning (Screen Pinning on older Android). Pin Chrome to prevent accidental exit.
3. **PWA manifest:** `display: fullscreen`, `orientation: landscape`, `start_url: /` — allows adding to home screen as a pseudo-app.
4. **Auto-launch:** Add Chrome shortcut to home screen with the localhost URL as the target.

---

## 7. Technical Specification

### 7.1 System architecture

```
┌──────────────────────────────────────────────────────┐
│  Android Tablet (AWOW UTBook_15, Android 15)         │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  Termux (background, boot-persistent)         │   │
│  │  python3 -m http.server 8080                  │   │
│  │  Serves: /data/data/com.termux/files/home/aac/│   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  Chrome (fullscreen, pinned)                  │   │
│  │  http://localhost:8080/index.html             │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
         ▲ SSH (maintenance only)
         │
┌────────────────────┐
│  Mac (Johannes)    │
│  ssh user@tablet   │
│  edit phrases.json │
│  run generate_audio│
└────────────────────┘
```

### 7.2 File structure

```
aac/
├── index.html              # Single-page app — all HTML, CSS, and JS inline
├── phrases.json            # Phrase bank and audio manifest
├── manifest.json           # PWA manifest (display: fullscreen, orientation: landscape)
├── audio/
│   ├── noodgeval.mp3
│   ├── roep_franscisca.mp3
│   ├── ja.mp3
│   └── ...                 # one MP3 per phrase
└── generate_audio.py       # Audio generation script (runs on Mac or tablet)
```

### 7.3 `index.html` — implementation notes

**Technology:** Vanilla HTML5, CSS3, JavaScript (ES2020). No framework. No build step. No npm.

**Structure:**
```
index.html
├── <head>
│   ├── PWA meta tags (viewport, theme-color, apple-mobile-web-app-capable)
│   └── <style> — all CSS inline
└── <body>
    ├── #always-bar        — fixed-position always-visible strip
    │   ├── #btn-franscisca
    │   └── #btn-noodgeval
    ├── #home-screen       — category grid (shown by default)
    └── #phrase-screen     — phrase grid (hidden by default, shown on category tap)
        ├── #phrase-header — category name + colour bar
        ├── #phrase-grid   — phrase buttons
        └── #nav-col       — Terug / Tuis buttons
    └── <script>           — all JS inline
```

**State management:** Minimal. One variable tracks the current screen (`'home'` or `'phrase'`). Navigation is `show/hide` on two `<div>` elements.

**JS responsibilities:**
1. Fetch and parse `phrases.json` at startup.
2. Render category grid from `categories[]`.
3. On category tap: populate phrase grid with that category's phrases, show phrase screen.
4. On phrase tap: play audio (stop any current audio first).
5. On always-bar tap: play audio (same mechanism).
6. On Terug/Tuis tap: show home screen.

**No service worker in v1.** Offline is achieved by serving locally from Termux — no caching layer needed.

### 7.4 CSS — layout specification

**Viewport:** `<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">`

**Always-bar:**
```css
#always-bar {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 64px;
  display: flex;
  z-index: 1000;
}
#btn-franscisca { flex: 1; background: #1565c0; color: white; font-size: 20px; }
#btn-noodgeval  { flex: 0 0 160px; background: #c62828; color: white; font-size: 20px; font-weight: bold; }
```

**Grid (category and phrase screens):**
```css
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 8px;
  /* fills remaining viewport height after always-bar */
  height: calc(100vh - 64px);
  margin-top: 64px;
}
.btn {
  border: none;
  border-radius: 8px;
  font-size: 24px;
  color: white;
  cursor: pointer;
  /* minimum 25mm on a 96dpi screen ≈ 94px; on a 10" tablet ~150dpi → 148px */
  min-height: 94px;
}
```

**Phrase screen layout:**
```css
#phrase-screen {
  display: grid;
  grid-template-columns: 1fr 80px;  /* phrase grid | nav column */
  margin-top: 64px;
  height: calc(100vh - 64px);
}
#nav-col {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
}
#nav-col .btn { flex: 1; background: #455a64; }
```

### 7.5 `generate_audio.py` — specification

**Purpose:** Read `phrases.json` and generate one MP3 per phrase using Microsoft Edge TTS.

**Voice:** `af-ZA-WillemNeural`

**Dependencies:** `edge-tts` (Python package, available in `brainstorm-dev` conda env).

**Interface:**
```
python3 generate_audio.py [--all] [--new-only]

  --all        Regenerate all audio files (overwrites existing)
  --new-only   Generate only phrases missing an audio file (default)
```

**Algorithm:**
```python
1. Load phrases.json
2. Collect all phrase entries from always_visible[] and categories[].phrases[]
   (including secondary screens); deduplicate on audio path
3. For each phrase entry:
   a. Determine output path from entry["audio"]
   b. If --new-only and file exists: skip
   c. Apply TTS_SUBSTITUTIONS to entry["phrase"] (e.g. TV → Televisie)
   d. Call edge-tts: communicate(text=normalised_phrase, voice="af-ZA-WillemNeural",
                                   write_media=output_path)
   e. If entry has "volume" field: re-encode MP3 in-place via ffmpeg
      (e.g. noodgeval: volume=2.5, peaks at 0 dBFS)
4. Print summary: N generated, M skipped
```

**Error handling:**
- If `edge-tts` network call fails (internet required for generation): print error for that phrase and continue. Missing audio handled gracefully by FR-04.

**Note:** `edge-tts` requires internet access to generate audio. This is acceptable because generation happens at maintenance time (on Mac or with Wi-Fi). Runtime playback is fully offline.

### 7.6 Termux HTTP server setup

```bash
# In Termux on the tablet
pkg install python
python3 -m http.server 8080 --directory ~/aac
# To persist across reboots: add to ~/.bashrc or use Termux:Boot
```

**Termux:Boot auto-start script (`~/.termux/boot/start-server.sh`):**
```bash
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/aac
python3 -m http.server 8080 &
```

### 7.7 SSH access (maintenance)

```bash
# From Mac
ssh u0_a<N>@<tablet-local-ip> -p 8022  # Termux SSH port
```

Termux SSH is already configured as part of the parent Android topic setup. See [../../../notes/](../notes/) for SSH setup details.

### 7.8 PWA manifest (`manifest.json`)

```json
{
  "name": "Pa se App",
  "short_name": "Pa se App",
  "start_url": "/",
  "display": "fullscreen",
  "orientation": "landscape",
  "background_color": "#212121",
  "theme_color": "#212121",
  "icons": []
}
```

### 7.9 Audio file naming convention

Audio file names are derived from the phrase `id` field in `phrases.json`:

- `id` is a lowercase alphanumeric slug with underscores, e.g. `ek_is_honger`
- Audio path: `audio/<id>.mp3`
- The `generate_audio.py` script derives the output path from the `audio` field in `phrases.json` — no inference from id.

### 7.10 Technology decisions and rationale

| Decision | Choice | Rationale |
|----------|--------|-----------|
| App type | Static PWA (single HTML file) | Zero build tooling; runs in Chrome on Android; updated by file edit + refresh |
| Language | Vanilla JS / HTML / CSS | No framework runtime to manage; no npm; no version drift |
| TTS | Pre-generated MP3 (edge-tts, af-ZA-WillemNeural) | Offline playback; natural voice; no runtime API calls; generated once |
| Local server | Termux `python3 -m http.server` | Zero dependencies beyond Python; already installed in parent topic |
| State management | None (DOM show/hide) | Two-screen app; no state complexity; Redux/Zustand would be overengineering |
| Audio API | HTML5 `Audio` object | Native browser; no library; pre-buffered at instantiation |
| Storage | No local storage | All state is in `phrases.json`; no user data to persist |
| Build pipeline | None | No minification, bundling, or transpilation required |

---

## 8. Phrase Bank

Full phrase bank: [notes/2026-04-03-phrase-bank.md](notes/2026-04-03-phrase-bank.md)

**Summary:**

| Category | Phrases | Priority |
|----------|---------|----------|
| Always-visible bar | 2 | Critical |
| Ja / Nee | 9 | Tier 1 |
| Ek het iets nodig | 9 | Tier 1 |
| Pyn | 10 + 7 secondary | Tier 1 |
| Ek voel | 9 | Tier 2 |
| Roep iemand | 9 | Tier 1 |
| Praat met my | 9 | Tier 2 |
| Aktiwiteite | 9 | Tier 3 |
| Ek het 'n beroerte gehad | 8 | Tier 3 |
| **Total** | **73 + 7** | |

---

## 9. Out of Scope — v1

The following are explicitly deferred to v2 or later:

| Item | Reason for deferral |
|------|---------------------|
| Symbol / picture buttons | Dad has intact reading; text-only is simpler and equally effective |
| Visual Scene Displays (VSDs) | Higher build effort; not needed for core home use |
| Custom family photos | Add in v2 after v1 is validated |
| Grandchildren names (Elaine's children) | Family decision; add when ready |
| Keyboard / free text input | Too slow; frustrating for aphasia user |
| Word prediction | Not needed for a pre-loaded phrase board |
| User accounts / login | Single-user, local-only device |
| Cloud sync | Offline-first design; no need |
| SLP integration / usage logging | Out of scope for personal family tool |
| Android TTS runtime | No quality Afrikaans offline TTS exists |
| Switch / scanner access | Not needed for current motor level; revisit if motor control deteriorates |
| Multiple communication partner profiles | Single household; not needed in v1 |

---

## 10. Open Items

These require family input or empirical device testing before v1 is declared complete.

| ID | Item | Who | How |
|----|------|-----|-----|
| D1 | Confirm highest-priority fringe phrases with Mom | Mom | Phone call / WhatsApp |
| D2 | Pictures + words, or words only? | Family | Confirm after first session |
| D3 | Grandchildren names (Elaine's children) | Elaine | Add when family ready — v2 |
| D4 | Verify PWA offline audio on Android | Johannes | Serve via Termux, go offline, tap phrases |
| D5 | Verify screen always-on / kiosk mode | Johannes | Test Developer Options + app pinning |
| D6 | Verify Termux HTTP server serves to Chrome | Johannes | `python3 -m http.server 8080`, open `localhost:8080` |
| D7 | Tablet positioning — hold, rest, or mount? | Mom | Ask at first session |

---

## 11. Evidence Basis

All design decisions in this specification are grounded in one or more of the following sources:

| Decision | Source(s) |
|----------|-----------|
| Min button size 25–30mm | Chen et al. (2013), Barros et al. (2014) |
| 9 buttons per screen (3×3) | Light et al. (2019); clinical consensus |
| Max 2-tap navigation depth | Clinical consensus (Lingraphica, Tobii Dynavox aphasia literature) |
| Always-visible emergency button | Clinical standard (ASHA AAC clinical practice guidelines) |
| Text-only display | Hux et al. (2001); intact reading comprehension confirmed |
| Font size ≥ 24pt | Elderly user guidelines; Light et al. (2019) |
| Category colour coding | Light et al. (2019) — reduces visual search time |
| Pre-generated audio over runtime TTS | NFR: offline reliability; quality: WillemNeural assessed by Johannes |
| TTS voice: af-ZA-WillemNeural | Only high-quality Afrikaans neural TTS available; assessed by Johannes |
| Communication partner training (caregiver guide) | Odendaal & Tönsing (2024); Aphasia Institute SCA™ framework |
| Context-setting phrases ("Ek het 'n beroerte") | Clinical consensus; Odendaal (2024) p.70 |
| Phrase bank category structure | Lingraphica SmallTalk 8-category structure; SASLHA Afrikaans Medical Board |
| Pain character secondary screen | SASLHA Afrikaans Medical Context Board (Bornman & Koekemoer, 2025) |
| Personalised vocabulary | Odendaal (2024): "generic systems do not work" — all 10 SA SLTs agreed |

Full references: [notes/2026-04-03-literature-review.md](notes/2026-04-03-literature-review.md) and [resources.md](resources.md).
