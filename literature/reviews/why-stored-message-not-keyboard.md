# Why Stored-Message AAC and Not a Keyboard?

## A Literature-Grounded Analysis for Post-Stroke Aphasia Interface Design

**Date:** 2026-04-05
**Author:** Johannes Foulds
**Purpose:** Academic synthesis of the clinical and neurolinguistic rationale for
stored-message AAC over open-ended text-entry as the primary communication mode for
a post-stroke Afrikaans-speaking user with aphasia, intact comprehension, and literacy.
**Sources:** All claims drawn from full-text MKVs in `literature/mkv/` — verified in
this session against quotable passages. Online sources retrieved and converted to MKV
using Mistral OCR for this document.

---

## 1. Introduction

A natural question when designing an AAC system for a person with post-stroke aphasia
who retains both literacy and intact comprehension is: why not simply provide a
keyboard and allow free-form text entry? A keyboard offers unlimited expressive range,
imposes no vocabulary ceiling, and eliminates the ongoing labour of message
pre-programming. For a literate user who can read and understand everything addressed
to him, a text-input interface appears to be the most direct solution.

This review argues that this intuition, while understandable, rests on a
misidentification of the primary impairment. Stroke-induced aphasia is not a disorder
of motor speech execution alone, nor of physical access; it is a disorder of the
language production system itself. @huang-2021-aac-inpatient-rct define it precisely:
post-stroke aphasia "is defined as an impairment of the complex process of interpreting
and formulating language symbols affecting auditory comprehension, reading, and
oral-expressive language **and writing**." The writing impairment is not incidental — it
is definitional.

The consequences of that definition are determinative for interface design. A keyboard
demands exactly the linguistic operations that aphasia damages. Pre-stored messages,
by contrast, re-route communication through recognition and selection — processes that
are typically more preserved. This document synthesises the clinical literature to
explain why, and to characterise the conditions under which stored-message AAC is the
appropriate design choice for this specific user.

---

## 2. The Linguistic Architecture of Writing and Why Aphasia Disrupts It

### 2.1 Agraphia as a Neurological Co-Occurrence with Aphasia

Writing is not simply speech transcribed. It requires the successful activation of a
separate graphemic output pathway that is neurologically proximate to — and frequently
damaged alongside — the perisylvian language network affected in most left-hemisphere
strokes. @thiel-2016-functional-writing state this directly: "Dysgraphia frequently
occurs as one symptom of aphasia, an acquired multi-modal language disorder caused by
traumatic brain injury, brain tumour, surgery, infection, or most commonly, stroke."

@koul-2011-aac-aphasia (Ch. 2) define the relevant disorder:

> Agraphia (Greek: *a* = without + *graphein* = to write) is an acquired writing
> disorder in which the ability to write and spell (i.e., to produce graphemes) is
> impaired subsequent to a stroke or other brain damage. Agraphia can be divided into
> lexical (or surface agraphia) and phonological types. In lexical agraphia, an
> individual presents with impaired spelling characterized by "over-reliance on
> sound-to-letter conversions."... In phonological agraphia, affected individuals can
> write common words (including irregularly spelled words) but cannot spell nonwords.

@koul-2011-aac-aphasia further identifies agraphia as one of the standard
co-occurring disorders in aphasia, alongside dysarthria, apraxia of speech, alexia,
and agnosia:

> Aphasia is frequently associated with concomitant disorders affecting motor speech
> functions (e.g., dysarthria or apraxia of speech), sensory recognition (agnosia),
> reading (alexia), writing (agraphia), and swallowing ability (dysphagia).

The practical implication is immediate: for the majority of people with aphasia,
writing and spelling are not intact backup channels for speech. They are part of the
same damaged language system.

### 2.2 The Dysgraphia Subtypes and Their Functional Consequences

@thiel-2016-functional-writing document four discrete dysgraphia subtypes in a
cohort of eight participants with post-stroke aphasia, each with distinct functional
consequences for keyboard use:

