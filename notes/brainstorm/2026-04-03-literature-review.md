# Literature Review: AAC for Post-Stroke Aphasia

**Date:** 2026-04-03
**Purpose:** Inform the design of a custom Afrikaans AAC app for an elderly post-stroke man with intact comprehension and limited fine motor control.

---

## 1. What is Aphasia and Why AAC

**Aphasia** is an acquired communication disorder resulting from brain damage — most commonly stroke. It affects the ability to speak, understand, read, and write. Crucially, it does not affect intelligence. The person with aphasia (PWA) still thinks, feels, and understands — they simply cannot reliably produce language.

Post-stroke aphasia affects approximately 30–40% of stroke survivors. It is one of the most devastating consequences of stroke because it strips social identity and independence.

**AAC (Augmentative and Alternative Communication)** supplements or replaces speech for people who cannot rely on natural voice. For aphasia, AAC typically takes the form of:

- **Low-tech:** printed communication boards, picture books, laminated phrase cards
- **High-tech:** dedicated speech-generating devices (SGDs) or tablet apps that produce synthesised or pre-recorded speech when symbols/phrases are selected

Key clinical finding (ASHA, Archives of PMR 2023): AAC is underused in aphasia rehabilitation due to clinician misconceptions. Many clinicians wrongly believe AAC prevents natural speech recovery — the evidence says the opposite. AAC use does not suppress recovery; it supports it.

---

## 2. Core Vocabulary: What Do People Most Need to Say?

### 2.1 The 80/20 Rule

Research consistently shows that approximately **200 words account for 80% of all spoken language** (Beukelman & Mirenda, 2013). These are called **core vocabulary** — small, high-frequency words used across all contexts: *I, want, need, help, yes, no, more, stop, go, like, don't, good, bad, feel, hurt, eat, drink, tired, hot, cold, please, thank you*.

**Fringe vocabulary** covers specific, personal words: names of family members, specific foods, specific places, specific activities. These are unique to each person.

### 2.2 What Aphasia Patients Most Need to Communicate (Clinical Consensus)

The clinical literature (Lingraphica SmallTalk, TouchChat Communication Journey: Aphasia, Barkley/Munroe AAC Centers, Cboard) converges on these communication priorities for adults with aphasia:

**Tier 1 — Immediate physical needs (most urgent, must be one tap):**
- Pain — general and body-specific (head, stomach, chest, arm, leg, back)
- Hunger and thirst
- Toilet/bathroom
- Hot/cold
- Tired / want to rest
- Help / call someone
- Emergency

**Tier 2 — Yes/No/Basic responses:**
- Yes / No / Maybe / I don't know
- I understand / I don't understand
- Good / Bad / OK

**Tier 3 — Social and emotional:**
- Greetings: hello, goodbye, good morning, good night
- Feelings: happy, sad, worried, frustrated, scared, bored, comfortable
- Thank you / please
- Wait a moment

**Tier 4 — Communication repair (often neglected, very important):**
- "Say that again"
- "I don't understand"
- "Write it down"
- "Slow down"
- "That's not what I meant"
- "I know what I want to say but can't"

**Tier 5 — Daily life and activities:**
- Food and drink preferences
- Activities (TV, music, outside, bed)
- People (call family members by name)
- Time (now, later, today, tomorrow, morning, night)

**Tier 6 — Situational:**
- Doctor / medical context
- Community (shop, pharmacy) — lower priority for home-based user

### 2.3 The Lingraphica SmallTalk Minimum Viable Set

Lingraphica SmallTalk Aphasia — the most widely used dedicated aphasia app — defines a minimum viable phrase set in 8 categories:

1. Stroke (context-setting: "I had a stroke", "I can't speak but I understand you")
2. Conversation (greetings, social phrases)
3. Phone
4. Emergency
5. Meals
6. Restaurants
7. Health
8. Pain scale (Wong-Baker Faces)

For a home-based user, categories 3, 6, and 7 are lower priority initially.

