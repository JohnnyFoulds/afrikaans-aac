# Intelligent AAC for Post-Stroke Aphasia in Low-Resource African Language Settings: A Literature Review for PhD Framing

**Purpose:** This review maps the academic literature relevant to framing an AI-focused PhD around the Afrikaans AAC project. It evaluates three candidate framings — (A) full intelligent AAC with AI inference features, (B) African language NLP + edge deployment without new features, (C) pure DSR/HCI — against the goals of AI credibility, applied research rigour, and institutional leverage. The review is evidence-based: every claim is drawn from a full-text MKV in `literature/mkv/`.

---

## Section 1 — The Communication Gap: Aphasia, AAC, and the South African Context

### 1.1 The epidemiology of post-stroke aphasia

Stroke is the most common cause of acquired aphasia. @brady-2021-release, the RELEASE meta-analysis of 5,928 participants across 47 randomised controlled trials, reports that "approximately one-third of the 25.7 million stroke survivors worldwide experience aphasia," with long-term language impairment affecting "61% of stroke survivors' communication at 1 year after onset." In South Africa specifically, stroke is the third most common cause of disability [@odendaal-2024-aac-aphasia-slp], and approximately 34% of ischemic stroke survivors develop aphasia [@odendaal-2024-aac-aphasia-slp].

Aphasia takes many forms. For people with non-fluent expressive aphasia — the type most common after left-hemisphere anterior lesions — the impairment is specific to language *production*: comprehension is typically intact, reading may be preserved, and cognitive capacity is substantially unaffected [@beukelman-2020-aac; @koul-2011-aac-aphasia]. The clinical significance is that a cognitively intact person is isolated by a specific failure in the production pathway: they know what they want to say but cannot produce the words. Augmentative and Alternative Communication (AAC) addresses exactly this gap.

Recovery from aphasia is meaningful but incomplete. @brady-2021-release demonstrates that gains are largest when intervention begins within one month of onset (overall-language improvement of +19.1 WAB-AQ points), but "clinically meaningful gains are still observable even beyond 6 months" — including in participants over 75 and in those enrolled more than two years post-onset. This persistent recovery trajectory means that AAC interventions remain relevant throughout the chronic phase, not only in acute rehabilitation.

### 1.2 Why stored-message AAC, not keyboard or LLM generation

Non-fluent aphasia damages the language production system itself [@beukelman-2020-aac; @koul-2011-aac-aphasia]. This has a direct implication for interface design: a keyboard or free-text generation interface requires the user to *produce* language — to think of words, select letters, and construct grammar — which uses precisely the impaired pathway. A stored-message interface, by contrast, requires *recognition*: the user identifies a pre-formed phrase that matches their intent and activates it. Recognition uses a more preserved cognitive pathway [@koul-2011-aac-aphasia].

@russo-2017-hightech-aac-aphasia review 30 studies of high-technology AAC for post-stroke aphasia and report that 90% showed positive or mixed outcomes. The most successful interventions employed vocabulary that was "as meaningful as possible to that person" [@odendaal-2024-aac-aphasia-slp] — a personalisation requirement that motivates word prediction and adaptive ranking, even in a stored-message system.

The clinical case for AAC for aphasia is explicit in South African practice. @odendaal-2024-aac-aphasia-slp surveyed 10 South African SLPs: all 10 reported implementing AAC with post-stroke aphasia clients, and 9 of 10 stated it was relevant. One participant described the principle: "You can never take away the hope that they have that their speech will return. Once they realize the power of communication that the [AAC] system can bring them... it is unlimited." The same study documents the central barrier: "generic systems... not set up in a way that that person [with post-stroke aphasia] relates to it" — motivating language-specific, personalised tools.

### 1.3 The Afrikaans gap

The South African SLP workforce cannot bridge the linguistic gap. @odendaal-2024-aac-aphasia-slp documents a stark disparity: of 10 participating SLPs, only two spoke an African language, "highlighting the disparity in providing SLP services to a country where the languages most frequently spoken as home languages are isiZulu (24.4%) and isiXhosa (16.3%)." Afrikaans is spoken by approximately 13.5% of the population as a home language.