**Surface dysgraphia** (damage to the orthographic lexicon): the user can apply
phoneme-to-grapheme rules but cannot retrieve irregular word forms. This produces
characteristic regularisation errors such as "serkle" for *circle*, "clok" for
*clock*, "speek" for *speak*, "elefant" for *elephant*. Every irregular word in
the target language becomes a potential spelling error.

**Deep dysgraphia** (damage to the semantic-to-orthographic pathway): the user
makes semantic errors in writing ("dish" for *spoon*, "post" for *letter*), cannot
write nonwords, and has specific difficulty with verbs — which are typically lower
imageability than nouns and therefore harder to retrieve orthographically. For
Afrikaans, a language with considerable irregular morphology, this systematically
affects the most communicatively important word classes.

**Phonological dysgraphia** (damage to the phoneme-to-grapheme conversion route):
the user cannot spell nonwords or unfamiliar words, and produces lexicality effects
(spelling a nonword as a similar-sounding stored word). In a post-stroke context,
many proper nouns, place names, and unfamiliar vocabulary become effectively
unspellable.

**Graphemic buffer disorder** (damage to the short-term holding mechanism for
orthographic sequences): the user produces addition, substitution, omission, and
transposition errors during word production — for example "stemp" for *stamp*,
"dace" for *dance* — and shows a marked length effect where longer words produce
more errors. Since the graphemic buffer must hold the entire intended word while it
is being written letter-by-letter, any increase in word length compounds the error
rate.

These subtypes are not mutually exclusive. @thiel-2016-functional-writing document
several participants with combined impairments (e.g., deep dysgraphia with
accompanying graphemic buffer disorder). The pattern confirms that the dysgraphic
impairment in aphasia is typically multifaceted and that no single route remains fully
intact as a reliable substitute for others.

### 2.3 Writing Complexity and Sensitivity to Brain Damage

@thiel-2017-email-writing explain why writing is disproportionately vulnerable:
"Writing is particularly sensitive to brain damage due to its inherent complexity in
incorporating linguistic, cognitive, perceptual and spatial processes." They further
distinguish between handwriting and keyboard-based typing: "Handwriting requires
knowledge of letter shapes and the grapho-motor skills to produce letters, whereas to
select letters on a keyboard visual recognition skills and spatio-motor are important."

This distinction is significant for AAC design. A keyboard is not simply easier than
handwriting for an aphasic user. While it removes the motor demand of letter
formation, it retains the full central linguistic burden of lexical retrieval,
phonological encoding, and orthographic sequencing. The bottleneck for users with
aphasia is not peripheral (motor, graphomotor) — it is central (linguistic). Switching
from pen to keyboard addresses the wrong level of the problem.

@huang-2021-aac-inpatient-rct confirm that writing impairment is not separable from
the broader aphasia presentation: "People with aphasia commonly experience different
levels of expressive language impairments, ranging from occasional word-finding
difficulties to severe verbal communication difficulties."

### 2.4 Lived Experience of Writing Impairment

@thiel-2022-writing-experiences conducted in-depth interviews with eight people with
post-stroke aphasia and writing difficulties and found that participants described
profound subjective distress at the gap between their literacy as readers and their
inability to produce written language:

> "I read them and I don't, I read them I can't I don't write them"
> "Sentences are completely different"
> "the spelling is so hard and also it's the pain in my life"

These first-person accounts confirm that the impairment is not merely a measurable
deficit on formal assessment — it is a daily lived experience of failure and
frustration that is distinct from, and often worse than, reading difficulty.
@thiel-2022-writing-experiences note that "participants felt negative about aspects
of their writing, including speed, accuracy and range of vocabulary."

The implications for design are direct. An interface that requires the user to compose
text from scratch — even with word prediction assistance — places him daily at the
site of his most frustrating functional impairment. Stored-message selection bypasses
this entirely.

