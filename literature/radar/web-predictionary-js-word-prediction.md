---
# IDENTITY
title: "predictionary — JavaScript dictionary-based word prediction library with self-learning (AsTeRICS AAC project)"
type: web-article
url: "https://asterics.github.io/predictionary/"
cite_key: ""

# PROVENANCE
author: "AsTeRICS Foundation"
organisation: "AsTeRICS Foundation (open-source AAC/AT ecosystem)"
site_name: "GitHub / npm"
date_published: "2021"
date_accessed: "2026-07-25"
duration: ""
platform: ""

# WORKFLOW
date_added: "2026-07-25"
status: processed
tags: [predictive-text, word-prediction, javascript, browser, pwa, aac, assistive-technology, offline, self-learning, afrikaans]
priority: high

# TRIAGE
relevance: "Pure-JavaScript, browser-native word prediction library from the AsTeRICS AAC ecosystem — the resolved browser-native alternative to Presage for the AAC PWA's word-prediction grid; zero dependencies, self-learning, IndexedDB-serialisable, works offline."
transcript_path: ""
---

# predictionary — JavaScript word prediction library (AsTeRICS AAC project)

## Why on radar

The AAC PWA requires a word-prediction grid that completes the current prefix and ranks completions by usage frequency. `predictionary` is the resolved browser-native implementation choice, identified after confirming that Presage (the originally-considered C++ library) has no WASM port and cannot run in the browser without major porting work (see `web-presage-predictive-text-aac.md`).

`predictionary` is the correct tool for three reasons:

1. **Browser-native**: pure JavaScript, zero dependencies, runs in any browser including the PWA's Android WebView — no install, no native process, no WASM compilation required.
2. **AAC provenance**: built by the AsTeRICS Foundation specifically for AAC use cases (the same open-source ecosystem as the Grid AAC software). Word prediction for people with motor/speech disabilities is its explicit design context, not a secondary use.
3. **Self-learning with JSON persistence**: the `learn()` method promotes chosen words and adapts rankings to the user's vocabulary. State serialises to a JSON string, which can be persisted to IndexedDB and reloaded across sessions — satisfying the personalisation requirement without a server.

## Source quality

Primary source: GitHub repository `asterics/predictionary` and npm package page. The AsTeRICS Foundation is an established open-source AT organisation (develops AsTeRICS Grid, ARE — the AsTeRICS Runtime Environment — and related AAC tools). The library is actively maintained (latest release v1.6.0, 2.3 MB unpacked). Grey/open-source documentation; not peer-reviewed. The AAC/AT context is well-established: AsTeRICS Grid is widely used in European AAC practice.

## Summary

`predictionary` is a pure-JavaScript, zero-dependency word prediction library designed for AAC systems. It maintains one or more named dictionaries of words, each word carrying a rank (lower rank = higher priority in suggestions). Given a text prefix, `predict(prefix)` returns the ranked list of matching words. The `learn(word)` method increments a chosen word's priority, implementing frequency-based self-learning. Dictionaries serialise to/from JSON strings, enabling persistence to IndexedDB or localStorage. Multiple dictionaries can be loaded simultaneously (e.g. a static base Afrikaans frequency list plus a user-specific learned dictionary), queried together or independently. The library is an ES6 module, installable via npm or includable via a `<script>` tag from unpkg/jsDelivr. License: unspecified in README (to verify before shipping).

## Key claims

- **Zero install, browser-native**: `npm install predictionary` or `<script src="https://unpkg.com/predictionary/dist/predictionary.min.js">` — no WASM, no native binary, no server. Works in any browser that supports ES6 modules.
- **Prediction is prefix-completion, not n-gram context**: `predict('goe')` returns words beginning with "goe" ranked by frequency/recency — it does **not** use prior context tokens (bigram/trigram conditioning). This is simpler than Presage but sufficient for a prefix-completion grid UX. The user types the first letter(s) of the next word and selects from the grid.
- **Self-learning**: `learn(word)` is called after the user selects a word; it promotes that word's rank, so frequently chosen words surface earlier over time. This is the frequency-based adaptation described in the brainstorm session.
- **Multiple dictionaries, different weights**: the app can load a static Afrikaans base frequency list as one dictionary and a user-utterance-history dictionary as another, then query both. The base dict provides cold-start coverage; the user dict personalises over time.
- **JSON round-trip for IndexedDB persistence**:
  ```javascript
  // Save after each session
  const json = pred.dictionariesToJSON();
  await idbKeyval.set('prediction-state', json);

  // Restore on load
  const json = await idbKeyval.get('prediction-state');
  if (json) pred.loadDictionaries(json);
  ```
- **Cold-start seeding**: on first run, seed from a pre-built Afrikaans frequency list derived from the `text2ngram` corpus pipeline (see **Corpus pipeline** section below).
- **No context-awareness is the key limitation vs Presage**: Presage's trigram predictor conditions on the two preceding words — e.g. after "goeie" it predicts "môre" more highly than after "baie". `predictionary` cannot do this; it ranks purely by frequency × recency. For the current single-user AAC device, this is likely acceptable: the user's vocabulary is narrow and high-frequency items will dominate the list quickly. Context-conditioning is a later enhancement if warranted.
- **Bundle size**: 2.3 MB unpacked; the minified browser bundle (`predictionary.min.js`) is substantially smaller. No voice data, no WASM binary.
- **License**: to be verified before shipping — README does not state a licence. The npm package should be checked (`package.json` `license` field). AsTeRICS projects are typically MIT or Apache 2.0, which would be compatible with the PWA.

## Connections to research