The vocabulary gap is structurally confirmed. @hattingh-2020-afrikaans-vocab established the first empirically grounded Afrikaans core vocabulary list, based on 12 Grade R (age 5–6) learners: 239 words met core vocabulary criteria, covering 79.4% of all speech in the composite sample. The paper explicitly acknowledges it is the "first core word list established in Afrikaans based on a sample of spoken words" and calls for extension to "other age groups... other settings." @winter-2025-afrikaans-vocab extend the methodology to a second paediatric dataset (25 children, structured elicitation, 60 minutes) and find a "perfect positive Spearman correlation (r = 1.00) between the two datasets" — confirming the paediatric vocabulary, but explicitly not extending it to adults. Both papers study preschool children. No adult Afrikaans clinical vocabulary list exists.

---

## Section 2 — AI Techniques in AAC: Word Prediction, LLMs, and the Aphasia Interface

### 2.1 The word prediction lineage

Word prediction for AAC has a well-established research lineage. @trnka-2007-corpus-word-prediction conducted corpus-based analysis of natural language to establish which prediction models best match AAC communication patterns, finding that context-sensitive n-gram models substantially outperform recency-only approaches. @trnka-2009-word-prediction-aac ran a controlled experiment with 33 adults using a simulated AAC interface (1.5-second key delay, producing ~8 wpm — comparable to real AAC users) and demonstrated that prediction quality is the decisive variable: "users communicate on average 45.8% faster using advanced prediction over basic prediction and 61.4% faster than using no word prediction." Prediction utilisation also differed: users selected from advanced prediction 94.4% of the time versus 79.9% for basic prediction — the better system was trusted and used more.

The mechanism is twofold. First, keystroke savings are direct: the advanced predictor (trigram language model) achieved 52.6% actual keystroke savings versus 20.9% for basic. Second, fatigue reduction is significant: "Advanced word prediction was much less tiring than basic word prediction" — a finding of special relevance for aphasia, where cognitive fatigue is a major barrier to sustained AAC use [@mao-2025-ai-aac-aphasia].

These results establish a quantitative benchmark framework — perplexity, keystroke savings, communication rate — that subsequent LLM-based AAC work directly inherits.

### 2.2 LLMs for AAC: current state and open problems

@gaines-2025-llm-aac demonstrate that LLMs can substantially outperform classical n-gram predictors for character-level AAC input: their best model (OPT-350M fine-tuned on conversational text) achieves average per-character perplexity of 2.11 versus the AAC n-gram baseline of 2.54 — a 17% relative improvement — and keystroke savings of 65.2% versus 59.7%. Crucially, the OPT-350M model achieves this using only 350 million parameters, smaller than many production-grade LLMs, suggesting that on-device deployment is plausible. The authors note that "larger LLMs eventually outperformed [the AAC n-gram baseline] despite the LLMs not being fine-tuned on AAC-like text," but that domain adaptation — fine-tuning on conversational rather than web-crawl text — is necessary for robust performance at smaller model sizes.

@dipaola-2024-llm-aac provide a design roadmap for foundation models in AAC, identifying five challenges: social barriers, technological barriers, cultural barriers, educator skill gaps, and flexibility/data analysis needs. Their AMBRA architecture explicitly proposes federated learning for on-device personalisation, and identifies multilingual and cultural barriers as "unsolved challenges" — precisely the gap this project addresses for Afrikaans. The paper notes the critical design principle that "AAC is not a one-size-fits-all solution; it requires a personalized approach."

The aphasia-specific constraint is identified but not resolved in existing work. @gaines-2025-llm-aac acknowledge that their models produce character-level predictions for a letter-by-letter keyboard interface — not word-level predictions for a stored-phrase board. For aphasia specifically, the constraint is stronger still: the interface cannot require users to produce language from scratch, only to recognise and select. LLM-generated *suggestions* — short, high-frequency phrases ranked by contextual relevance — represent the appropriate interaction modality, not free-text generation.

### 2.3 AI for conversational repair: the listen-and-suggest case

Conversational repair — the process by which communication breakdowns are detected and resolved — is not a symptom of aphasia but a joint conversational process. @ferguson-1994-conversational-repair studied 9 aphasic and 18 normal subjects in structured and unstructured conversations and found that "all 18 normal subjects used interactive repair patterns with aphasic partners; only 10 of 18 did so with normal partners" — demonstrating that repair behaviour adjusts to the interactant, not the pathology. The study establishes that "this view of communication as jointly negotiated through the action of repair has the potential to enhance the type and range of therapy for aphasic individuals and their conversational partners."