---

## 3. Recognition as an Alternative Pathway

### 3.1 The Production/Recognition Distinction

The central design principle of stored-message AAC is the substitution of *recognition*
for *production*. When a user selects a pre-stored message, they perform a recognition
task: scanning a set of externally represented options and identifying one that matches
their communicative intent. Recognition does not require lexical retrieval,
phonological encoding, or orthographic sequence production. It requires only that the
stored form — whether word, phrase, photograph, or symbol — is sufficiently legible
and contextually presented to trigger identification.

The clinical evidence that recognition is substantially more preserved than production
in aphasia is robust. @beukelman-2020-aac (Ch. 15) reports:

> People with aphasia with minimal reading ability on formal tests were more than 90%
> accurate when responding to conversational questions by pointing to written choices,
> as long as the choices were presented within the context of a conversation and spoken
> aloud by the partner while he or she wrote them.

This finding is remarkable precisely because formal reading scores would predict
failure. The discrepancy between formal test performance and functional accuracy in
context demonstrates that the recognition pathway — supported by contextual cueing —
is far more intact than the production pathway tested by formal instruments. The
stored-message AAC paradigm exploits this preserved capacity directly.

### 3.2 AAC Reduces the Production Burden Rather Than Bypassing Language

@huang-2021-aac-inpatient-rct articulate the functional mechanism precisely:
"AACT may simultaneously strengthen communication by reducing the pressure to retrieve
target concepts using impaired language functions." This is not merely a compensatory
effect — it is a relief of cognitive load that can enable more reliable communication
in contexts where independent production fails entirely.

The clinical literature supports this framing strongly. @odendaal-2024-aac-aphasia-slp,
reporting on South African SLPs, found that participants "agreed that both restorative
and compensatory approaches are essential, and many use AAC from the outset with their
clients" — treating AAC not as a last resort but as an integral component of
rehabilitation from the beginning.

### 3.3 Literacy as an Enabling Factor, Not a Production Guarantee

A user who retains literacy — the ability to read words and phrases — occupies a
privileged position on the AAC continuum. @beukelman-2020-aac (Ch. 15) and
@lowis-2024-caya-aac-aphasia both identify reading ability at the word/phrase/sentence
level as the defining competence of stored-message communicators. Literacy enables
the user to navigate labelled displays without symbol-learning burdens and to select
messages whose text they can verify before activation.

However, literacy as a receptive/recognition skill is not equivalent to literacy as
a productive/generative skill. A person can reliably *read* a word without being able
to *spell* it under the dual load of aphasia. The thiel-2022 interviews confirm this
asymmetry: participants described being able to read text while being unable to
produce it: "I read them and I don't, I read them I can't I don't write them."

The preserved reading ability of the project participant supports stored-message AAC
precisely because it enables accurate recognition; it does not imply that keyboard
composition is viable.

---

## 4. The Stored-Message Communicator Profile

### 4.1 The Garrett–Lasker Classification Framework

@odendaal-2024-aac-aphasia-slp note that South African SLPs "in general... appeared to
follow the principles of Garrett and Lasker's functional classification framework
(Garrett et al. 2020), initially focusing on aspects such as unaided AAC (involving
no external tools or technology, e.g. gestures), low-tech AAC, and partner-supported
strategies. Once the person with aphasia is open to alternative forms of communication,
they introduce more comprehensive AAC systems."

The Garrett–Lasker framework, as synthesised in @beukelman-2020-aac (Ch. 15), defines
six communicator levels: Emerging, Contextual Choice, Transitional, Stored-Message,
Generative, and Specific-Need. Each level is defined by what the user can do
independently, not what they cannot do.

### 4.2 The Stored-Message Communicator Definition

@beukelman-2020-aac (Ch. 15) define stored-message communicators as follows:

> Stored-message AAC communicators can learn to independently locate messages that
> have been stored in advance within their low- or high-tech AAC systems, even if they
> cannot generate these messages independently via spelling, combining symbols,
> writing, or speaking. They have enough executive function and initiation ability to
> learn to consistently access entire phrase or sentence messages in specific contexts.

The distinguishing feature of this communicator category — in contrast to the
transitional communicator below it on the continuum — is *partner-independent
initiation*: stored-message AAC communicators "can learn to initiate and use their
systems to supplement or substitute for speech without prompting within familiar
situations" [@beukelman-2020-aac, Ch. 15].

The participant in this project maps directly to this profile: intact comprehension,
literacy at the word/phrase/sentence level, and the executive capacity to navigate
a familiar display without requiring a partner to curate options on a turn-by-turn
basis. His communication is not partner-dependent in the clinical sense; the system
must support *his own* initiation.

### 4.3 The Customisation Imperative

@odendaal-2024-aac-aphasia-slp report a consistent finding across their South African
SLP participants: "Many noted that generic systems do not work for this population and
that AAC systems must be highly personalized to benefit them." One participant stated:
"AAC... should always be as meaningful as possible to that person. Sometimes, with
these kinds of generic systems... it is not set up in a way that that person [with
post-stroke aphasia] relates to it."

This is a critical constraint for keyboard-centric design as well as for stored-message
design. A keyboard provides unlimited expressive range, but the range is inaccessible
to the user because the production system is impaired. A stored-message system
provides finite range, but if the vocabulary is correctly mapped to the user's
communicative ecology, the accessible range within that system meets the user's actual
daily needs. The design obligation is to build the vocabulary set around this specific
user — his daily routines, family relationships, recurring topics, healthcare needs,
and preferences.

### 4.4 The Communication Partner as Design Variable

@odendaal-2024-aac-aphasia-slp document a theme that emerged across all ten SLP
participants: the essential role of the communication partner. One participant
described it in terms that are particularly relevant to home-based AAC:

> "You need that golden thread of the communication partner... The communication
> partner... is as much of a ramp or a crutch as an eye gaze device is for someone
> with motor neuron disease... The golden thread is the person who is facilitating it.
> If you do not have that, then your aphasic patient... will struggle to be an
> independent user of the AAC device, and that is not anybody's fault. It's the
> nature of the injury."

This observation applies differentially to stored-message vs. keyboard design. A
keyboard interface that fails communicatively creates a barrier at the point of
language production — the user cannot get past the first step. A stored-message system
that is well-designed allows the partner to respond to complete, verified messages
and then scaffold further communication. The partner's role is facilitative rather
than substitutive.

---

## 5. Empirical Evidence for AAC in Post-Stroke Aphasia

### 5.1 AAC Effectiveness Across Communication Domains

@huang-2021-aac-inpatient-rct designed a randomised controlled trial of AAC
intervention for in-patient post-stroke aphasia specifically to evaluate "the
effectiveness and feasibility of including AACT in regular SLT." Their intervention
used "a paper-made communication board... includ[ing] 45 pictures relating to basic
needs, emotional expression, medical conditions, and daily activities" — a classic
stored-message, category-based design directly analogous to the artefact under
discussion. The primary outcomes included communication of basic needs, overall
language performance, and quality of life. The stored-message design was specifically
chosen because the participants had "moderate to severe aphasia" — a level where
generative text production is not reliably accessible.

@formica-2024-aac-brain-injury report a case series of three adults with severe
acquired brain injury who received AAC rehabilitation. Case 1 — a 71-year-old man
with ischemic stroke — presented a profile directly parallel to the project user:
"Writing capabilities were also damaged but verbal comprehension was preserved... His
communication was based on the patient's selection and choice of images shown on the
computer screen." The selection-and-recognition model succeeded precisely where
production-dependent alternatives had failed.

### 5.2 AAC Does Not Impede Speech Recovery