### 2.4 The "I had a stroke" Opener

A clinically important phrase type often overlooked: **context-setting phrases** that explain the person's condition to strangers or new caregivers:

- "I had a stroke / brain blockage"
- "I cannot speak but I understand you"
- "Please be patient with me"
- "Please speak slowly"
- "Point to what you mean"

These dramatically reduce communication breakdowns with people who don't know the person.

---

## 3. Interface Design: What the Research Says

### 3.1 Button Size

This is the most critical design variable for a user with motor impairment.

**Research summary (W3C Mobile Accessibility Task Force, Chen et al. 2013, Duff et al. 2010):**

| Group | Minimum recommended button size |
| --- | --- |
| Non-disabled adults | 20mm × 20mm |
| Motor impairment | 20–30mm (performance continues improving up to 30mm) |
| Older adults | 20mm minimum; wider is better |

**Key finding (Chen et al., Applied Ergonomics, 2013):**
> "Performance for the non-disabled group plateaued at button size 20mm, with minimal gains at larger sizes. In comparison, the disabled group's performance continued to improve as button size increased."

**Post-stroke upper-limb impairment specifically:** No study directly measuring optimal touch target size for post-stroke elderly tablet users was found. Chen et al. (2013) included participants with various motor impairments but does not report a post-stroke subgroup. Barros et al. (2014, *Procedia Computer Science*) examined elderly mobile UI and found that users 65+ benefit from targets ≥ 25mm, consistent with the general motor-impairment literature. The absence of post-stroke specific data means **Chen et al.'s 25–30mm recommendation is the best available evidence** and remains in force. No upward revision is supported by evidence; no evidence contradicts the 30mm upper bound for a 3×3 grid.

**For our user:** Buttons should be **at least 20mm × 20mm**, ideally 25–30mm. On a 10-inch tablet (usable landscape area approximately 210mm × 130mm, minus system bars), a **3×3 grid of 9 buttons at 25–30mm each fits comfortably** with 3mm gaps. A 3×4 grid (12 buttons) is possible at 25mm but leaves little margin. Portrait orientation gives more vertical room but less width — landscape is preferred for grid layouts.

Button spacing: minimum 3mm gap between buttons to reduce adjacent errors.

### 3.2 Grid Density

**Research finding (Light et al., AAC 2019):** For adults with acquired conditions (stroke, TBI), grid displays work well with text labels. The number of items per page matters significantly — too many items increases visual search time and error rates.

**Clinical recommendations:**
- **4–6 items per page:** Very simple navigation, best for severe motor impairment
- **9–12 items per page:** Standard for moderate impairment
- **15–20 items per page:** Only for users with good motor control and literacy

**For our user:** 9 buttons per screen (3×3 grid) for the category home screen, 9–12 for phrase sub-screens.

### 3.3 Navigation Depth

**Clinical consensus:** Maximum **2 taps** to any phrase. Three-level hierarchies cause confusion and abandonment, especially in emotionally heightened moments (pain, urgency).

Structure: **Home → Category → Phrase** (2 taps).

Exception: Tier 1 needs (pain, call for help, emergency) should be **0 taps** — always visible on every screen, not behind a category.

### 3.4 Visual Design

**Text vs. symbols+text:**
- Adults with aphasia who retain reading comprehension generally perform equally well or better with **text-only** labels (Hux et al., 2001)
- Symbols help users with reading impairment, but add visual complexity
- **Decision for our user:** Text-only initially (he can do word puzzles — reading is intact). Can add images later if needed.

**Font size:** Minimum 18pt for AAC labels; 24pt+ preferred for elderly users.

**Colour coding of categories:** Supported by research as reducing visual search time. Standard Minspeak/LAMP colour conventions (but not required for a simple phrase board — consistent colours per category is sufficient).

**Contrast:** High contrast essential. White text on dark category colour, or dark text on light background. Avoid grey-on-grey.

