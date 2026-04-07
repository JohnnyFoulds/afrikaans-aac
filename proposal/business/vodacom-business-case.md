# Business Case: Vodacom Partnership for Afrikaans AAC

**Document type:** Internal strategy document — not a final pitch deck  
**Date:** 2026-04-05  
**Author:** Johannes Foulds  
**Purpose:** Articulate the strongest credible case for Vodacom engagement, map
it against Vodacom's documented strategic priorities, and identify the specific
ask, the right entry points, and the honest risks.

**Research basis:** All Vodacom claims in this document are sourced from
Vodacom's own press releases, conference materials, and product pages as
documented in `notes/vodacom-aac-research.md` and
`notes/vodafone-group-aac-research.md`. No Vodacom claims are invented or
speculated beyond what is documented there.

---

## 1. The Opportunity in One Paragraph

Vodacom has spent over two decades building South Africa's most sophisticated
disability-and-connectivity programme — and has a conspicuous blind spot. Its
entire disability portfolio addresses Deaf, hearing-impaired, and visually
impaired customers. It has no product, service, or research programme for the
hundreds of thousands of South Africans who lose speech following stroke. This
project — a working, deployed, open-source Afrikaans AAC system built at zero
institutional cost — sits exactly where Vodacom's stated purpose-led strategy,
its SAMRC relationship, its ConnectU zero-rating infrastructure, and its
African language AI capability converge. The opportunity is to be the first
African mobile operator to address acquired communication disability at scale.
The entry cost for Vodacom is low. The reputational and commercial return is
high. The academic and social impact is documented.

---

## 2. The Problem This Project Solves

### 2.1 Stroke and Acquired Communication Disability in South Africa

Stroke is one of South Africa's leading causes of adult disability. Globally,
approximately one-third of stroke survivors develop aphasia — a language
disorder that typically leaves comprehension intact while destroying the ability
to speak, write, and type (Brady et al., 2021, *Stroke*; Beukelman & Light,
2020). Up to 40% of people with aphasia will have chronic, severe communication
impairment for the rest of their lives.

South Africa carries a disproportionate stroke burden relative to its income
level, driven by hypertension prevalence, limited tertiary care access outside
major centres, and post-discharge rehabilitation gaps. Exact national aphasia
incidence data is unavailable — a gap that itself reflects how invisible this
population is to health systems and to industry.

What is certain from the international literature: if South Africa's stroke
incidence approximates the global median (roughly 250 per 100,000 population
per year), and one-third of those develop aphasia, several tens of thousands of
South Africans acquire aphasia every year. Most will go home with no AAC
support, no Afrikaans-language tool, and no institutional follow-up.

### 2.2 The Afrikaans Language Gap

There is no commercially available AAC system in Afrikaans. Every commercial
speech-generating device on the South African market defaults to English
vocabulary. Hattingh, Louw, and Uys (2020) — the only published study on adult
Afrikaans AAC vocabulary — confirmed that no empirically-derived Afrikaans core
vocabulary set exists for adults with acquired communication disorders. This
means an Afrikaans-speaking stroke survivor must either communicate in a foreign
language or go without.

This is not a niche edge case. Afrikaans is spoken as a first language by
approximately 6.2 million South Africans (2022 Census, ~10.6% of the
population). It is the third most common home language in South Africa. It is
the dominant home language in the Western Cape and Northern Cape. Afrikaans
speakers are disproportionately represented in older age cohorts — the primary
stroke demographic.

### 2.3 The SLT Access Gap

South Africa has an acute shortage of speech-language therapists (SLTs).
Odendaal and Tönsing (2024) and Odendaal (2022) document that SLT access in
South Africa is severely constrained, particularly for post-acute, community-
based, and home-care patients. The consequence is that most people with aphasia
in South Africa go home from hospital with no ongoing SLT support, no AAC
assessment, and no device. Families and caregivers are left to manage
communication without training or tools.

### 2.4 The Digital Access Gap (Where Vodacom Enters)

