# PhD Research Summary — Johannes Foulds

**Working title:** AI-Assisted Augmentative Communication for Post-Stroke Aphasia in an Under-Resourced African Language Setting

---

## The problem

Approximately 34% of stroke survivors develop aphasia — a specific impairment to language *production* while comprehension remains intact. In South Africa, Afrikaans-speaking patients in home-care settings have no viable pathway to speech-language therapy (workforce too small, language mismatch) and no AAC technology designed for their language or context.

Augmentative and Alternative Communication (AAC) tools address this gap by offering pre-formed phrases the patient can select rather than generate. Evidence is strong: 90% positive or mixed outcomes across 30 high-technology AAC studies. But existing tools are generic, English-dominant, and cloud-dependent — none of them works for an Afrikaans speaker on a commodity tablet with intermittent connectivity.

---

## The research gap (four intersecting dimensions)

| Dimension | Gap |
|---|---|
| **Clinical** | No deployed AI-assisted AAC system exists for post-stroke Afrikaans-speaking home-care patients |
| **Language** | No adult Afrikaans clinical vocabulary list or NLP corpus exists; the only published vocabulary lists cover preschool children |
| **AI interaction** | All published LLM-AAC work is English-only; the listen-and-suggest modality (ASR → conditioned phrase suggestion) has no Afrikaans or African language implementation |
| **Deployment** | All existing AI-AAC systems assume cloud inference; the edge deployment constraints of commodity Android hardware in South African home-care settings are uncharacterised |

The intersection of all four is empty. This is not a contrived gap — it is the exact space where a clinical need, a language technology vacuum, a deployment constraint, and a design problem converge.

---

## The research artefact

A Progressive Web App (PWA) AAC system is already built and in active daily use by one participant: an Afrikaans-speaking man with post-stroke aphasia, full comprehension intact, touchscreen tablet in home care. The system is fully offline, runs Edge TTS (`af-ZA-WillemNeural`) for voice output, and is personalised to his vocabulary and routines.

This is not a prototype. It is a deployed, dependency-free system with a real user and a real usage log — an unusually strong starting point for a PhD that takes Design Science Research (Hevner et al., 2004) as its methodology.

---

## The three PhD contributions

**Contribution 1 — Adult Afrikaans clinical vocabulary corpus**
Elicit, annotate, and publish the first vocabulary dataset for adult Afrikaans-speaking AAC users. Currently no such resource exists; the only published Afrikaans vocabulary lists cover preschool children. This is a foundational resource for any downstream NLP or ASR work, and is publishable independently.

**Contribution 2 — NLP-assisted phrase prediction for a low-resource African language**
Fine-tune a multilingual sentence transformer (AfroXLM-R or equivalent) on the adult Afrikaans corpus and evaluate phrase-ranking quality against a frequency baseline. Characterise the sparse-feedback personalisation problem (single user, tens of tap events per day) and implement a lightweight on-device ranking model. Evaluate longitudinally in the deployed system.

**Contribution 3 — Listen-and-suggest: conversational ASR + conditioned response generation**
Build an Afrikaans ASR component (Whisper fine-tuned on in-domain speech) that transcribes the communication partner's utterances and generates a ranked shortlist of contextually appropriate stored responses for the patient to select. Evaluate response quality, latency, and user acceptance. Derive and publish design principles for offline-first AI-assisted AAC in under-resourced African language settings.

---

## Why DSR, not an RCT

Design Science Research (Hevner et al., 2004) is the appropriate methodology for an AI-artefact PhD: the artefact is the contribution; the deployment evaluation is the validation mechanism. A randomised controlled trial would require ethics clearance, clinical collaborators, and 20–30 participants — infrastructure that takes 18–24 months to build. DSR begins with the existing N=1 deployment and expands through design cycles as ethics clearance is obtained. This is not a limitation — it is the standard iterative DSR process.

---

## Why this matters beyond one patient

Each of the three contributions generalises:

- The vocabulary corpus is reusable for any Afrikaans NLP downstream task
- The NLP evaluation framework applies to any low-resource African language AAC setting
- The design principles for offline-first AI-assisted AAC apply across South African and sub-Saharan African home-care deployments
- The personalisation framework (sparse-feedback, single-user, clinical domain) applies to any under-resourced AAC deployment globally

Vodacom's accessibility and connectivity-equity commitments are directly relevant: the edge deployment characterisation produces actionable guidance for any AI-enabled health application designed for the South African market.

---

## Current status

- Deployed artefact: live, daily use, one participant
- Literature review: complete (17 papers with full MKV conversion)
- Vocabulary gap: confirmed in literature; elicitation planned
- Ethics: not yet submitted; N=1 deployment under informal consent
- Target institutions: Stellenbosch University (primary — Prof Herman Kamper, E&E / Prof Thomas Niesler, Afrikaans ASR); UCT (fallback — Assoc Prof Melissa Densmore, HCI/AT)
- Target start: January 2027

---

*Johannes Foulds — Senior AI Engineer, Vodacom South Africa — MSc Data Science & AI*
*hfoulds@gmail.com*