The prospect of AI supporting the conversational side of repair — listening to the partner's speech and suggesting responses the patient can select — is a recent development. @mao-2025-ai-aac-aphasia conducted design probe research with 11 people with aphasia across two evaluation phases. Their System 2 (keyword-to-sentence generation using GPT-3.5 with intent categories) was rated most positively across participants; one participant (AP8, unable to form sentences independently) responded "Beautiful… Great sentences for words, man." The same study identified a critical failure mode: "AI instability/misalignment" — when inputs were ambiguous, AI-generated outputs diverged dramatically from intended meaning.

@vanvaals-2024-llm-broca directly address the sentence-completion task for Broca's aphasia: fine-tuning T5 on synthetically generated agrammatic utterances, they report successful completion in 41% of authentic aphasic test sentences, and conclude that "LLM-based approaches provide a possibility to overcome these restraints by offering ongoing and consistent support tailored to the specific needs of a patient." The study identifies the key prerequisite: a spoken-language corpus from which to generate synthetic training data. "For many [languages] featured," this corpus does not exist — including Afrikaans.

@russo-2017-hightech-aac-aphasia identify communication-partner involvement as a consistent success factor across 30 studies: "The experience in the field of AAC interventions has shown that accepting the new high-technology device may depend on the presence of a caregiver or communication partner." An AI system that mediates the partner's speech — transcribing it and generating response options — directly integrates the partner into the communication loop, consistent with the evidence base.

### 2.4 The aphasia-specific constraints not met by existing AI-AAC work

The existing AI-AAC research has four consistent gaps relative to this project:

1. **Language**: all published LLM-AAC work is English-only. @gaines-2025-llm-aac's training corpora (Switchboard, BOLT, Daily Dialog) are English. @vanvaals-2024-llm-broca's synthetic data generator "may not transfer to morphologically different languages like Afrikaans." No published work addresses LLM-assisted AAC for any African language.

2. **Population**: most word prediction and AI-AAC work targets motor impairment (cerebral palsy, ALS, MND) or developmental disabilities, not acquired post-stroke aphasia [@russo-2017-hightech-aac-aphasia; @trnka-2009-word-prediction-aac]. Aphasia imposes additional cognitive load, vocabulary constraints, and word-retrieval difficulties that existing systems do not model.

3. **Deployment context**: all existing work assumes reliable internet connectivity and commercial cloud inference [@dipaola-2024-llm-aac; @gaines-2025-llm-aac]. The South African home-care deployment context — commodity Android tablet, intermittent or absent connectivity, low-data-cost constraint — is not addressed.

4. **Personalisation with sparse data**: @mao-2025-ai-aac-aphasia note that "the heterogeneity of aphasia makes it difficult to design AAC systems that accommodate all users without excluding some." Single-user deployment with a few taps per day is the primary data source for personalisation — a sparsity regime that existing recommendation and ranking systems are not designed for.

Each of these gaps is a PhD-level research contribution.

---

## Section 3 — Low-Resource NLP and the African Language AI Landscape

### 3.1 The structural under-resourcing of African language NLP

The under-representation of African languages in NLP is structural, not merely a data availability problem. @nekoto-2020-participatory-nlp document that Africa has 2,144 living languages, yet "of all ACL conferences in 2019, only 5 out of 2,695 (0.19%) author affiliations were based in Africa" — a disparity that reflects "systemic problems in society" and produces a self-reinforcing cycle of exclusion. @nekete-2020-masakhane establish the Masakhane initiative to address this, lowering participation barriers (free compute, Jupyter notebooks, no academic prerequisites) and creating the first reusable benchmarks for African language NLP.

@hedderich-2021-lowresource-nlp, in a 365-citation survey, frame the problem precisely: "most of today's research in natural language processing (NLP) is concerned with the processing of 10 to 20 high-resource languages with a special focus on English, and thus, ignores thousands of languages with billions of speakers." The survey documents that "African and American languages are not well-represented within the transformer models, even though millions of people speak these languages," and that practical performance gaps compound: "the four American and African languages with between 1.5 and 60 million speakers have been addressed less than the Estonian language, with 1 million speakers."

### 3.2 The Afrikaans NLP position