Standard commercial AAC apps (Proloquo2Go, Snap Core First, TouchChat) cost
USD 200–350 per app licence plus the device. Monthly data plans are required
for cloud-dependent features. These price points are inaccessible to the
majority of South African households.

The project system is:
- **Free** — open source, zero licence cost
- **Fully offline** — no data required after deployment
- **Runs on commodity Android hardware** — any mid-range tablet
- **Afrikaans-native** — built around a specific user's communicative ecology,
  not translated from English defaults

This is precisely the access gap Vodacom has positioned itself to close.

---

## 3. What Has Been Built

The artefact is a functioning, deployed Augmentative and Alternative
Communication (AAC) system:

| Component | Description |
|---|---|
| **Type** | Progressive Web App (PWA) — static HTML/JS, no framework |
| **Language** | Afrikaans — all vocabulary, all audio |
| **Voice output** | Microsoft Edge TTS `af-ZA-WillemNeural` (pre-generated MP3 files; no cloud call at runtime) |
| **Hardware** | AWOW UTBook\_15, Android 15 tablet (≈R2,500–R3,500 retail) |
| **Connectivity** | **Fully offline** — no data required |
| **Deployment** | Termux + Fully Kiosk Browser; locked-down single-app mode |
| **Status** | Live, in active daily use by one participant (post-stroke, home care) |
| **Cost to replicate** | ~R3,000 (hardware) + zero for software |
| **Caregiver protocol** | IN–UIT–BEVESTIG (IN–OUT–VERIFY), adapted from Supported Communication for Adults with Aphasia (SCA™); Afrikaans caregiver guide exists |
| **Source code** | Private currently; publishable under open licence |

The system is not a prototype. It is being used every day by a real person.
The design decisions are documented and grounded in the peer-reviewed clinical
literature on post-stroke aphasia and AAC (Beukelman & Light, 2020; Koul &
Beck, 2011; Odendaal & Tönsing, 2024; Thiel et al., 2016, 2017, 2022).

---

## 4. Why Vodacom

Vodacom is the right partner for four specific, documented reasons.

### 4.1 Stated Purpose and Conference Platform

Vodacom Group CEO Shameel Joosub at the 2025 Disability and Accessibility
Conference (1 July 2025, Johannesburg):

> "At Vodacom Group, true inclusion begins with understanding the daily
> realities of persons with disabilities and co-creating solutions that respond
> to their needs."

> "Empowering people through connectivity is central to Vodacom's purpose-led
> strategy. Whether through assistive technologies, inclusive digital literacy
> programmes, or accessible customer service, we're committed to closing the
> digital divide and enabling equitable participation for everyone."

Stephen Chege, Chief Officer for Regulatory and External Affairs:

> "This includes supporting digital innovations that overcome accessibility
> barriers and reviewing organisational, and broader policies that ensure no
> one in Africa is left behind."

The 2025 conference theme — "Implementing accessibility upfront, promoting
positive customer experiences" — is directly relevant. Acquired communication
disability (aphasia) is accessibility infrastructure that Vodacom has not yet
implemented. A partnership here is consistent with, not additional to, the
stated strategy.

### 4.2 The SAMRC Relationship

The South African Medical Research Council (SAMRC) sent a representative
(Bradley Carpenter) to the 2025 Disability and Accessibility Conference as a
named speaker alongside Vodacom's CEO. This is a documented, active
institutional relationship. The SAMRC funds health research across stroke,
rehabilitation, and disability. A three-way structure — Vodacom (connectivity
and funding), SAMRC (research validation and clinical credibility), AAC project
(artefact and community deployment) — is now a credible possibility rather
than a speculative one, because the two institutional parties already share a
platform.

### 4.3 ConnectU Zero-Rating Infrastructure

Vodacom's ConnectU platform zero-rates access to specific digital services for
low-income customers. Emergency health services are already zero-rated. The
platform's own documentation states that clinics and health organisations can
apply for zero-rated status. A free AAC Progressive Web App, deployed to
Afrikaans-speaking stroke survivors via community health worker referral, is
exactly the kind of health-adjacent digital service ConnectU was designed to
enable. This does not require Vodacom to build anything new — it requires
applying the existing infrastructure to a new, documented population.