**Background colour:** Research (Light et al., 2019) found background colour does NOT improve symbol search and may distract. Use it for category identification only, not decoration.

### 3.5 Why AAC Apps Fail (Abandonment Reasons)

Literature on AAC abandonment (Light & McNaughton, 2012; Baxter et al., 2012):

1. **Too complex to navigate** — too many levels, too many buttons per page
2. **Vocabulary doesn't match the person's actual needs** — generic vocabulary that doesn't reflect their life, relationships, and priorities
3. **Caregiver/family not trained** — device is used but communication partners don't know how to respond or model
4. **Too slow** — too many taps required for urgent needs
5. **Embarrassment** — device draws attention; less of an issue at home
6. **Device not available when needed** — must be on the table, not in a drawer

**Design implication:** Keep it simple. Fewer well-chosen phrases beats a comprehensive but overwhelming vocabulary. The first version should have the 30–40 most important phrases only.

### 3.6 The Emergency Button

Clinical standard: AAC systems for adults living with reduced independence must include an always-accessible emergency mechanism. This is not a category — it is a persistent control visible on every screen.

For a home-based user living with a spouse, this means: **one button that calls the caregiver**, always visible, always in the same position (top-right or bottom-right — position must never change).

---

## 4. Display Type: Grid vs. Visual Scene

**Grid displays** (buttons with labels) — best for users with good literacy and category understanding. Efficient for practiced users. What we are building.

**Visual Scene Displays (VSDs)** (photographs with hotspots) — better for users with reading impairment or who respond better to visual/contextual cues. More effort to build.

**For our user:** Grid display is appropriate (intact reading comprehension, word puzzle capability). VSDs could be considered for specific high-use scenarios (e.g., a photo of the kitchen with hotspots for "water", "food", "coffee") but not required for v1.

---

## 5. Afrikaans AAC — State of the Field

### 5.1 Summary

Afrikaans AAC is an emerging but underdeveloped field. No commercial Afrikaans AAC app exists for post-stroke elderly adults. This is essentially a blank slate.

### 5.2 What Exists

**SASLHA Free Communication Boards (October 2025):**
Prof Juan Bornman and Gert Koekemoer (Stellenbosch University) produced three Tobii Dynavox communication boards in English, Afrikaans, and isiXhosa:
- Medical Context Board (most relevant for us)
- Preschool Board
- School Board

Available free from saslha.co.za/communication-boards. The Medical Context Board contains Afrikaans phrases for medical emergencies and consultations — directly relevant.

**Tobii Dynavox / Stellenbosch Afrikaans Symbol Set (2025):**
First culturally adapted Afrikaans AAC symbol set, completed by Prof Bornman and Monique Visser. Not yet publicly released; sits within the Tobii Dynavox commercial platform. Culturally adapted to include SA-specific symbols (Table Mountain, Springbok, melktert, koeksister, rand, SA taxi).

**Afrikaans Core Vocabulary Research (University of Pretoria CAAC):**
Hattingh & Tönsing (2020, SAJCD) identified 239 core Afrikaans words from child speech samples, accounting for 79.4% of all speech. Published open-access. Important caveat: derived from preschool children — no adult Afrikaans core vocabulary study exists yet.

Winter et al. (2025, Folia Phoniatrica et Logopaedica, DOI: 10.1159/000546919) published a secondary analysis extending this work — but also using preschool Afrikaans-speaking children. Confirms and extends Hattingh & Tönsing; does not close the adult vocabulary gap.

**South African post-stroke AAC research:**
Odendaal, I. & Tönsing, K.M. (2024, *Augmentative and Alternative Communication*, 41(1), 56–64) is a peer-reviewed journal article based on Odendaal's 2022 UP Master's dissertation. The full dissertation has been obtained (see `references/papers/odendaal-2022-sa-slts-aac-aphasia-dissertation.pdf`, 150 pages).