Afrikaans occupies an ambiguous position in this landscape. @wet-2011-afrikaans-asr describe it as "the most technologically developed language in South Africa" but "still... an under-resourced language when compared to languages such as English, Spanish, Dutch or Japanese." Afrikaans benefits from lexical and structural similarity to Dutch, enabling what @wet-2011-afrikaans-asr call "recycling" of Dutch resources — bootstrapping NLP tools from a better-resourced sibling language — but this advantage is limited for specialised domains (medical, clinical, aphasia-specific vocabulary) where Dutch resources do not exist.

@martinus-2019-masakhane quantify the resource baseline: as of 2019, Afrikaans had only 37,219 training sentences for machine translation — compared to millions for high-resource languages — yielding a best BLEU score of 35.26 with transformer models. Afrikaans substantially outperforms isiZulu (BLEU 3.33) and isiXhosa, reflecting the Dutch proximity advantage, but remains "low-resource" by global NLP standards.

For AAC specifically, the resource gap is complete. The only published Afrikaans vocabulary lists are @hattingh-2020-afrikaans-vocab and @winter-2025-afrikaans-vocab — both covering preschool children (ages 5–6), both derived from structured or naturalistic play contexts, neither applicable to adult clinical communication. No Afrikaans corpus exists for adult spontaneous conversational speech, adult clinical vocabulary, or aphasia-specific phrase patterns. The foundational data resource required for any NLP contribution — an adult Afrikaans clinical phrase corpus — does not exist. This is both the primary gap and the primary first-phase research contribution.

### 3.3 Transfer learning and the multilingual model landscape

@adelani-2021-masakhaner demonstrate that multilingual models such as AfroXLM-R, fine-tuned on as few as 10–100 sentences of target-language data, yield "significant boost in performance for classification in low-resource languages" [@hedderich-2021-lowresource-nlp]. The MasakhaNER 2.0 paper [@adelani-2022-masakhaner2] shows that "choosing the best transfer language improves zero-shot F1 scores by an average of 14 points across 20 languages compared to using English." For Southern Bantu languages (isiXhosa, isiZulu), choosing isiZulu as a transfer source over English yields F1 of 83.7 versus 24.5 — a 59-point improvement. Afrikaans, structurally closer to Dutch than to Bantu languages, would benefit from Dutch or multilingual transfer rather than English or Bantu.

These findings establish a clear technical path for a PhD-level NLP contribution: construct an adult Afrikaans clinical vocabulary corpus, fine-tune AfroXLM-R or a multilingual sentence transformer on it, and evaluate against a frequency-ranking baseline. @hedderich-2021-lowresource-nlp confirm that "fine-tuning language BERT and language XLM-R models achieves a 1–7% improvement in F1-score over fine-tuning mBERT-base and XLM-R-base respectively" even with modest additional data. The contribution is modest but genuine: the first NLP evaluation on an adult Afrikaans clinical phrase dataset.

### 3.4 Afrikaans ASR: from 2011 to 2025

@wet-2011-afrikaans-asr developed the first broadband Afrikaans ASR system: a 27-hour broadcast news corpus, ~24,000-entry pronunciation dictionary, and HMM acoustic model achieving 76% phone correctness / 69% accuracy. The corpus was entirely read broadcast news, which the authors acknowledge "leaves much room for improvement" for conversational or clinical ASR. No word-error rate or large-vocabulary continuous speech recognition results are reported.

By 2025, @jacobs-2025-afrikaans-asr demonstrate dramatically improved results using Whisper (OpenAI) as a base model. On preschool children's oral narratives, fine-tuning with only 5 minutes of in-domain speech achieves WER of 47.4% for Afrikaans — compared to 88.1% with no fine-tuning. The most effective intervention is adding 30 minutes of in-domain adult speech (adults reading the same narrative texts), reducing WER to 33.7%. The paper documents the key finding: "in-domain data is beneficial... will still be easier to obtain than child recordings" — a practical observation directly applicable to building an ASR component for aphasia AAC, where collecting large volumes of impaired speech is constrained but small in-domain samples are achievable.

The ASR gap for adult conversational and aphasia-specific speech remains open. @jacobs-2025-afrikaans-asr work with narrative preschool data; no published work addresses Afrikaans ASR for adult conversational speech or for aphasic utterances. @vanvaals-2024-llm-broca note that a sentence completion pipeline for aphasia "depends on available spoken-language corpora... that do not exist for Afrikaans."

