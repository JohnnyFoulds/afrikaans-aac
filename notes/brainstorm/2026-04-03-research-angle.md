# AAC Research Angle — Academic Documentation

**Date:** 2026-04-03
**Status:** Exploratory — not a committed PhD topic

---

## Context

The v1 AAC PWA was built for a specific person (Dad, post-stroke expressive aphasia, Afrikaans-speaking, home care). After completing the practical build, we explored whether there is academic value in the work — publication, MSc, or PhD.

---

## What we built (the artefact)

- Custom Afrikaans AAC PWA — static HTML/JS, no framework
- Pre-generated MP3 audio via `af-ZA-WillemNeural` (Microsoft Edge TTS)
- Deployed on Android 15 tablet via Termux + Fully Kiosk Browser
- Afrikaans caregiver guide (IN–UIT–BEVESTIG protocol)
- Designed for adult post-stroke aphasia, home care, no SLT involvement

---

## The gap this fills

The academic case rests on three absences in the literature:

### 1. No validated adult Afrikaans AAC core vocabulary

All existing Afrikaans AAC vocabulary studies are paediatric (children). There is no empirically-derived core vocabulary set for adult Afrikaans speakers with post-stroke aphasia. Every existing SGD (Speech-Generating Device) either:
- Defaults to English, or
- Uses machine translation of English vocabulary sets (which does not capture Afrikaans cultural and pragmatic norms)

**This is the primary gap. A needs analysis + core vocabulary elicitation study would be the first empirical publication.**

### 2. No Afrikaans-specific post-stroke AAC deployment protocol

Existing AAC deployment research is predominantly English or other high-resource languages. The South African context adds:
- Low SLT-to-population ratio (few families get professional AAC assessment)
- Home care as the dominant post-acute setting
- Caregiver as the primary communication partner (not SLT)

### 3. Caregiver training gap

Almost no published work on Afrikaans caregiver AAC training. The IN–UIT–BEVESTIG (IN–OUT–VERIFY) protocol developed here is an adaptation of Supported Communication for Adults with Aphasia (SCA™) — but no Afrikaans-language version exists in the literature.

---

## Academic framing options

### Option A: Single publication (lowest effort)

**Title:** *A low-cost, home-deployed Afrikaans AAC system for post-stroke aphasia: design, implementation, and preliminary evaluation*

- Single-participant case study (n=1, Dad)
- Design Science Research (DSR) artefact cycle documented
- Contribution: existence proof + design lessons for low-resource African language AAC
- Target: *Augmentative and Alternative Communication* journal, or *African Journal of Disability*
- Realistic? Yes — the case study format is established in AAC literature; n=1 is acceptable for a design report

**Limitation:** Generalisation claims must be modest. "Preliminary" is the honest word.

### Option B: Master's by thesis (MSc — separate from existing DS&AI MSc)

> *Design and validation of a culturally-situated Afrikaans AAC system for post-stroke aphasia in low-resource home care*

Three chapters:
1. Needs analysis — semi-structured interviews with Afrikaans-speaking stroke survivors and caregivers; elicit priority vocabulary; compare to existing English/paediatric sets
2. Artefact development (DSR) — the PWA; justify design decisions against literature
3. Evaluation — usability + communication outcomes; structured sessions with 3–5 participants (including Dad); caregiver interview

**Effort:** M (months, not years) — much of chapters 2 is already done

**Home department problem:** This is Communication Sciences (UP, Stellenbosch) not Information Systems. An IS/CS master's on AAC is a stretch unless framed as HCI.

### Option C: PhD — HCI4D / African language accessibility framing

**Title:** *Design principles for home-deployed African language AAC systems: a design science research study*

**Framing:** Human-Computer Interaction for Development (HCI4D) with assistive technology focus. Contribution is not a single system — it is a set of transferable design principles for low-resource, African language, home care AAC deployment.

**DSR structure:**
- Cycle 1: Afrikaans (this work — Dad)
- Cycle 2: isiZulu or Sesotho (replication, different language family, recruited participants)
- Cycle 3: Cross-cycle abstraction → design principles

**What makes it PhD-level:**
1. Documented vocabulary gap (literature contribution)
2. Multi-language DSR methodology
3. Multi-participant evaluation (not n=1)
4. Generalisable design principles (not just "here is an app")

**Supervisor fit:**
- **Prof Judy van Biljon (UNISA CSET)** — NRF C1, HCI4D, ML4D, ODeL usability, published on disability and technology in African contexts. This is the most realistic fit within UNISA.
- **Prof Kerstin Tönsing (UP, Communication Pathology)** — CAAC director, co-supervisor on Odendaal (2024) dissertation, specialist in SA AAC research. Ideal content supervisor but UP Communication Pathology, not IS/CS.
- **Hybrid model:** van Biljon (primary, IS/HCI4D frame) + Tönsing (co-supervisor, AAC content). This combination would be strongest.

**The honest tension:** The deepest academic contribution is in Communication Sciences. Forcing it into IS/CS to fit UNISA CSET is a frame, not a lie — but it does limit which AAC-specific claims you can make without a clinical co-supervisor.

---

## Relevant literature already reviewed

| Cite key | Relevance |
|---|---|
| Odendaal-2022 | Only known study on SA SLT perspectives on adult Afrikaans AAC; confirms vocabulary gap |
| Beukelman-Light-2020 | Standard AAC textbook; core vocabulary framework |
| (Kertesz aphasia battery) | Assessment instrument; confirms aphasia type classification |
| SCA™ (Kagan et al.) | Supported Communication framework; source of IN–OUT–VERIFY protocol |

---

## Phased strategy

### Phase 0 — Write the complete thesis draft before registration (current resources only)

