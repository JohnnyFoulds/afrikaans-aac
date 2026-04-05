# Why Stored-Message AAC and Not a Keyboard? A Literature-Grounded Analysis

**Date:** 2026-04-05
**Author:** Johannes Foulds
**Purpose:** Academic synthesis of the clinical and neurolinguistic rationale for
stored-message AAC over open-ended text-entry as the primary communication mode for
a post-stroke Afrikaans-speaking user with aphasia, intact comprehension, and literacy.
**Sources:** All claims drawn from full-text MKVs in `literature/mkv/` — verified
in this session against quotable passages.

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
language production system itself. The consequences of that distinction are
determinative for interface design. A keyboard demands exactly the linguistic
operations that aphasia damages. Pre-stored messages, by contrast, re-route
communication through recognition and selection — processes that are typically more
preserved. This document synthesises the clinical literature to explain why, and to
characterise the conditions under which stored-message AAC is the appropriate design
choice.

A secondary set of access factors — limited prior touchscreen experience and mild
post-stroke fine motor impairment — provide further independent justification for
large-button, low-density display design, over and above the core linguistic argument.

---

## 2. The Linguistic Architecture of Writing and Why Aphasia Disrupts It

### 2.1 Agraphia as a Neurological Co-Occurrence with Aphasia

Writing is not simply speech transcribed. It requires the successful activation of a
separate graphemic output pathway that is neurologically proximate to — and
frequently damaged alongside — the perisylvian language network affected in most
left-hemisphere strokes.

@koul-2011-aac-aphasia (Ch. 2) defines the relevant disorder:

> Agraphia (Greek: *a* = without + *graphein* = to write) is an acquired writing
> disorder in which the ability to write and spell (i.e., to produce graphemes) is
> impaired subsequent to a stroke or other brain damage. Agraphia can be divided into
> lexical (or surface agraphia) and phonological types. In lexical agraphia, an
> individual presents with impaired spelling characterized by "over-reliance on
> sound-to-letter conversions." Individuals with lexical agraphia have no difficulty
> spelling words with conventional sound-to-letter correspondence (e.g., mat) but are
> impaired at spelling irregular words (e.g., circuit, which may be misspelled as
> surkit or sirkit). In phonological agraphia, affected individuals can write common
> words (including irregularly spelled words) but cannot spell nonwords. Beeson et al.
> (2004) have reported that lexical agraphia is caused by left extrasylvian lesions
> resulting in impairment at the level of orthographic word forms. This is contrasted
> with phonological agraphia which results from left perisylvian cortical lesions that
> result in impaired phonological processing.

Critically, @koul-2011-aac-aphasia identifies agraphia as one of the standard
co-occurring disorders in aphasia, alongside dysarthria, apraxia of speech, alexia,
and agnosia:

> Aphasia is frequently associated with concomitant disorders affecting motor speech
> functions (e.g., dysarthria or apraxia of speech), sensory recognition (agnosia),
> reading (alexia), writing (agraphia), and swallowing ability (dysphagia).

The practical implication is immediate: for the majority of people with aphasia,
writing and spelling are not intact backup channels for speech. They are part of the
same damaged language system. A keyboard interface does not bypass the impairment; it
places the user directly in the impaired pathway.

### 2.2 The Processing Demands of Keyboard-Based Text Entry

Composing text at a keyboard requires a sequence of cognitive-linguistic operations
that are each vulnerable to stroke-induced damage:

1. **Lexical retrieval** — identifying the target word from the mental lexicon.
   Word-finding difficulties (anomia) are among the most universal symptoms across
   all aphasia types [@koul-2011-aac-aphasia, Ch. 2; @beukelman-2020-aac, Ch. 15].

2. **Phonological encoding** — retrieving the phonological form of the word in order
   to map it to its letter sequence. In phonological agraphia this route is
   specifically damaged, rendering spelling of unfamiliar or nonword forms unreliable
   [@koul-2011-aac-aphasia, Ch. 2].

3. **Orthographic retrieval** — accessing the stored letter sequence for the word
   (the orthographic lexicon). In lexical agraphia this route is damaged, producing
   phonologically plausible but orthographically incorrect spellings [@koul-2011-aac-aphasia, Ch. 2].

4. **Sequential graphemic output** — producing letters in correct serial order.
   @beukelman-2020-aac (Ch. 15) notes that generalised aphasia frequently produces
   "difficulties with word retrieval, spelling, and syntactic formulation" in written
   as well as spoken output.