### 4.4 African Language AI and 5G/Digital Inclusion Narrative

Vodacom's 2024–2025 positioning has consistently framed African language
digital inclusion as a strategic differentiator. The `af-ZA-WillemNeural` TTS
voice this system runs on is a Microsoft product. An Afrikaans AAC system
jointly branded with Vodacom — the South African operator most associated with
connectivity for underserved communities — provides a concrete, human, and
narratively powerful case study for exactly this framing. The story of a
post-stroke Afrikaans-speaking man communicating with his family again through
a system deployed on a tablet via Vodacom connectivity is more compelling to
any stakeholder audience than a 5G bandwidth demonstration.

---

## 5. The Blind Spot Vodacom Has Not Addressed

Vodacom's disability portfolio, as documented in research, addresses three
populations:

1. **Deaf / hearing-impaired**: National Relay Service (2022), ER24 text
   emergency (2017), SASL workplace training (2026), BlindShell Classic 2 (2025)
2. **Visually impaired**: BlindShell Classic 2, GARI device accessibility,
   screen reader support
3. **Senior citizens**: Priority service, accessible billing formats

**The population that acquired speech loss after stroke or brain injury is not
served by any Vodacom product, service, or programme.**

This population:
- Can hear perfectly (NRS is not relevant to them)
- Can usually read (visual impairment devices are not relevant to them)
- Can use a touchscreen (mobility devices are not relevant to them)
- Cannot speak and cannot reliably type (both primary modes of mobile
  communication are unavailable to them)

They are the people most in need of an alternative communication channel, and
the people for whom Vodacom's current portfolio provides nothing.

This is not a criticism — it is a specific, unopened door.

---

## 6. What We Are Asking For

The ask is modular. Each level stands independently. Vodacom can engage at
whatever level aligns with current programme capacity.

### Level 1 — Zero-Rating (Lowest cost, highest leverage)

**Ask:** Zero-rate the AAC Progressive Web App on ConnectU for Vodacom
customers who are registered under the Specific Needs programme.

**What Vodacom does:** Apply the existing ConnectU zero-rating infrastructure
to one more URL. Zero incremental engineering cost. Follows the precedent
already set for health and emergency services.

**What this achieves:** Any Afrikaans-speaking post-stroke AAC user on a
Vodacom SIM can download and use the system without spending data. This alone
removes the primary access barrier for low-income households.

**Precedent:** ConnectU already zero-rates emergency health services and allows
health organisations to apply for zero-rated status.

### Level 2 — Research Partnership (SAMRC bridge)

**Ask:** Facilitate introduction to the SAMRC contact (Bradley Carpenter,
2025 conference) or equivalent, for joint research funding on Afrikaans AAC
deployment outcomes.

**What Vodacom does:** One email introduction, and/or joint application for
SAMRC innovation grant funding. Vodacom provides connectivity infrastructure
and the SAMRC provides research credibility.

**What this achieves:** An academically validated study on low-cost, African
language AAC deployment — the first of its kind in South Africa. Publications
in *Augmentative and Alternative Communication*, *African Journal of Disability*,
and communication sciences journals. A citable case study for Vodacom's ESG
reporting.

**Return for Vodacom:** Independent research validation that Vodacom's
connectivity infrastructure enabled measurable communication outcomes for a
documented underserved disability population. This is exactly the evidence
Vodacom needs to report against the UN Disability and Development Report 2024
framing used at the 2025 conference.

### Level 3 — Pilot Deployment Partnership

**Ask:** Co-fund a 12-month community deployment pilot in partnership with
Afrikaans stroke support groups (Western Cape and Northern Cape). Target: 20–30
participants, community health worker-referred, tablet + data provision.

**What Vodacom does:** Provide subsidised tablets and/or data SIMs for the
cohort; provide access to existing Specific Needs programme infrastructure for
registration; co-brand the deployment.

**What the project delivers:** Full deployment, caregiver training (Afrikaans
IN–UIT–BEVESTIG protocol), outcome data collection, and published results.