Using only Dad, Mom, and the deployed tool:

| Chapter | Content | Resources needed |
|---|---|---|
| 1 | Introduction + problem statement | Literature only |
| 2 | Literature review — vocabulary gap, SA SLT landscape, SCA™ | Sources already reviewed |
| 3 | DSR methodology + artefact design rationale | The build itself |
| 4 | Deployment + evaluation — Dad (n=1), Mom caregiver interview, phrase usage data | Dad + Mom |
| 5 | Proposed design principles (framed as "proposed, pending validation") | Synthesis of above |
| 6 | Limitations + future work — n=1 constraint named; community expansion as next step | Honest framing |

This draft is **submission-ready as a publication** and serves simultaneously as the **PhD research proposal** at registration. The supervisor reviews rather than guides from day one.

### Phase 1 — Community recruitment (day 1 of registration, running in parallel)

Recruit 3–6 Afrikaans-speaking stroke survivors via community stroke support groups. Deploy v2 to each. Operationally identical to the Dad deployment — second tablet, rsync, same tool. No hospital, no lab, no clinical infrastructure required.

Ethics: a community-based non-clinical study requires clearance, but this is lightweight compared to hospital-based research. UP or UNISA ethics committees handle this routinely.

### Phase 2 — Thesis refinement (after community data collected)

Fold community data into Chapter 4. Upgrade "proposed" design principles to "validated" in Chapter 5. The thesis already exists — this is revision, not writing from scratch.

---

## Risk assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| Community recruitment stalls (can't find 3–6 participants) | Low–Medium | Afrikaans stroke support groups are active; community is tight-knit; n=1 still yields a strong publication |
| Dad's condition changes during study | Medium | Phase 0 captures baseline data now; Phase 1 doesn't depend on Dad |
| Supervisor won't accept n=1 as DSR Cycle 1 | Low | Single-participant embedded case studies are established in AAC and DSR literature |

---

## Origin story note

"This started as a personal intervention for my father and grew into a formal study" is not a weakness — it is a legitimate DSR origin. The problem was real, the context was authentic, the first cycle was motivated by genuine need. That is exactly what DSR is supposed to look like. Document this explicitly in Chapter 1.

---

## Researcher background and what it means

**Background:** AI Engineer, MSc in Data Science and AI. No clinical training. Not an SLP.

### The problem

A PhD examiner in Communication Sciences will ask: *what clinical training do you have to evaluate communication outcomes in aphasia?* The answer is none. Submitting to UP Communication Pathology means competing against SLTs with 4 years of clinical training. Domain credibility gap is real.

### Why it is fine — if you own the frame

The background is the **reason** the framing must be HCI/IS, not Communication Sciences. This is not a compromise — it is the correct framing for what was actually built.

This is not a clinical intervention. It is a **low-cost, open-source, home-deployable AAC system** built using commodity hardware, edge TTS, and a static PWA. The contribution is **engineering + design**. The evaluation is **usability and caregiver experience** — not clinical outcomes.

An AI engineer with an MSc in DS&AI who builds an NLP-adjacent assistive technology system and evaluates it through HCI/DSR methodology belongs in CSET or an IS department, not Communication Pathology.

### What this means practically

**Own the frame.** Chapter 3 is not "here is a clinical AAC system" — it is "here is a design science artefact built by a technologist, evaluated through user experience and caregiver interviews, with design principles transferable to other low-resource language contexts."

**One clinical collaborator is required** — not as supervisor, but as co-author or advisor. Their role: validate that outcome measures are appropriate and aphasia framing is accurate. One email, one conversation, their name on the paper. Prof Tönsing (UP CAAC) is the natural candidate. This covers the clinical credibility gap without requiring clinical training.

**The actual superpower:** no SLP would have built this. They would have waited for institutional resources, a clinical trial protocol, and a commercial SGD. This was built in a weekend for a specific person in need. The PhD documents why that approach works and how others can replicate it. That is the contribution.

### One-line summary

The background is not a weakness — it is why the system exists at all. Frame it that way, get one clinical collaborator to validate the outcome measures, and submit to HCI/IS, not Communication Sciences.

---

## Relationship to UNISA RAG PhD

These are **two completely independent PhDs** on separate tracks:

| | UNISA RAG PhD | AAC PhD |
|---|---|---|
| Topic | RAG for ODL (UNISA tutorial letter corpus) | Afrikaans AAC for post-stroke aphasia |
| Frame | Information Systems / HCI4D | Communication Sciences / HCI4D |
| Institution target | UNISA CSET | UNISA CSET or UP Communication Pathology |
| Primary supervisor target | Prof van Biljon | Prof van Biljon (IS frame) or Prof Tönsing (UP) |
| Status | Active — application in progress | Exploratory — publication first |
| Dependency | None | None |

The AAC PhD does not compete with the UNISA RAG PhD. They are in different domains, potentially at different institutions, and on different timelines. The AAC track starts with a single publication (Option A) — no PhD commitment required yet.

---

## Deferred decisions

| # | Question | Notes |
|---|---|---|
| R1 | **Which institution for AAC PhD?** | UNISA CSET (HCI4D frame, van Biljon) vs UP Communication Pathology (Tönsing) — decision can wait until after publication |
| R2 | **Contact Prof Tönsing at UP?** | Relevant even for a standalone publication — she may want to co-author |
| R3 | **Ethics for n>1?** | Dad is family (informal consent); recruiting 3–5 additional participants requires formal ethics approval (UP or UNISA) |
| R4 | **Vocabulary elicitation study feasibility** | Requires access to Afrikaans-speaking stroke survivors outside family — via stroke support groups, neurology wards |