---

## Section 4 — Personalisation Under Extreme Data Scarcity

A recurring theme across the AI-AAC literature is the tension between personalisation and data availability. @odendaal-2024-aac-aphasia-slp document that SLPs consistently identify personalisation as the key success factor: "AAC should always be as meaningful as possible to that person." @mao-2025-ai-aac-aphasia confirm that PWAs want control: "AI should serve as an 'assistive tool, not a directive tool'" (AP6). @dipaola-2024-llm-aac argue that "AAC is not a one-size-fits-all solution; it requires a personalized approach" and propose federated learning for edge-device personalisation.

In home-deployed single-user AAC, the personalisation data is the usage log: which phrases were selected, how frequently, in which conversational sequences. For a patient using the app several times per day, this may yield tens of tap events daily — orders of magnitude less than the feedback signal assumed by recommendation system training literature.

This is a genuine research gap. Existing techniques for preference learning and continual adaptation assume either a large initial dataset or rapid online feedback. Neither assumption holds in the aphasia AAC context. The PhD-level contribution is not in inventing a new personalisation algorithm but in characterising and solving the specific problem of preference learning with extremely sparse, temporally spaced, single-user feedback in the clinical AAC domain — a problem instance that has not been studied.

The technical approach is tractable without a large model: lightweight embedding-based ranking with online update (e.g. a small bilinear preference model over phrase embeddings), or Bayesian ranking over a bounded vocabulary space (200–400 stored phrases), can be updated from tens of observations and run at inference time on a commodity Android device. The contribution is in defining the problem, implementing a solution, evaluating it in a real longitudinal deployment, and publishing the evaluation framework for others to build on.

---

## Section 5 — Edge AI and Offline Deployment in Low-Connectivity Settings

The deployment context of the Afrikaans AAC project is fully offline: an Android tablet in a home environment, with no reliable internet connectivity assumed. This constraint is not incidental but structural — South African home care settings, particularly in coloured and Afrikaner working-class communities, have intermittent data access, high per-megabyte costs relative to median income, and device hardware that is commodity grade rather than high-performance.

@wet-2011-afrikaans-asr note that Afrikaans "can still be considered an under-resourced language" in its NLP infrastructure; the infrastructure constraint applies equally to deployment: cloud-based inference assumes connectivity and per-query cost structures that are not viable for home-deployed AAC in South Africa.

The edge AI opportunity is direct. @gaines-2025-llm-aac demonstrate that a 350M-parameter LLM achieves state-of-the-art AAC prediction results — substantially smaller than the billion-parameter models most commonly discussed. Whisper's smallest variant (`whisper-tiny`) runs in real time on CPU-only devices. Lightweight phrase-ranking models require negligible compute. The research contribution in the edge deployment space is not about developing new compression algorithms but about:

1. **Characterising the deployment constraints** of the specific hardware (current: AWOW UTBook_15 Android tablet; general: commodity Android hardware) for LM inference and ASR
2. **Evaluating the trade-off** between on-device inference (full offline capability, higher latency/memory) and thin-client inference (lower latency, connectivity-dependent)
3. **Documenting design principles** for offline-first AI deployment in low-connectivity South African household settings

This characterisation is publishable as an engineering contribution (IEEE TNSRE or ACM ASSETS) and is directly applicable to Vodacom's connectivity-equity framing: the results inform deployment decisions for any AI-enabled health or accessibility application in the South African market.

---

## Section 6 — Design Science Research as Methodology for an AI-Artefact PhD

### 6.1 The DSR framework

@hevner-2004-dsr, with over 12,000 citations, provides the foundational framework for Design Science Research in Information Systems. DSR is explicitly positioned as complementary to behavioural science: "the behavioral-science paradigm seeks to develop and verify theories that explain or predict human or organizational behavior. The design-science paradigm seeks to extend the boundaries of human and organizational capabilities by creating new and innovative artifacts."

The four types of IT artefact — constructs, models, methods, and instantiations — map directly to this project's contributions: the Afrikaans clinical vocabulary corpus (a construct), the phrase-prediction language model (a model and method), and the deployed AAC PWA with AI inference components (an instantiation). The seven DSR guidelines are satisfied: the artefact addresses an unsolved real-world problem (communication for Afrikaans-speaking stroke survivors without SLP support); it is evaluated through deployment; the design cycles generate reusable knowledge.

