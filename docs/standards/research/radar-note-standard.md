# Radar Note Standard

A radar note is a structured record of a source that may be relevant to the
research but has not yet entered the formal literature pipeline
(`references.bib` → `literature/papers/` → `literature/mkv/`).

The radar corresponds to the **screening stage** in PRISMA systematic review
terminology and the **fleeting note** in Zettelkasten practice. A source on the
radar has been identified; it has not yet been read, evaluated, or formally cited.

---

## When to create a radar note

Create a radar note when:
- You encounter a YouTube video, talk, lecture, or podcast that looks relevant
- You find a blog post, web article, or grey literature document worth tracking
- A paper is flagged as potentially relevant but you do not yet have the PDF

Do **not** create a radar note for:
- Papers you are actively citing — these go through the full pipeline:
  bib entry → `literature/papers/<cite-key>.pdf` → `literature/mkv/<cite-key>.md`
- Sources you have already decided are irrelevant — set `status: archived` and move on

---

## File location and naming

```
literature/radar/<slug>.md
```

Naming convention:
| Source type | Slug format | Example |
| --- | --- | --- |
| YouTube video | `youtube-<title-slug>` | `youtube-chromas-new-20b-model.md` |
| Web article / blog | `web-<site>-<title-slug>` | `web-towardsdatascience-rag-chunking.md` |
| Conference talk (non-video) | `talk-<conf>-<title-slug>` | `talk-acl2024-retrieval-augmented.md` |
| Once a cite key is assigned | `<cite-key>` | `chroma-2026-context1.md` |

Raw transcripts (videos only) are saved separately:

```
literature/radar/transcripts/<slug>.txt
```

---

## Frontmatter schema

All fields are present in every note. Fields that do not apply are empty strings
or empty lists — never omitted — so automated queries work consistently.

```yaml
---
# IDENTITY
title: ""
type: video | web-article | blog | talk | podcast
url: ""
cite_key: ""           # empty until a bib entry exists; fill when source is integrated

# PROVENANCE
author: ""             # person(s) or channel name (CSL: author / director)
organisation: ""       # institution, conference, or publisher behind the source
site_name: ""          # blog/site name for web sources (CSL: container-title)
                       # channel name or conference series for videos
date_published: ""     # YYYY-MM-DD or YYYY — when the source was published (CSL: issued)
date_accessed: ""      # YYYY-MM-DD — when you retrieved it (web sources can disappear)
duration: ""           # HH:MM:SS or MM:SS — video/podcast only; empty otherwise
platform: ""           # YouTube | Vimeo | conference-server | etc.; empty for non-video

# WORKFLOW
date_added: ""         # YYYY-MM-DD — when it entered this radar
status: unread         # see status vocabulary below
tags: []               # topic keywords, e.g. [rag, bm25, odl, sdl, evaluation]
priority: medium       # low | medium | high

# TRIAGE
relevance: ""          # one sentence: why is this potentially relevant to the research?
transcript_path: ""    # relative path to raw transcript; empty for non-video sources
---
```

### Status vocabulary

Mirrors the PRISMA systematic review pipeline stages:

| Status | Meaning | PRISMA equivalent |
| --- | --- | --- |
| `unread` | Identified, not yet watched/read | Identified |
| `skimmed` | Briefly scanned; triage decision made | Screened |
| `watched` | Fully watched/read; no synthesis yet | Eligibility assessed |
| `processed` | Summary, key claims, and relevance notes written | Data extracted |
| `integrated` | `cite_key` set; bib entry exists; in `literature/index.md` | Included |
| `archived` | Reviewed; decided not relevant | Excluded |

A note created by `/transcribe-youtube` starts at `processed` because the
transcript exists and Claude has already generated a summary and key claims.
A note created manually for a URL you have not yet read starts at `unread`.

---

## Body structure

```markdown
# <Title>

## Why on radar
One paragraph: what about this source is potentially relevant to the RAG-for-ODL
research, and which research question(s) it might speak to (RQ1–RQ4).

## Source quality
One sentence: is this peer-reviewed, industry/practitioner, tutorial, grey
literature, or opinion? What is the credibility basis?
This prevents treating a YouTube tutorial equivalently to a conference paper.

## Summary
2–4 sentences summarising the main argument or content.
For video notes created by /transcribe-youtube this is Claude-generated from the
transcript. Update it after watching if the AI summary is inaccurate.

## Key claims
- Main point extracted from source
- Another main point
- ...

## Connections to research
- Links to related radar notes, proposal sections, or research questions
- e.g. "Relevant to §3.4 Retrieval Component" or "See also RQ2"

## Transcript / Notes
For videos: link to the raw transcript in literature/radar/transcripts/.
For web articles: paste key excerpts or your reading notes here.
For unread sources: leave empty until you read/watch it.
```

---

## Graduation to the formal literature pipeline

A radar note graduates when you decide the source is citable in the proposal.
The graduation steps are:

1. Obtain the PDF (or establish it is a non-paper source with a stable URL)
2. Add a BibTeX entry to `references/references.bib` using the standard cite-key
   format: `firstauthor-year-keyword`
3. For papers: save PDF to `literature/papers/<cite-key>.pdf` and convert to
   `literature/mkv/<cite-key>.md` per the PDF-to-Markdown workflow in CLAUDE.md
4. Set `cite_key` in the radar note frontmatter to the new key
5. Set `status: integrated`
6. Add an entry to `literature/index.md` (the annotated bibliography)
7. Rename the radar note file to `<cite-key>.md` if it was previously named by slug

The radar note is **not deleted** on graduation — it becomes a permanent record
of when the source was first identified and why it was considered relevant.

---

## Creating radar notes

### For YouTube videos — automated pipeline

```bash
/transcribe-youtube <url> --relevance "<why relevant>"
```

This downloads the audio, transcribes locally with MLX Whisper, generates a
summary and key claims via Claude (Bedrock), and writes the full structured note.

See [.claude/commands/transcribe-youtube.md](../.claude/commands/transcribe-youtube.md)
for full options including `--transcript-dir`, `--radar-dir`, and `--no-synthesis`.

### For web articles and other URLs — manual or semi-automated

1. Create `literature/radar/<slug>.md` with the frontmatter schema above
2. Set `status: unread`
3. Use `/fetch-page <url>` to retrieve the page text if needed
4. Fill in `## Summary` and `## Key claims` after reading
5. Update `status` to `processed` when synthesis is complete

Claude can assist: paste the URL and ask "add this to the radar" — Claude will
fetch the page, generate the structured note, and save it to `literature/radar/`.

---

## Relation to other literature files

```
literature/
  radar/           ← screening stage (this standard)
    transcripts/   ← raw transcripts from /transcribe-youtube
  papers/          ← formal pipeline: PDFs (cite-key named)
  mkv/             ← formal pipeline: full-text Markdown conversions (cite-key named)
  index.md         ← annotated bibliography for integrated sources
  README.md        ← full literature workflow documentation
```

Radar notes are the intake layer. They do not feed directly into the proposal —
a source must complete the graduation steps above before it can be cited.