**Study design:** Qualitative phenomenological study. 10 South African SLTs with ≥10 years of experience working with post-stroke aphasia, interviewed using open-ended questions. Thematic analysis (Fereday & Muir-Cochrane, 2006). Synthesised member checking. First study to explore SA SLTs' perspectives on AAC for this population.

**Key findings — directly relevant to our design:**

*Communication partner is the critical factor for AAC success:*

- All 10 participants agreed that the communication partner is "an integral component of the success of AAC" (p.68)
- Eight participants: the partner must be willing to "make an effort to support the person with aphasia, facilitate interactions and compensate for the person with aphasia's difficulty in initiating" (p.68)
- "The ultimate key to success in the implementation of AAC for persons with post-stroke aphasia is the involvement of the communication partner" — 8/10 participants (p.87–88)
- Partners need training on: the diagnosis of aphasia, that the person with aphasia retains competence, strategies to assist, and involving the person with aphasia in conversations (p.69)
- Partners who talk for the person with aphasia limit their opportunities to generalise — explicitly named as a harmful behaviour (p.69)
- Pre-morbid relationship quality is a strong predictor of AAC success (p.69)

*Personalisation is mandatory — generic systems do not work:*

- "All participants agreed that generic systems do not work for persons with post-stroke aphasia but that systems need to be personalised to be beneficial to them" (p.66)
- "The more buy-in you get from the family, and the communication partner in assisting you in developing this device, the more likely they [persons with aphasia] are to use it" [P3] (p.67)
- Language, age, culture, gender, voice output appropriateness all matter for system selection (p.66)

*Consistency of use drives improvement:*

- "Persons with post-stroke aphasia need to use AAC consistently to ensure carryover and improve their communicative abilities" (p.87)
- "Successful communication attempts lead to more regular use" — virtuous cycle confirmed (p.87)

*AAC abandonment is common:*

- 9/10 participants reported that AAC is "abandoned regularly" — left in a drawer when the SLT is not present (p.81)
- Key abandonment driver: no communication partner to drive use at home (p.81)
- "The communication partner is as much of a ramp or a crutch as an eyegaze device is for someone with motor neuron disease" [P3] (p.88)

*South African context barriers (directly relevant):*

- No government tender for AAC devices (policy section p.76)
- Medical aids do not cover AAC (9/10 participants) (p.77)
- SLT distribution skewed to private sector, urban areas (p.28)
- "There is absolutely nothing around the communication plan... There is nothing around communication accessibility" [P9] (p.77)
- Most scientific evidence is Western and "not applicable to the South African context" [P5] (p.78)
- Only 39 SLTs per million population (2017 estimate); only 217/782 registered SLTs have special interest in aphasia (p.27)

*Practical implications for our app:*

- Tablet/smartphone ownership makes high-tech AAC more accessible in SA (5 participants noted this) (p.67)
- "Be careful not to introduce something they are not going to be able to take home or purchase or access" — offline, free solution is the right approach [P4] (p.67)
- Consistent daily use in real-life situations is what predicts success — morning check-in routine and pre-meal usage directly supported (p.87)
- Context-setting phrases ("I had a stroke, I understand you") are important for strangers and visitors — confirmed by SA SLTs (see p.70 reference to partner education)

**University of Pretoria CAAC:**
Oldest AAC research centre in SA (est. 1990). Has an AAC Resource Manual and downloadable resources at up.ac.za/centre-for-augmentative-alternative-communication.

### 5.3 What Does Not Exist