**What this achieves:** South Africa's first community-scale Afrikaans AAC
deployment study. The evidence base for national scale-up. A model that can be
replicated in isiZulu, Sesotho, and other under-resourced languages.

**Return for Vodacom:** Category-defining first-mover position in acquired
communication disability across Africa. Tangible SDG-linked outcomes data.
A story the 2026 Disability and Accessibility Conference can anchor on.

### Level 4 — Foundation Grant (Optional, longer horizon)

**Ask:** Vodacom Foundation grant for a full DSR (Design Science Research) PhD
study on design principles for home-deployed African language AAC systems.

**What this achieves:** A supervised PhD that produces open-source design
principles replicable across all 11 official South African languages. This is
not a one-system study — it is the academic foundation for a national AAC
infrastructure in indigenous languages that currently does not exist.

**Return for Vodacom Foundation:** Alignment with the Foundation's education
and digital skills mandate; a fundable, bounded, time-limited research
programme with clear outputs; academic publications with Vodacom Foundation
acknowledged as funder.

---

## 7. What Vodacom Does Not Need to Do

To prevent scope inflation, this section states explicitly what is not being
asked:

- Vodacom does not need to build or maintain the app
- Vodacom does not need to hire SLTs or clinical staff
- Vodacom does not need to distribute or support hardware beyond the pilot
- Vodacom does not need to partner exclusively — SAMRC, SASLHA, and university
  clinical partners are also targeted
- Vodacom does not need to make a commercial product — this is a social impact
  and research partnership, not a product development engagement

---

## 8. The Competitive and Reputational Argument

No South African mobile operator has addressed acquired communication
disability. MTN's disability work is also exclusively Deaf/hearing-impaired
(Convo SA relay pilot, 2023). The space is unoccupied.

The window for first-mover positioning is open now because:
1. No competitor has moved into this space
2. The UN Disability and Development Report 2024 (cited by Vodacom at the 2025
   conference) creates an ESG accountability context that makes acquired
   communication disability a credible SDG reporting gap
3. The Vodacom × SAMRC relationship (documented at the 2025 conference) is
   already active — this project has a natural institutional bridge

The risk of inaction is not that a competitor moves first (this market is
too small to attract commercial competition). The risk is that in three years,
when the academic publications are out, the first conference paper describing
this system will note that it was built without any telco support — while
Vodacom's 2025 conference was quoting the UN report on exactly this population.

---

## 9. Honest Assessment of Risks and Weaknesses

This is an internal strategy document. The following risks are stated clearly
so that any outreach engagement is grounded.

| Risk | Assessment |
|---|---|
| **The project is currently n=1** | True. One deployed user. The business case for Vodacom is the *scale-up* story, not the current deployment. The n=1 status is appropriate for Phase 0; it is not the pitch. |
| **No clinical partner yet** | True. Prof Tönsing (UP CAAC) is the target. Until she or equivalent is engaged, the clinical validation dimension is aspirational. Do not overstate it. |
| **Vodacom Foundation's current focus is education + GBV** | True. Foundation funding is a Level 4 ask and the longest shot. Zero-rating (Level 1) and SAMRC bridge (Level 2) are the realistic near-term targets. |
| **No formal ethics approval for community deployment** | True. Any pilot beyond n=1 (family) requires ethics approval. This is achievable (UP or UNISA Ethics Committee) but must be in place before a Level 3 pitch is made. |
| **The Afrikaans-specific framing limits pan-African scalability story** | True but manageable. The correct framing is "Afrikaans is Cycle 1 of a multi-language design science research programme — the design principles generalise to isiZulu, Sesotho, etc." Do not pitch this as Afrikaans-only. |
| **Vodacom may prefer to build their own version** | Addressed by open-source licensing. The correct response: "We'd encourage that. The design principles and vocabulary set are available for any implementation. Attribution is the only ask." |

---

## 10. Entry Points and Recommended Sequencing

### Recommended first contact

**Target:** Takalani Netshitenzhe, Executive Director of External Affairs,
Vodacom South Africa — named in the NRS press release (2022) as the executive
responsible for disability inclusion. This is the most documented, most
appropriate first contact for a disability technology partnership.