The critical DSR requirement is explicit: "the key differentiator between routine design and design research is the clear identification of a contribution to the archival knowledge base." For this project, the contribution to the knowledge base is threefold: (1) the adult Afrikaans clinical vocabulary corpus, (2) the evaluation of NLP-assisted phrase prediction for low-resource African language AAC, and (3) the design principles derived from deploying AI-assisted AAC in a low-resource South African home-care setting — generalisable to other under-resourced African languages.

### 6.2 Why DSR suits an AI-artefact PhD

The alternative to DSR is a behavioural study (randomised controlled trial or quasi-experimental design comparing the AAC system against a control condition). An RCT for AAC in post-stroke aphasia requires ethics clearance, a clinical collaborator (an SLP), and a minimum of 20–30 participants — infrastructure that will take at minimum 18–24 months to establish. DSR, by contrast, can begin with a single participant (the current deployment) and expand through design cycles as ethics clearance is obtained. The initial design cycle (single-participant home deployment, N=1) is not a limitation in DSR terms — it is the first iteration of a legitimate research process [@hevner-2004-dsr].

Crucially, DSR is the appropriate methodology for a researcher whose primary expertise is engineering, not clinical science. @odendaal-2024-aac-aphasia-slp document that clinical AAC practice is constrained by "the clinician factors... ability, willingness to learn, and willingness to be reflective" — a framing that acknowledges the engineer's contribution is legitimate alongside (not subordinate to) the clinician's. In DSR, the artefact is the contribution; the clinical validation is the evaluation criterion.

---

## Section 7 — Synthesis: The Four-Way Research Gap

The literature establishes four intersecting gaps, each necessary but none sufficient alone:

**Gap 1 — Clinical**: Post-stroke aphasia is prevalent (~34% of stroke survivors), persistent (61% still impaired at 1 year), and largely unserved in Afrikaans-speaking South African home-care settings [@brady-2021-release; @odendaal-2024-aac-aphasia-slp]. Existing AAC interventions show 90% positive/mixed outcomes [@russo-2017-hightech-aac-aphasia] but require SLP involvement that is structurally unavailable for most patients.

**Gap 2 — Language**: No adult Afrikaans clinical vocabulary list exists [@hattingh-2020-afrikaans-vocab; @winter-2025-afrikaans-vocab]. No NLP model has been trained or evaluated on adult Afrikaans clinical or conversational speech. The Afrikaans ASR baseline is 14 years old [@wet-2011-afrikaans-asr] and was built exclusively on broadcast news; no work addresses conversational or aphasia-specific Afrikaans ASR.

**Gap 3 — AI interaction model**: All published LLM-AAC work is English-only and targets motor impairment rather than aphasia [@gaines-2025-llm-aac; @dipaola-2024-llm-aac; @trnka-2009-word-prediction-aac]. The listen-and-suggest (conversational repair) modality — ASR + conditioned response generation — has no published Afrikaans or African language implementation. Personalisation under the extreme data scarcity of single-user home deployment is unstudied.

**Gap 4 — Deployment**: All existing AI-AAC systems assume cloud inference and reliable connectivity. The edge deployment constraints of commodity Android hardware in South African home-care settings — latency, memory, battery, offline-first requirement — have not been characterised for AI-assisted AAC applications.

The intersection of all four gaps is empty: no published work addresses AI-assisted AAC for adult Afrikaans-speaking stroke survivors, deployed on commodity offline hardware, with personalisation from sparse usage data. This is not a narrow or contrived gap — it is the exact intersection of a clinical need, a language technology vacuum, a deployment constraint, and a design problem that no existing research addresses.

---

## Section 8 — PhD Framing Options: What the Literature Supports

### Option A — "Intelligent AAC with Features A+B" (Recommended)

The literature directly motivates and supports a PhD that builds, deploys, and evaluates an intelligent Afrikaans AAC system incorporating:

- **Feature A (word-level prediction)**: @trnka-2009-word-prediction-aac establish the 61% communication rate improvement from high-quality prediction; @gaines-2025-llm-aac provide the LLM methodology; @hedderich-2021-lowresource-nlp and @adelani-2021-masakhaner provide the transfer learning path for Afrikaans; @hattingh-2020-afrikaans-vocab and @winter-2025-afrikaans-vocab confirm that the vocabulary corpus must be constructed from adult data.
- **Feature B (listen-and-suggest)**: @ferguson-1994-conversational-repair motivates the joint repair model; @mao-2025-ai-aac-aphasia provide design probe evidence that keyword-to-sentence generation is the most positively received AI-AAC capability; @vanvaals-2024-llm-broca provide the technical pipeline; @wet-2011-afrikaans-asr and @jacobs-2025-afrikaans-asr establish the ASR feasibility baseline for Afrikaans.
- **Personalisation**: @dipaola-2024-llm-aac establish the federated/on-device personalisation architecture; the PhD contribution is characterising and solving the sparse-feedback regime.
- **DSR methodology**: @hevner-2004-dsr provides the methodological scaffold.

This framing produces three publishable contributions at AI-relevant venues (African language NLP corpus + model; ASR + generation pipeline; personalisation framework), satisfies all three goals (AI credibility, applied rigour, Vodacom leverage), and is intellectually honest — the AI systems are real, inference runs at deployment time, and the research gaps are genuine.

**What this requires beyond the current artefact:** Adult Afrikaans clinical vocabulary elicitation (N=1 initially, ethics for N≥5 for statistical credibility), corpus annotation, model development, Features A+B implementation, longitudinal deployment evaluation.

### Option B — "African Language NLP + Edge AI, no new features"

The literature also supports a more conservative framing in which the PhD produces the vocabulary corpus and NLP model without integrating them into the live artefact. This is a genuine AI research contribution and satisfies the Vodacom leverage and AI credibility goals, but at reduced strength: the AI never runs in the deployed system, which limits the "applied research" claim and weakens the product story for Vodacom. This option is best understood as the first phase of Option A, not as a complete PhD.

### Option C — "Pure DSR / HCI AAC"

The literature does not support this as the primary framing for a researcher with an MSc in Data Science & AI. The evidence base for AAC in aphasia is well-established [@russo-2017-hightech-aac-aphasia; @johnson-2008-aac-severe-aphasia]; a DSR PhD that merely deploys an existing stored-message design without AI contributions would be difficult to distinguish from system-building. The AI credibility goal is not met.

---

## References

[@beukelman-2020-aac] D. R. Beukelman and J. C. Light, *Augmentative and Alternative Communication: Supporting Children and Adults with Complex Communication Needs*, 5th ed. Baltimore, MD: Paul H. Brookes Publishing, 2020.

[@brady-2021-release] RELEASE Collaborators and M. C. Brady et al., "Predictors of Poststroke Aphasia Recovery: A Systematic Review-Informed Individual Participant Data Meta-Analysis," *Stroke*, vol. 52, no. 5, pp. 1778–1787, 2021. doi: 10.1161/STROKEAHA.120.031162.

[@koul-2011-aac-aphasia] R. Koul and A. R. Beck, *Augmentative and Alternative Communication for Adults with Aphasia: Science and Clinical Practice*. Leiden: Brill Academic Publishers, 2011.

[@hattingh-2020-afrikaans-vocab] D. Hattingh and K. M. Tönsing, "The core vocabulary of South African Afrikaans-speaking Grade R learners without disabilities," *South African Journal of Communication Disorders*, vol. 67, no. 1, 2020. doi: 10.4102/sajcd.v67i1.701.

[@winter-2025-afrikaans-vocab] P. Winter, J. van der Linde, F. de Wet, M. A. Graham, and J. Bornman, "Using Secondary Data Analysis to Compare Core Vocabulary Lists and Elicitation Duration of Two Data Sets of Typically Developing Preschool Afrikaans-Speaking Children," *Folia Phoniatrica et Logopaedica*, 2025. doi: 10.1159/000546919.

[@odendaal-2024-aac-aphasia-slp] I. Odendaal and K. M. Tönsing, "Augmentative and alternative communication for individuals with post-stroke aphasia: perspectives of South African speech-language pathologists," *Augmentative and Alternative Communication*, vol. 41, no. 1, pp. 56–64, 2024. doi: 10.1080/07434618.2024.2374303.

[@russo-2017-hightech-aac-aphasia] M. J. Russo et al., "High-technology augmentative communication for adults with post-stroke aphasia: a systematic review," *Expert Review of Medical Devices*, vol. 14, no. 5, pp. 355–370, 2017. doi: 10.1080/17434440.2017.1324291.