A concern sometimes raised by users and families is that AAC use may substitute for
natural speech recovery and thereby reduce motivation to regain oral language. The
evidence directly contradicts this. @huang-2021-aac-inpatient-rct note that
"previous studies have reported that people with aphasia and their families often
reject to adopt AAC strategies with the fear that AAC may interfere with or impede
the restoration of their natural language system. However, studies have shown that
AACT may simultaneously strengthen communication by reducing the pressure to retrieve
target concepts using impaired language functions."

@odendaal-2024-aac-aphasia-slp confirm that South African SLPs "agreed that both
restorative and compensatory approaches are essential" — AAC is integrated with, not
opposed to, speech therapy. @tobii-aphasia-therapy-guide states that AAC is
appropriate "any time post their onset, at any level of language impairment," and
that "using AAC will not hinder PWA's ability to regain speech."

### 5.3 Vocabulary Scope: Real Needs Are Finite and Known

The stored-message approach has an acknowledged limitation: communication is bounded
by what has been programmed. This limitation is real but manageable. The vocabulary
for a single user's daily communicative ecology is finite and largely predictable
[@beukelman-2020-aac, Ch. 15; @odendaal-2024-aac-aphasia-slp]. The failure mode of
stored-message AAC is vocabulary mismatch — messages programmed that do not match the
user's actual communicative situations — not vocabulary finitude per se.

@odendaal-2024-aac-aphasia-slp document that South African SLPs specifically
highlighted "the involvement of the person with post-stroke aphasia and their
communication partner in personalizing AAC devices" as a key facilitator of success.
The design obligation this creates — building the vocabulary around this user's
actual life — does not invalidate the stored-message model; it defines the minimum
requirements for implementing it correctly.

---

## 6. The Keyboard Case and Why It Fails for This User

A keyboard-centric design — whether a virtual on-screen keyboard, a physical
keyboard, or a letter-by-letter text entry field — requires the following sequential
operations to produce a single complete message:

1. **Communicative intent** — the user must formulate what they want to say.
2. **Lexical retrieval** — the user must identify the target words from the mental
   lexicon. Anomia (word-finding difficulty) is among the most universal symptoms
   across all aphasia types [@koul-2011-aac-aphasia, Ch. 2].
3. **Phonological encoding** — the user must retrieve the phonological form of each
   word to map it to its spelling. In phonological agraphia this route is specifically
   damaged [@thiel-2016-functional-writing; @koul-2011-aac-aphasia, Ch. 2].
4. **Orthographic retrieval** — the user must access the stored letter sequence for
   each word. In lexical/surface agraphia this route is damaged, producing
   phonologically plausible but orthographically incorrect spellings
   [@thiel-2016-functional-writing].
5. **Graphemic buffer maintenance** — the user must hold the intended word in
   orthographic working memory while executing the letter-by-letter sequence.
   Graphemic buffer disorder produces errors that scale with word length
   [@thiel-2016-functional-writing; @thiel-2017-email-writing].
6. **Sequential motor output** — the user must activate the correct key for each
   letter in the correct order. Even where linguistic retrieval succeeds, motor
   sequencing errors can disrupt the output.
7. **Syntactic formulation** — for sentence-length messages the user must construct
   grammatical sequences, which requires working memory for phrase structure and
   morphological agreement.

Any single failure in steps 2–7 produces either an incorrect message or no message
at all. In moderate to severe aphasia, failures are not occasional exceptions — they
are the norm. @thiel-2022-writing-experiences document participants who could not
complete email writing despite sustained effort: "the spelling is so hard and also
it's the pain in my life."

Contrast this with the stored-message selection task:

1. The user browses displayed options.
2. The user recognises a message that matches their intent.
3. The user taps the button.
4. The message is spoken aloud.

