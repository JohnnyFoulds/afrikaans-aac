# AAC Tool Review — Commercial and Open-Source Options

**Date:** 2026-04-03
**Purpose:** Evaluate existing AAC tools for suitability as a solution for Dad — post-stroke aphasia, Afrikaans, 10" Android tablet, home use.

**Verdict summary:** No existing tool meets the Afrikaans requirement adequately. Custom PWA is the correct approach.

---

## Tobii Dynavox — TD Snap

**Website:** tobiidynavox.com
**Type:** Commercial AAC app (subscription)
**Platforms:** iPad, Windows, Android (APK via mytobiidynavox.com — not on Google Play)

### What it is

Tobii Dynavox is the world's leading AAC company. They make both dedicated speech-generating hardware devices and software apps. TD Snap is their flagship app — symbol + text based, with multiple built-in page sets including one specifically for aphasia.

**Built-in page sets relevant to aphasia:**
- **Aphasia** — designed for post-stroke adults; grid and visual scene options; 3×3, 4×3, 6×5 grid sizes
- **Core First** — symbol-based core vocabulary
- **Express** — simplified, easy entry point
- **Text** — keyboard + word prediction (7×10 grid)
- **Scanning** — switch access

**Features:**
- Touch, eye gaze, and switch access methods
- Customisable pages (add/edit buttons, phrases, categories)
- Code switching between languages in one message window
- Backup and sync
- Partner-assisted scanning

### Pricing

| Model | Price |
| --- | --- |
| Subscription (from May 21, 2024) | $9.99 USD/month (~$120/year) |
| One-time purchase (pre-May 2024) | $79.99 — no longer available |
| On Tobii Dynavox dedicated hardware | Perpetual licence included (hardware: $3,000–$8,000+) |

The switch to subscription in May 2024 was controversial and widely criticised in the AAC community.

### Afrikaans support — NOT available

Full supported language list (from TD Snap User's Manual v1.17):

> Arabic (SA), Chinese (Simplified), Czech, Danish, Dutch, English (AU/CA/UK/US), Finnish, French (CA/FR), German (DE/CH), Hebrew, Icelandic, Italian, Japanese, Norwegian, Polish, Portuguese (BR/PT), Spanish (ES/LatAm/US), Swedish, Turkish

**Afrikaans is absent.** This means:
- No Afrikaans symbol labels
- No built-in Afrikaans TTS
- No Afrikaans word prediction or auto-morphing
- All built-in vocabulary and page sets are English-only

**Note:** Prof Bornman and Monique Visser (Stellenbosch University) developed a culturally adapted Afrikaans AAC symbol set with Tobii Dynavox in 2025. However, this is not yet publicly released and appears to be a clinical/research deployment within the Tobii platform — it is not accessible as a standard TD Snap language pack.

### Could it be adapted for Dad?

Technically yes — you could create custom pages with Afrikaans text and attach manually recorded audio per button. But:
- Every built-in page set, symbol label, and menu remains English
- TTS speaks English unless you manually record audio for every button
- That is effectively what we are building anyway — but inside a $120/year subscription, locked to their ecosystem
- No benefit over our custom PWA for an Afrikaans user

### Verdict

**Not suitable.** Excellent product for 27 supported languages; nothing for Afrikaans.

---

## Lingraphica SmallTalk Aphasia

**Website:** lingraphica.com
**Type:** Commercial — dedicated aphasia app
**Platforms:** iPad only

### What it is

The most widely used dedicated aphasia app in the US. Purpose-built for post-stroke adults. Pre-loaded phrase sets in 8 categories (Stroke context, Conversation, Phone, Emergency, Meals, Restaurants, Health, Pain scale).

**Strengths:**
- Specifically designed for aphasia (not autism/CP as primary use case)
- Picture + text buttons — good for users with reading impairment
- Pain scale (Wong-Baker Faces)
- "I had a stroke" context-setting phrases built in

**Weaknesses for our use:**
- iPad only — no Android
- English only — no Afrikaans
- Subscription / device rental model
- No offline customisation without SLP involvement

### Verdict

**Not suitable** — iOS only, English only. Informed our phrase bank design (8-category structure, aphasia context phrases).

---

## Cboard

**Website:** cboard.io
**Type:** Open source, web-based AAC
**Platforms:** Any browser (PWA), Android app on Play Store

### What it is

Free, open-source, web-based AAC board. Supported by UNICEF. Symbol-based (ARASAAC symbols). Available in many languages via community translation.

**Afrikaans status:** Has partial Afrikaans UI translation (community-contributed) but no Afrikaans TTS and no Afrikaans symbol labels. Symbols use ARASAAC library (Spanish origin, culturally non-specific).

**Strengths:**
- Free and open source
- Runs in browser — similar architecture to our PWA
- Community-maintained phrase boards

**Weaknesses for our use:**
- No Afrikaans TTS
- Symbol-based (we want text-first for Dad)
- Generic vocabulary, not aphasia-specific
- Requires internet for full functionality

### Verdict

**Not suitable** — no Afrikaans TTS or vocabulary. Architecturally similar to what we're building but without the Afrikaans support we need.

---

## LetMeTalk

**Website:** github.com/rvolz/LetMeTalk
**Type:** Free, open source, Android
**Platforms:** Android

### What it is

Free Android AAC app using ARASAAC symbols. Open source (GitHub). Widely used in developing countries due to zero cost.

**Afrikaans status:** No Afrikaans TTS, no Afrikaans vocabulary. Uses Android system TTS — could theoretically use an Afrikaans TTS engine if one were installed, but none of good quality exists for Android offline.

**Strengths:**
- Free, Android-native
- Simple symbol-based interface
- Works offline

**Weaknesses for our use:**
- No quality Afrikaans TTS
- Symbol-based, not text-first
- Not aphasia-specific
- No easy remote maintenance

### Verdict

**Not suitable** — no Afrikaans audio.

---

## Comparison table

| Tool | Afrikaans TTS | Aphasia-specific | Android | Cost | Offline | Custom phrases |
| --- | --- | --- | --- | --- | --- | --- |
| **TD Snap** | No | Yes (English) | Yes (APK) | $120/yr | Yes | Yes (manual) |
| **SmallTalk Aphasia** | No | Yes (English) | No | Subscription | Yes | Limited |
| **Cboard** | No | No | Yes | Free | Partial | Yes |
| **LetMeTalk** | No | No | Yes | Free | Yes | Yes |
| **Our PWA** | Yes (WillemNeural) | Yes (designed for Dad) | Yes | Free | Yes | Yes (JSON+SSH) |

---

## Conclusion

No existing tool supports Afrikaans TTS with quality sufficient for a real user. All tools are either English-only, iOS-only, or require online connectivity for TTS. The custom PWA approach — pre-generated MP3s via Microsoft Edge TTS `af-ZA-WillemNeural`, served locally on the tablet — is the only viable path to a working Afrikaans AAC solution for Dad.

The tool review confirmed our architecture decisions rather than challenging them.