- No Afrikaans-specific AAC app for adults with aphasia
- No adult Afrikaans core vocabulary list (only children's) — Hattingh & Tönsing (2020) and Winter et al. (2025) both use preschool children; gap explicitly confirmed
- No validated Afrikaans AAC phrase bank for post-stroke patients
- No Afrikaans text-to-speech voice in any open-source offline TTS engine (eSpeak NG has Afrikaans but quality is poor)

### 5.4 TTS for Afrikaans

**Microsoft Edge TTS** (`af-ZA-WillemNeural`, `af-ZA-AdriNeural`) — confirmed good quality in testing. Free, no API key required, online generation. Pre-generating audio files eliminates the online dependency at runtime.

---

## 6. Implications for Our Design

### 6.1 Phrase priority (what to build first)

| Priority | Category (Afrikaans) | Notes |
| --- | --- | --- |
| Always visible | Noodgeval / Roep [Mom] | Never behind a category — always on screen |
| Tier 1 | Ja / Nee / Ek weet nie | One tap, always quick |
| Tier 1 | Ek het pyn + body part | Pain is the most urgent communication need |
| Tier 1 | Ek is honger / dors / moeg / koud / warm | Physical needs |
| Tier 1 | Ek moet toilet toe | |
| Tier 2 | Voel (feelings) | Happy, sad, worried, scared, bored |
| Tier 2 | Roep iemand | Family names |
| Tier 3 | Praat met my (communication repair) | "Sê dit weer", "Skryf dit neer" |
| Tier 3 | Aktiwiteite | TV, music, outside |
| Tier 4 | Ek het 'n beroerte gehad / Ek kan nie praat nie | For use with visitors/strangers |

### 6.2 UI specifications derived from research

| Parameter | Value | Source |
| --- | --- | --- |
| Min button size | 20mm × 20mm | Chen et al. 2013 |
| Recommended button size | 25–30mm | Chen et al. 2013 |
| Buttons per home screen | 9 (3×3) | Clinical consensus |
| Buttons per phrase screen | 9–12 | Clinical consensus |
| Max navigation depth | 2 taps | Clinical consensus |
| Emergency button | Always visible, fixed position | Clinical standard |
| Font size | ≥24pt for labels | Elderly user guideline |
| Display type | Text-only grid | Intact reading comprehension |
| Colour coding | Per category (for visual search) | Light et al. 2019 |

### 6.3 What we should do before building v1

1. **Download and review the SASLHA Afrikaans Medical Context Board** — extract Afrikaans phrases that are directly usable
2. **Get phrase input from Mom** — what does Dad try to communicate that he can't? This populates the fringe vocabulary
3. **Keep v1 small** — 30–40 phrases maximum; expand after testing with Dad
4. **Add "context-setting" phrases** — "Ek het 'n beroerte gehad. Ek kan nie praat nie, maar ek verstaan alles." This is important for visitors

---

## 7. References

- Beukelman, D.R. & Mirenda, P. (2013). *Augmentative and Alternative Communication: Supporting Children and Adults with Complex Communication Needs* (4th ed.). Paul H. Brookes.
- Chen, K.B., Savage, A.B., Chourasia, A.O., Wiegmann, D.A., & Sesto, M.E. (2013). Touch screen performance by individuals with and without motor control disabilities. *Applied Ergonomics*, 44(2), 297–302.
- Hattingh, D. & Tönsing, K.M. (2020). The core vocabulary of South African Afrikaans-speaking Grade R learners without disabilities. *South African Journal of Communication Disorders*, 67(1). DOI: 10.4102/sajcd.v67i1.701
- Light, J., Wilkinson, K.M., Thiessen, A., Beukelman, D.R., & Fager, S.K. (2019). Designing effective AAC displays for individuals with developmental or acquired disabilities. *Augmentative and Alternative Communication*, 35(1), 42–55. PMC6436972.
- Odendaal, I. et al. (2024). Augmentative and alternative communication for individuals with post-stroke aphasia: perspectives of South African speech-language pathologists. *Augmentative and Alternative Communication*, 40(3). DOI: 10.1080/07434618.2024.2374303.
- W3C Mobile Accessibility Task Force. Summary of Research on Touch/Pointer Target Size. w3.org/WAI/GL/mobile-a11y-tf/wiki/Summary_of_Research_on_Touch/Pointer_Target_Size
- Lingraphica SmallTalk Aphasia app category structure (lingraphica.com)
- SASLHA Communication Boards — Bornman & Koekemoer, Stellenbosch University (saslha.co.za/communication-boards, October 2025)