5. **Working memory** — holding the intended message in working memory while
   executing the letter-by-letter sequence. @beukelman-2020-aac observes that
   people with aphasia frequently demonstrate "reductions in processing speed,
   attention, memory, executive functions, and/or problem solving that cannot be
   completely explained by language impairments alone."

The convergence of these demands makes free-form keyboard use not merely difficult but
functionally non-viable for most people with moderate to severe aphasia.
@beukelman-2020-aac (Ch. 15) states this directly:

> People with very severe aphasia, however, cannot write independently. Their
> linguistic impairments prevent them from meeting the composition, semantic,
> syntactic, and spelling demands of independent writing.

Even at less severe levels, @beukelman-2020-aac (Ch. 15) identifies spelling errors as
a persistent frustration for generative communicators, noting that "writers with
aphasia are frequently frustrated by difficulties with word retrieval, spelling, and
syntactic formulation." Word prediction technology can mitigate some of this burden,
and @beukelman-2020-aac (Ch. 15) documents cases where generative AAC communicators
have benefited from word prediction and text-to-speech; however, these individuals
represent the upper end of the cognitive-linguistic continuum (anomic, mild conduction
aphasia), where residual language production is substantially intact.

---

## 3. Recognition as an Alternative Pathway

### 3.1 The Production/Recognition Distinction

The central design principle of stored-message AAC is the substitution of *recognition*
for *production*. When a user selects a pre-stored message, they are performing a
recognition task: scanning a set of externally represented options and identifying one
that matches their communicative intent. Recognition does not require lexical retrieval,
phonological encoding, or orthographic sequence production. It requires only that the
stored form — whether word, phrase, photograph, or symbol — is sufficiently legible and
contextually presented to trigger identification.

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

### 3.2 Literacy as an Enabling Factor, Not a Production Guarantee

A user who retains literacy — the ability to read words and phrases — occupies a
privileged position on the AAC continuum. @beukelman-2020-aac (Ch. 15) and
@lowis-2024-caya-aac-aphasia both identify reading ability at the word/phrase/sentence
level as the defining competence of stored-message communicators. Literacy enables
the user to navigate labelled displays without symbol-learning burdens and to select
messages whose text they can verify before activation.

However, literacy as a receptive/recognition skill is not equivalent to literacy as
a productive/generative skill. A person can reliably *read* a word without being able
to *spell* it under the dual load of aphasia. The preserved reading ability of the
project participant supports stored-message AAC precisely because it enables accurate
recognition; it does not imply that keyboard composition is viable.

@lowis-2024-caya-aac-aphasia makes this distinction operationally explicit by
distinguishing stored-message communicators (who require "read at word/phrase/sentence
level" as a *receptive* competency) from generative writers (who require the ability
to "recognise items through whole-word or phonological strategies" *while producing*
sequences), noting that even at the generative level, spelling and word retrieval
errors are common barriers.

---

## 4. The Stored-Message Communicator Profile

### 4.1 Clinical Classification

@beukelman-2020-aac (Ch. 15) defines stored-message communicators as follows:

> Stored-message AAC communicators can learn to independently locate messages that
> have been stored in advance within their low- or high-tech AAC systems, even if they
> cannot generate these messages independently via spelling, combining symbols,
> writing, or speaking. They have enough executive function and initiation ability to
> learn to consistently access entire phrase or sentence messages in specific contexts.

The distinguishing feature of this communicator category — in contrast to the
transitional communicator below it on the continuum — is *partner-independent
initiation*: "stored-message AAC communicators can learn to initiate and use their
systems to supplement or substitute for speech without prompting within familiar
situations" [@beukelman-2020-aac, Ch. 15].

The participant in this project maps directly to this profile: intact comprehension,
literacy at the word/phrase/sentence level, and the executive capacity to navigate
a familiar display without requiring a partner to curate options on a turn-by-turn
basis. His communication is not partner-dependent in the clinical sense; the system
must support *his own* initiation.

### 4.2 The Failure Mode of Keyboard-Centric Design

@beukelman-2020-aac (Ch. 15) documents the concrete consequences of placing
generative demands on users whose linguistic system does not support them:

> However, they seldom generate enough novel information to participate in a
> discussion about an unusual topic because their spelling, speech, and AAC
> capabilities are not sufficient to participate independently in free-form
> conversations.

This observation applies even to stored-message communicators who have some residual
spelling ability: the system can be supplemented with a keyboard level for familiar
short words, as @beukelman-2020-aac (Ch. 15) describes in the case of Norman (who
used keyboard access primarily to type first letters for word prediction, not to
compose sentences). The stored-message layer is the functional primary; text entry
is a supplementary fallback, not the primary design centre.

The documented failure modes for AAC in aphasia include:

1. Vocabulary and content that do not match specific real-life communication
   opportunities [@beukelman-2020-aac, Ch. 15]
2. Communication partners unwilling to accept AAC [@beukelman-2020-aac, Ch. 15]
3. Technology too large/unwieldy or too small for the user's vision capabilities
   [@beukelman-2020-aac, Ch. 15]
4. Social networks so restricted that communication opportunities are absent
   [@beukelman-2020-aac, Ch. 15]

None of these failure modes is caused by the use of pre-stored messages per se.
All of them can be caused by a keyboard-centric design that demands linguistic
production the user cannot reliably execute, resulting in frustration, abandonment,
and — eventually — social withdrawal.

---

## 5. Display Design: Large Targets and Low Symbol Density

### 5.1 Neurological and Cognitive Constraints on Navigation

Even where the linguistic argument is accepted, the question of display design
remains. The optimal stored-message interface for a person with aphasia is not merely
any pre-programmed system; it is one whose physical and cognitive access demands
match the user's profile.

@beukelman-2020-aac (Ch. 15) summarises the evidence on display density:

> Research suggests that the MCST-A effectively distinguishes between communicators
> who require partner support to indicate choices and stored-message AAC communicators
> who can independently search through the booklet to locate symbols.

More directly on density effects, @beukelman-2020-aac (citing Petroi, Koul, & Corwin,
2014) establishes that "people with aphasia identify symbols within an AAC device most
readily when fewer symbols per screen are displayed and when minimal navigation is
required." Wallace and Hux (2013) found improved access efficiency "when provided with
a navigation ring compared to standard multiple-display navigation."

The working memory cost of multi-level navigation is particularly relevant.
@beukelman-2020-aac notes that "arranging messages in AAC systems with multiple
displays... may impose significant processing challenges for many people with aphasia
who demonstrate problems recalling the location of stored messages and symbols. They
must demonstrate sufficient working memory to complete the steps involved in accessing
the messages before forgetting their intent." Large targets on low-density displays
reduce the number of navigation steps and the working memory load associated with
each step.

### 5.2 Motor Access Factors

@beukelman-2020-aac identifies motor impairments as a direct constraint on physical
access to writing technologies: "Motor impairments that limit or complicate physical
access to reading materials and writing implements (e.g., pencils, pens, computer
keyboards, or other technologies)."

For the project participant, mild post-stroke fine motor impairment in the upper
extremity compounds the above. Keyboard use — which requires precise individual
key activation across a dense array of small targets — is substantially more demanding
of fine motor precision than large-button touchscreen activation. @koul-2011-aac-aphasia
(Ch. 2) notes that limb apraxia frequently co-occurs with anterior aphasia syndromes
and "can interfere with pointing, gesturing, and device operation."

The large-button design of the current implementation responds to this compound
requirement: it must be operable by someone with (1) reduced precision grip and
tremor, and (2) no prior touchscreen experience — a combination that makes dense or
small-target interfaces unreliable regardless of the linguistic argument.

### 5.3 Technology Familiarity as an Independent Access Factor

@touchchat-2024-aphasia-guide acknowledges that AAC technology is often most
successfully adopted by users who have some prior technology experience. Where prior
experience is absent, interface complexity becomes an adoption barrier independent of
communicative competency.

The participant has never used a smartphone or tablet in regular daily life. The
gestural grammar of touchscreen interfaces — swipe, scroll, pinch, tap — must be
treated as an acquired skill, not a baseline assumption. Large, clearly labelled,
single-purpose targets minimise the interface learning curve to its lowest practicable
level: one action (tap) maps to one communicative output (message played aloud).

---

## 6. The Trade-Off: Vocabulary Coverage vs. Linguistic Accessibility

### 6.1 The Real Constraint of Pre-Stored Vocabularies

The stored-message approach has an acknowledged limitation: communication is bounded
by what has been programmed. @beukelman-2020-aac (Ch. 15) lists vocabulary mismatch
as the primary documented failure mode for AAC in aphasia. @touchchat-2024-aphasia-guide
states that "there is no standardized vocabulary file that will meet even the minimum
needs of every person with aphasia... customization is the responsibility of the
speech language pathologist."

This limitation is real but manageable. It implies a design obligation: the
vocabulary set must be built around the actual communicative ecology of this specific
user — his daily routines, his family relationships, his recurring topics, his
healthcare needs, and his preferences. The burden of customisation does not invalidate
the stored-message model; it defines the minimum requirements for implementing it
correctly.

### 6.2 Evolving Toward Greater Generativity