Steps 2–7 of the keyboard pathway collapse to a single recognition step. No lexical
retrieval is required because the word is displayed. No phonological encoding is
required because there is no spelling. No orthographic sequencing is required. No
graphemic buffer is loaded. The recognition pathway, which @beukelman-2020-aac (Ch.
15) demonstrates achieves over 90% accuracy even in users with near-zero formal
reading scores, handles the entire communicative transaction.

@pierce-2019-multimodal-therapy, in their systematic scoping review of multimodal
aphasia treatment, identify two key dimensions of multimodal interventions: whether
the aim is to "improve total communication, as in Augmentative and Alternative
Communication approaches," or to improve a single modality. AAC approaches for aphasia
explicitly prioritise total communication over single-modality output — recognising
that the user needs to communicate, not to perform a specific linguistic sub-skill.
A keyboard-only interface implicitly prioritises written production as the communication
channel, which is precisely the most impaired modality.

---

## 7. Display Design: Large Targets and Low Symbol Density

### 7.1 Cognitive Constraints Specific to Aphasia

Even where the linguistic argument is accepted, the question of display design
remains. The optimal stored-message interface for a person with aphasia is not merely
any pre-programmed system; it is one whose physical and cognitive access demands match
the user's profile.

@beukelman-2020-aac (Ch. 15, citing Petroi, Koul & Corwin, 2014) establishes that
"people with aphasia identify symbols within an AAC device most readily when fewer
symbols per screen are displayed and when minimal navigation is required." Working
memory load is the critical constraint: multi-step navigation requires the user to
hold both the current navigation state and the intended message simultaneously.
@beukelman-2020-aac notes that "arranging messages in AAC systems with multiple
displays... may impose significant processing challenges for many people with aphasia
who demonstrate problems recalling the location of stored messages and symbols."

Large targets on low-density displays reduce the number of navigation steps and the
working memory load associated with each step.

### 7.2 Motor Access and Technology Familiarity

@koul-2011-aac-aphasia (Ch. 2) notes that limb apraxia frequently co-occurs with
anterior aphasia syndromes and "can interfere with pointing, gesturing, and device
operation." For the project participant, mild post-stroke upper-extremity impairment
independently motivates large-button design: keyboard use requires precise individual
key activation across a dense array of small targets, substantially more demanding of
fine motor precision than large-button touchscreen activation.

The participant has never used a smartphone or tablet in regular daily life. The
gestural grammar of touchscreen interfaces — swipe, scroll, pinch, tap — must be
treated as an acquired skill, not a baseline assumption. Large, clearly labelled,
single-purpose targets minimise the interface learning curve: one action (tap) maps to
one communicative output (message played aloud). This design principle applies
independently of the linguistic argument.

---

## 8. Synthesis: Why the Current Design Is Appropriate

The stored-message, large-button AAC design for this user rests on a convergence of
four independent lines of argument, each individually sufficient and mutually
reinforcing:

**1. The primary impairment is linguistic and includes writing.**
Post-stroke aphasia is formally defined as including impairment of writing alongside
speech, reading, and comprehension [@huang-2021-aac-inpatient-rct]. Dysgraphia
co-occurs with aphasia as the expected, not exceptional, clinical presentation
[@thiel-2016-functional-writing]. Its four subtypes — surface, phonological, deep, and
graphemic buffer — each independently disrupt different components of the keyboard
production pathway. A keyboard interface does not bypass the impairment; it places
the user directly in the most impaired pathway.

**2. Recognition is more preserved than production.**
The user's intact comprehension and literacy are assets for *recognising and selecting*
pre-stored messages, not for *generating* them from scratch. People with aphasia have
demonstrated over 90% accuracy in selecting from written choices in context, despite
near-zero formal reading scores [@beukelman-2020-aac, Ch. 15]. The stored-message
paradigm routes communication through the more preserved pathway. AAC "reduces the
pressure to retrieve target concepts using impaired language functions"
[@huang-2021-aac-inpatient-rct].