[@johnson-2008-aac-severe-aphasia] R. K. Johnson et al., "Functional Communication in Chronic Severe Aphasia Using Augmentative Communication," *Augmentative and Alternative Communication*, vol. 24, no. 4, pp. 269–280, 2008. doi: 10.1080/07434610802463957.

[@ferguson-1994-conversational-repair] A. Ferguson, "The influence of aphasia, familiarity and activity on conversational repair," *Aphasiology*, vol. 8, no. 2, pp. 143–157, 1994. doi: 10.1080/02687039408248647.

[@trnka-2007-corpus-word-prediction] K. Trnka and K. F. McCoy, "Corpus studies in word prediction," in *Proc. ASSETS '07*, 2007. doi: 10.1145/1296843.1296877.

[@trnka-2009-word-prediction-aac] K. Trnka, J. S. Yaruss, and K. F. McCoy, "User Interaction with Word Prediction: The Effects of Prediction Quality," in *Proc. ASSETS '09*, 2009. doi: 10.1145/1497302.1497307.

[@dipaola-2024-llm-aac] G. Di Paola et al., "Foundation Models in AAC: Opportunities and Challenges," arXiv:2401.08866, 2024.

[@gaines-2025-llm-aac] B. Gaines and K. Vertanen, "Adapting LLMs for Character-based Augmentative and Alternative Communication," in *Proc. EMNLP 2025*, arXiv:2501.10582, 2025.

[@mao-2025-ai-aac-aphasia] W. Mao et al., "Design Probes for AI-Driven AAC: Addressing Complex Communication Needs in Aphasia," in *Proc. DIS '25*, 2025. doi: 10.1145/3715336.3735736.

[@vanvaals-2024-llm-broca] L. van Vaals et al., "Generating Completions for Broca's Aphasic Sentences Using LLMs," *IEEE Journal of Biomedical and Health Informatics*, 2024. doi: 10.1109/JBHI.2025.3639109.

[@martinus-2019-masakhane] L. Martinus and J. Z. Abbott, "A Focus on Neural Machine Translation for African Languages," arXiv:1906.05685, 2019.

[@nekoto-2020-participatory-nlp] W. Nekoto et al., "Participatory Research for Low-resourced Machine Translation: A Case Study in African Languages," in *Findings of EMNLP 2020*, 2020. doi: 10.18653/v1/2020.findings-emnlp.195.

[@nekete-2020-masakhane] I. Orife et al., "Masakhane — Machine Translation For Africa," arXiv:2003.11529, 2020.

[@adelani-2021-masakhaner] D. I. Adelani et al., "MasakhaNER: Named Entity Recognition for African Languages," *Transactions of the Association for Computational Linguistics*, vol. 9, pp. 1116–1131, 2021. doi: 10.1162/tacl_a_00416.

[@adelani-2022-masakhaner2] D. I. Adelani et al., "MasakhaNER 2.0: Africa-centric Transfer Learning for Named Entity Recognition," in *Proc. EMNLP 2022*, arXiv:2210.12391, 2022.

[@hedderich-2021-lowresource-nlp] M. A. Hedderich et al., "A Survey on Recent Approaches for Natural Language Processing in Low-Resource Scenarios," in *Proc. NAACL-HLT 2021*, 2021. doi: 10.18653/V1/2021.NAACL-MAIN.201.

[@wet-2011-afrikaans-asr] F. de Wet, A. de Waal, and G. B. van Huyssteen, "Developing a Broadband Automatic Speech Recognition System for Afrikaans," in *Proc. Interspeech 2011*, 2011. doi: 10.21437/Interspeech.2011-797.

[@jacobs-2025-afrikaans-asr] G. Jacobs et al., "Speech Recognition for Automatically Assessing Afrikaans and isiXhosa Preschool Oral Narratives," in *Proc. ICASSP 2025*, arXiv:2501.06478, 2025. doi: 10.1109/ICASSP49660.2025.10889916.

[@hevner-2004-dsr] A. R. Hevner, S. T. March, J. Park, and S. Ram, "Design Science in Information Systems Research," *MIS Quarterly*, vol. 28, no. 1, pp. 75–105, 2004. doi: 10.2307/25148625.
