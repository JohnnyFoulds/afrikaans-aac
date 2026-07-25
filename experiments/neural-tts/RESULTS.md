# Neural Afrikaans TTS Experiment — Results

**Date:** 2026-07-25  
**Machine:** dragon (RTX 3090 Ti, 23 GB VRAM, PyTorch 2.6.0+cu124)  
**Model:** UBC-NLP/Simba-TTS-afr (VITS/MMS-TTS, EMNLP 2025, 36.3M params)  
**Branch:** feat/neural-afrikaans-tts

---

## Step results

| Step | Status | Notes |
| --- | --- | --- |
| CUDA verification | ✅ PASS | RTX 3090 Ti, 23 GB VRAM, CUDA 12.2 |
| Dependency install | ✅ PASS | transformers 4.57.6, optimum 2.1.0, onnxruntime 1.28.0 (CPU) |
| PyTorch inference | ✅ PASS | 5 phrases, 16 kHz WAVs, UTF-8 diacritics handled |
| ONNX export | ✅ PASS | 109 MB model.onnx; tolerance warning expected for VITS stochastic sampling |
| ONNX inference | ✅ PASS | onnxruntime InferenceSession; ORTModelForTextToWaveform not in optimum 2.1.0 |

## Installed packages

```
transformers==4.57.6
optimum==2.1.0
onnxruntime==1.28.0   # CPU build; onnxruntime-gpu 1.27.0 requires CUDA 13, dragon has 12.2
onnx==1.22.0
scipy==1.18.0
soundfile==0.14.0
accelerate==1.14.0
```

---

## Audio quality assessment

**Verdict: NOT SUITABLE for production use.**

Samples were played back on the target device and evaluated against Edge TTS `af-ZA-WillemNeural`.

Key finding: the model mispronounces core Afrikaans vocabulary, including basic words like
"môre" — a word that would appear in the very first phrase any AAC user would say. The
prosodic quality is also poor: flat intonation, unnatural rhythm, and a non-native-sounding
accent throughout. Varying `noise_scale` (0.1–0.667), `noise_scale_duration` (0.3–0.8), and
`speaking_rate` (0.9–1.0) produced no meaningful improvement — the problems are in the
model weights, not the inference parameters.

**Root cause:** The NCHLT Afrikaans corpus (~56 hours, ~200 speakers) used to train this model
is read speech recorded under lab conditions. It is too narrow and too small to produce a
natural-sounding voice. The SimbaBench paper (EMNLP 2025) optimises for ASR/TTS benchmarks
across 7 African languages simultaneously; per-language quality is sacrificed for breadth.

**Comparison with Edge TTS af-ZA-WillemNeural:** not in the same league. Willem is a production
neural voice trained on far more data with professional recording quality.

**Comparison with eSpeak NG af (formant):** Simba is marginally less robotic in timbre but
worse in intelligibility for Afrikaans-specific phonemes. eSpeak at least pronounces "môre"
correctly. For a communication device, intelligibility > naturalness.

---

## Architecture recommendation

The phonemizer-only WASM path (`wide-video/espeakng-wasm`) that motivated this experiment
is NOT currently useful for Afrikaans: no neural Afrikaans TTS model exists that is good
enough to pair with it at acceptable quality.

**Revised Tier-2 recommendation:** eSpeak NG (`steveseguin/espeakng.js`, 3.3 MB WASM) remains
the only viable offline fallback. Robotic but intelligible and correct. The Phase 1 decision
to defer Tier-2 entirely and use visual text fallback remains defensible given the quality gap.

**Conditions under which this changes:**
1. A higher-quality Afrikaans TTS dataset is recorded and released (none known as of 2026-07-25)
2. Someone fine-tunes Simba or a similar VITS model on that data
3. Edge TTS adds an offline/on-device deployment path for WillemNeural

---

## Files

| File | Description |
| --- | --- |
| `inference_test.py` | PyTorch inference script (5 test phrases) |
| `*.wav` | PyTorch inference outputs (committed) |
| `best_*.wav` | Parameter sweep outputs (noise_scale / speaking_rate variants) |
| `onnx_test.wav` | ONNX inference output |
| `simba-tts-afr-onnx/` | ONNX export directory (model.onnx gitignored, configs committed) |