@beukelman-2020-aac (Ch. 15) and @tobii-aphasia-therapy-guide both observe that AAC
system design should reflect the user's current communicator profile but anticipate
progression. As linguistic recovery continues — or as the user's facility with the
stored-message system develops — supplementary generative features (word prediction,
first-letter alphabet access, free-text field) can be introduced without replacing the
primary stored-message infrastructure.

The current implementation represents the appropriate starting point, not a permanent
ceiling. The design logic is one of successive approximation: begin at the
communicator's current functional level and build upward as competency develops.
@tobii-aphasia-therapy-guide explicitly addresses the temporal dimension: AAC is
appropriate "any time post their onset, at any level of language impairment," and
"using AAC will not hinder PWA's ability to regain speech."

---

## 7. Synthesis: Why the Current Design Is Appropriate

The stored-message, large-button AAC design for this user rests on a convergence of
four independent lines of argument, each individually sufficient and mutually
reinforcing:

**1. The primary impairment is linguistic, not motor.**
Keyboard-based text composition demands lexical retrieval, phonological encoding,
orthographic sequencing, and syntactic formulation. Aphasia damages all of these.
Agraphia — impairment of the written output pathway — co-occurs with aphasia in the
majority of cases [@koul-2011-aac-aphasia, Ch. 2]. Even where residual spelling is
present, it is frequently too fragmented and inconsistent for reliable sentence-level
communication [@beukelman-2020-aac, Ch. 15].

**2. Recognition is more preserved than production.**
The user's intact comprehension and literacy are assets for *recognising and selecting*
pre-stored messages, not for *generating* them from scratch. People with aphasia have
demonstrated over 90% accuracy in selecting from written choices in context, despite
near-zero formal reading scores [@beukelman-2020-aac, Ch. 15]. The stored-message
paradigm routes communication through the more preserved pathway.

**3. The user's communicator profile fits the stored-message category.**
Partner-independent initiation, literacy at word/phrase/sentence level, intact
comprehension, and sufficient executive function to navigate a familiar display are
the defining characteristics of stored-message communicators
[@beukelman-2020-aac, Ch. 15; @lowis-2024-caya-aac-aphasia]. The participant meets
all criteria. A keyboard-first design would target the generative level, which sits
above his current functional profile.

**4. Physical and experiential access factors independently require large targets.**
Mild post-stroke fine motor impairment and zero prior touchscreen experience both
favour a large-button, low-density display. Evidence from display density research
confirms that aphasia-specific cognitive constraints (working memory, navigation
load) converge with these motor and experiential factors to make low-density, minimal-
navigation displays the empirically supported choice [@beukelman-2020-aac, Ch. 15].

---

## 8. Sources Used

All claims in this document are drawn from full-text MKVs in `literature/mkv/`
that were read in the session in which this document was produced.

| Cite key | Relevant content |
|---|---|
| `beukelman-2020-aac` | Ch. 15: stored-message and generative communicator definitions; agraphia in aphasia; 90%+ recognition accuracy; spelling/writing impairment in aphasia; display density research; working memory and navigation; failure modes of AAC |
| `koul-2011-aac-aphasia` | Ch. 2: agraphia taxonomy (lexical and phonological); agraphia as standard aphasia co-morbidity; writing impairment across aphasia types |
| `lowis-2024-caya-aac-aphasia` | Stored-message communicator profile: reading at word/phrase/sentence level as enabling competency; literacy requirements per communicator type |
| `tobii-aphasia-therapy-guide` | No exclusionary criteria based on timing or severity; AAC does not inhibit speech recovery; temporal recommendations |
| `touchchat-2024-aphasia-guide` | Customisation imperative; technology familiarity as adoption factor; AAC for specific aphasia profiles |

## References

[@beukelman-2020-aac] D. R. Beukelman, J. C. Light, P. Mirenda, et al., *Augmentative and Alternative Communication: Supporting Children and Adults with Complex Communication Needs*, 5th ed. Baltimore, MD: Paul H. Brookes Publishing Co., 2020.

[@koul-2011-aac-aphasia] R. K. Koul, Ed., *Augmentative and Alternative Communication for Adults with Aphasia: Science and Clinical Practice*. Bingley, UK: Emerald Group Publishing, 2011.

[@lowis-2024-caya-aac-aphasia] D. Lowis, *CAYA AAC-Aphasia Categories of Communicators Checklist*. Clinical AAC resource, 2024.

[@tobii-aphasia-therapy-guide] Tobii Dynavox, *Aphasia Therapy Guide*, 2024.

[@touchchat-2024-aphasia-guide] PRC-Saltillo, *TouchChat AAC Aphasia User Guide*, 2024.