- **Resolves the Presage WASM blocker**: this is the Phase 1 browser-native word prediction implementation. See `web-presage-predictive-text-aac.md` for the Presage architecture that informed the design requirements.
- **Pairs with eSpeak NG WASM for full offline operation**: the PWA can predict (`predictionary`) and speak (`steveseguin/espeakng.js`) entirely offline, with no Android system dependencies. See `web-espeak-ng-wasm-afrikaans-tts.md`.
- **Self-learning maps to the brainstorm phrase-bank design**: the frequency-promoting `learn()` call is the implementation of the decay-weighted quick-phrase bank scoring discussed in `notes/brainstorm/2026-07-25-the-boys/2026-07-25-the-boys.md`. The phrase bank and the prediction dictionary can share the same `predictionary` instance.
- **Afrikaans corpus pipeline**: see the **Corpus pipeline** section below — `text2ngram` (Presage) on dragon is the correct tool to generate the frequency data that seeds `predictionary`.

## Transcript / Notes

### Key URLs

| Resource | URL |
| --- | --- |
| npm package | <https://www.npmjs.com/package/predictionary> |
| GitHub repo | <https://github.com/asterics/predictionary> |
| Project page / demo | <https://asterics.github.io/predictionary/> |
| unpkg CDN | <https://unpkg.com/predictionary/dist/predictionary.min.js> |
| AsTeRICS Foundation | <https://www.asterics-foundation.org/> |

### Corpus pipeline — generating the Afrikaans word list

**The right tool is `text2ngram` from Presage, run on dragon.** `predictionary` has no built-in corpus ingestion; `text2ngram` does it properly. The workflow:

#### Step 1 — Get Afrikaans corpus (on dragon)

```bash
# NCHLT Afrikaans text corpus (North-West University / SADiLaR)
# Available at: https://repo.sadilar.org/items/2bf723bc-7420-439e-a55d-833e10b0c776
# Or GoVZA government text (crawled af.gov.za content)
# Or user utterance log exported from the app's IndexedDB
```

#### Step 2 — Install presage (on dragon, Ubuntu 24.04)

```bash
sudo apt install presage
# text2ngram is included in the presage package
which text2ngram
```

#### Step 3 — Generate n-gram SQLite databases

```bash
# Unigrams (word frequencies for predictionary seed)
text2ngram -n 1 -o af_1gram.db -f sqlite -l corpus.txt

# Bigrams (context: what word follows which word)
text2ngram -n 2 -o af_2gram.db -f sqlite -l corpus.txt

# -l flag enables lowercase conversion
```

#### Step 4 — Convert to JSON for the PWA

```python
import sqlite3, json

# Unigrams → ranked word list for predictionary
db1 = sqlite3.connect('af_1gram.db')
# Inspect actual table/column names first: db1.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
rows = db1.execute('SELECT word, count FROM ngram ORDER BY count DESC LIMIT 5000').fetchall()
unigrams = [{"word": w, "rank": i + 1} for i, (w, _) in enumerate(rows)]
json.dump(unigrams, open('af_unigrams.json', 'w'), ensure_ascii=False)

# Bigrams → context trie for JS query
db2 = sqlite3.connect('af_2gram.db')
rows2 = db2.execute('SELECT w1, w2, count FROM ngram').fetchall()
bigrams = {}
for w1, w2, count in rows2:
    bigrams.setdefault(w1, {})[w2] = count
json.dump(bigrams, open('af_bigrams.json', 'w'), ensure_ascii=False)

print(f"Unigrams: {len(unigrams)} words")
print(f"Bigram contexts: {len(bigrams)} first words")
```

**Note**: inspect the actual SQLite schema with `.tables` and `PRAGMA table_info(ngram)` before running — `text2ngram`'s column names need to be confirmed against the installed version.

#### Step 5 — Seed predictionary at app startup

```javascript
import Predictionary from 'predictionary';
import unigramData from './af_unigrams.json';  // bundled at build time

const pred = Predictionary.instance();

// Load persisted user state if it exists
const saved = await idbGet('prediction-state');
if (saved) {
    pred.loadDictionaries(saved);
} else {
    // Cold start: seed base Afrikaans frequency list
    pred.addDictionary('base');
    pred.addWords(unigramData, 'base');  // [{word, rank}] format
    pred.addDictionary('user');          // starts empty, filled by learn()
}
```

#### Step 6 — Context-aware prediction (bigram trie, separate from predictionary)

For true bigram context, query the JSON trie directly in JS alongside predictionary:

```javascript
import bigrams from './af_bigrams.json';

function predict(prevWord, prefix) {
    // Bigram context if we have a previous word
    const candidates = bigrams[prevWord] ?? {};
    // Fall back to predictionary unigram ranking
    const unigrams = pred.predict(prefix);

    // Merge: bigram-ranked matches first, then unigram fill
    const bigramMatches = Object.entries(candidates)
        .filter(([w]) => w.startsWith(prefix))
        .sort((a, b) => b[1] - a[1])
        .map(([w]) => w);

    return [...new Set([...bigramMatches, ...unigrams])].slice(0, 8);
}
```

### Comparison with Presage

| Property | Presage | predictionary + text2ngram pipeline |
| --- | --- | --- |
| Language | C++ | JavaScript (prediction) + C (corpus build) |
| Browser-native | No | Yes |
| Corpus ingestion | `text2ngram` built-in | `text2ngram` at build time → JSON |
| Context-awareness | Yes (trigram, runtime) | Yes (bigram, baked into JSON trie) |
| Self-learning | Yes (online + offline) | Yes (frequency promotion via `learn()`) |
| Persistence | SQLite file | JSON string (IndexedDB) |
| Phase 1 choice | No | **Yes** |