**3. The user's communicator profile fits the stored-message category.**
Partner-independent initiation, literacy at word/phrase/sentence level, intact
comprehension, and sufficient executive function to navigate a familiar display are
the defining characteristics of stored-message communicators [@beukelman-2020-aac,
Ch. 15]. The stored-message level is not a compromise — it is the correct functional
classification for this user. A keyboard-first design would target the generative
level, which sits above his current functional profile. South African SLPs consistently
follow the Garrett–Lasker framework in making exactly this determination
[@odendaal-2024-aac-aphasia-slp].

**4. Physical and experiential access factors independently require large targets.**
Mild post-stroke fine motor impairment and zero prior touchscreen experience both
independently favour a large-button, low-density display. Evidence from display density
research confirms that aphasia-specific cognitive constraints (working memory,
navigation load) converge with these motor and experiential factors to make
low-density, minimal-navigation displays the empirically supported choice
[@beukelman-2020-aac, Ch. 15].

---

## 9. Conclusion

The stored-message AAC design for this user is not a concession to disability or a
reduction in communicative ambition. It is the correct design for the correct user
profile, grounded in the neurolinguistic literature on post-stroke aphasia and the
clinical evidence base for AAC in this population.

The keyboard-centric alternative is not more ambitious — it is less effective. It
places the user inside the impaired production system and makes successful communication
contingent on operations that aphasia has damaged. The stored-message model places
communication inside the preserved recognition system and makes successful communication
contingent on operations — reading, recognising, tapping — that are substantially
intact.

The design obligation that follows is not to defend this choice but to implement it
correctly: vocabulary that reflects the user's actual communicative ecology, buttons
large enough for reliable touchscreen activation, navigation shallow enough to impose
minimal working memory load, and a partner who understands their facilitative role.
These are the conditions for success. They are achievable. A keyboard is not.

---

## 10. Sources Used

All claims in this document are drawn from full-text MKVs in `literature/mkv/`
read in the session in which this document was produced.

| Cite key | Source | Relevant content |
| --- | --- | --- |
| `beukelman-2020-aac` | Book (local) | Ch. 15: stored-message and generative communicator definitions; agraphia in aphasia; 90%+ recognition accuracy; spelling/writing impairment; display density research; working memory and navigation; AAC failure modes |
| `koul-2011-aac-aphasia` | Book (local) | Ch. 2: agraphia taxonomy (lexical and phonological); agraphia as standard aphasia co-morbidity; limb apraxia co-occurrence |
| `thiel-2016-functional-writing` | Journal article (online, DOI 10.3109/09638288.2015.1114038) | Four dysgraphia subtypes documented in post-stroke aphasia cohort; "dysgraphia frequently occurs as one symptom of aphasia" |
| `thiel-2017-email-writing` | Journal article (online, DOI 10.1111/1460-6984.12261) | Writing sensitivity to brain damage; keyboard vs. handwriting distinction; assistive technology evidence |
| `thiel-2022-writing-experiences` | Journal article (online, DOI 10.1111/1460-6984.12762) | Lived experience of writing impairment; "the spelling is so hard and also it's the pain in my life"; production/recognition asymmetry in first-person accounts |
| `odendaal-2024-aac-aphasia-slp` | Journal article (online, DOI 10.1080/07434618.2024.2374303) | South African SLP perspectives; Garrett–Lasker framework in practice; "generic systems do not work"; customisation imperative; communication partner role |
| `huang-2021-aac-inpatient-rct` | Journal article (online, DOI 10.1186/s13063-021-05799-0) | Definition of post-stroke aphasia including writing; stored-message board design for moderate-severe aphasia; AAC reduces production pressure; AAC does not impede speech recovery |
| `formica-2024-aac-brain-injury` | Journal article (online, DOI 10.3390/brainsci14070709) | Case series: selection-based AAC succeeds where production fails; 71-year-old stroke patient with preserved comprehension and impaired writing |
| `pierce-2019-multimodal-therapy` | Journal article (online, DOI 10.1044/2018_AJSLP-18-0157) | AAC as "total communication" approach; distinction between production-focused and communication-focused interventions |
| `lowis-2024-caya-aac-aphasia` | Clinical resource (local) | Stored-message communicator profile: reading at word/phrase/sentence level as enabling competency |
| `tobii-aphasia-therapy-guide` | Clinical guide (local) | AAC does not impede speech recovery; no exclusion criteria based on timing or severity |
| `touchchat-2024-aphasia-guide` | Clinical guide (local) | Customisation imperative; technology familiarity as adoption factor |