**Alternative / fallback:** Stephen Chege, Chief Officer for Regulatory and
External Affairs (group level) — quoted at the 2025 Disability Conference.
Appropriate if a group-level conversation is more relevant than a SA-specific one.

**SAMRC bridge:** Bradley Carpenter — named speaker at the 2025 Disability
Conference. The bridge to SAMRC is documentable and specific.

### Recommended sequencing

1. **Before any outreach:** Engage Prof Tönsing (UP CAAC) for clinical credibility.
   Even a letter of support or informal endorsement from an established SA AAC
   researcher changes the quality of the opening conversation with Vodacom.

2. **First Vodacom contact:** Email to Takalani Netshitenzhe. Subject: acquired
   communication disability + ConnectU zero-rating. Short, specific, documented.
   The ask is zero-rating — the lowest-friction, most concrete first step.

3. **After zero-rating is in conversation:** Raise SAMRC bridge. Frame as
   "the research validation that would make this reportable."

4. **After clinical partner is engaged:** Pilot deployment proposal.

5. **Parallel track:** PhD registration. The research programme strengthens
   every subsequent conversation with Vodacom because it converts a goodwill
   ask into a formal research partnership with academic outputs.

### What not to do

- Do not send an email asking for money before Level 1 (zero-rating) has been
  discussed. The ask must be framed as infrastructure, not funding, for the
  first contact.
- Do not claim clinical validation before Prof Tönsing (or equivalent) is on
  board.
- Do not frame this as Vodacom Foundation initially — the Foundation's current
  programme areas are education and GBV. The commercial/ESG argument lands
  better with External Affairs and Corporate Affairs first.
- Do not send before there is a published or near-published academic output
  to reference. A short paper (even a conference paper) that can be cited
  transforms the conversation from "promising project" to "documented
  contribution."

---

## 11. The One-Paragraph Version (for verbal pitches)

> "South Africa has hundreds of thousands of stroke survivors who can hear
> and read perfectly, but cannot speak. Vodacom's disability programme serves
> the Deaf, the visually impaired, and seniors — but not them. We've built the
> first Afrikaans AAC system in existence: free, open-source, runs offline on a
> commodity Android tablet, and is already being used every day by one person
> who would otherwise have no voice. The specific ask to Vodacom is narrow: zero-
> rate the app on ConnectU so that any Afrikaans-speaking aphasia user on a
> Vodacom SIM can access it without spending data. That costs Vodacom nothing
> to implement, uses infrastructure that already exists, and closes a gap that
> the UN's own disability report identified at your 2025 conference."

---

## 12. Sources and Evidence Base

All claims about Vodacom sourced from documented press releases and product
pages — see `notes/vodacom-aac-research.md` and
`notes/vodafone-group-aac-research.md` for full references.

All clinical claims sourced from full-text MKVs in `literature/mkv/` — see
`notes/literature-review-aphasia-aac.md` and
`notes/why-stored-message-not-keyboard.md` for detailed citations.

Key sources:

| Claim | Source |
|---|---|
| One-third of stroke survivors develop aphasia | Brady et al. 2021, *Stroke* (PMC:read) |
| Up to 40% have chronic severe impairment | Beukelman & Light 2020, Ch. 15 (MKV:read) |
| No Afrikaans adult AAC vocabulary set | Hattingh et al. 2020 (MKV:read) |
| SA SLT access gap; customisation imperative | Odendaal & Tönsing 2024 (MKV:read) |
| Vodacom disability portfolio (NRS, Specific Needs) | Vodacom press release, 18 Nov 2022 |
| Vodacom 2025 Disability Conference speakers + quotes | Vodacom press release, 1 Jul 2025 |
| SAMRC at 2025 conference | Vodacom press release, 1 Jul 2025 |
| Vodacom Foundation focus: education + GBV | vodacom.com/vodacom-foundation.php |
| ConnectU zero-rating for health services | vodacom-aac-research.md §4.2 |
| MTN disability work (comparator) | vodacom-aac-research.md §7 |