## References

[@beukelman-2020-aac] D. R. Beukelman and J. C. Light, *Augmentative and Alternative Communication: Supporting Children and Adults with Complex Communication Needs*, 5th ed. Baltimore, MD: Paul H. Brookes Publishing, 2020.

[@koul-2011-aac-aphasia] R. Koul and A. R. Beck, *Augmentative and Alternative Communication for Adults with Aphasia: Science and Clinical Practice*. Leiden: Brill Academic Publishers, 2011.

[@thiel-2016-functional-writing] L. Thiel, K. Sage, and P. Conroy, "The role of learning in improving functional writing in stroke aphasia," *Disability and Rehabilitation*, vol. 38, no. 23, pp. 2307–2317, 2016. doi: 10.3109/09638288.2015.1114038.

[@thiel-2017-email-writing] L. Thiel, K. Sage, and P. Conroy, "Promoting linguistic complexity, greater message length and ease of engagement in email writing in people with aphasia," *International Journal of Language & Communication Disorders*, vol. 52, no. 3, pp. 279–293, 2017. doi: 10.1111/1460-6984.12261.

[@thiel-2022-writing-experiences] L. Thiel and P. Conroy, "'I think writing is everything': writing experiences of people with aphasia," *International Journal of Language & Communication Disorders*, vol. 58, no. 2, pp. 298–312, 2022. doi: 10.1111/1460-6984.12762.

[@odendaal-2024-aac-aphasia-slp] I. Odendaal and K. M. Tönsing, "Augmentative and alternative communication for individuals with post-stroke aphasia: perspectives of South African speech-language pathologists," *Augmentative and Alternative Communication*, vol. 41, no. 1, pp. 56–64, 2024. doi: 10.1080/07434618.2024.2374303.

[@huang-2021-aac-inpatient-rct] L. Huang et al., "Augmentative and alternative communication intervention for in-patient individuals with post-stroke aphasia: study protocol of a parallel-group, pragmatic randomized controlled trial," *Trials*, vol. 22, no. 1, p. 951, 2021. doi: 10.1186/s13063-021-05799-0.

[@formica-2024-aac-brain-injury] C. Formica, M. C. De Cola, F. Corallo, and V. Lo Buono, "Role of Alternative and Augmentative Communication in Three Cases of Severe Acquired Brain Injury: A Neurorehabilitative Approach," *Brain Sciences*, vol. 14, no. 7, p. 709, 2024. doi: 10.3390/brainsci14070709.

[@pierce-2019-multimodal-therapy] J. E. Pierce, R. O'Halloran, L. Togher, and M. L. Rose, "What is meant by 'multimodal therapy' for aphasia?" *American Journal of Speech-Language Pathology*, vol. 28, no. 2, pp. 584–602, 2019. doi: 10.1044/2018_AJSLP-18-0157.

[@lowis-2024-caya-aac-aphasia] N. Lowis et al., *CAYA AAC Resource for Individuals with Aphasia*. CAYA, 2024.

[@tobii-aphasia-therapy-guide] Tobii Dynavox, *Communication Activity and Therapy Guide for Aphasia*. Tobii Dynavox, 2023.

[@touchchat-2024-aphasia-guide] TouchChat, *TouchChat Communication Journey: Aphasia — Vocabulary File User's Guide*. TouchChat, 2024.
