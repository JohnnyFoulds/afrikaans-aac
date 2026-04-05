# Literature Radar

Sources that may be relevant to the research but are not yet ready to enter the
formal literature pipeline (`references.bib` → `literature/papers/` → `literature/mkv/`).

**Full standard and rationale:** [docs/standards/research/radar-note-standard.md](../../docs/standards/research/radar-note-standard.md)

Each entry is a markdown file named by a short slug. When a source graduates to a
formal citation, a `cite_key` is added to the frontmatter and a proper bib entry is
created. The file stays in `radar/` until it is fully processed into `literature/index.md`.

---

## Status vocabulary

| Status | Meaning | Equivalent stage |
| --- | --- | --- |
| `unread` | Identified, not yet watched/read | PRISMA: identified |
| `skimmed` | Briefly scanned, triage complete | PRISMA: screened |
| `watched` | Video fully watched / article fully read | PRISMA: eligibility |
| `processed` | Summary and relevance notes written | PRISMA: data extraction |
| `integrated` | Cite key added; bib entry exists; in `literature/index.md` | PRISMA: included |
| `archived` | Reviewed and decided not relevant | PRISMA: excluded |

---

## Frontmatter schema

All fields are present in every entry. Fields that do not apply are left as empty
strings or empty lists — never omitted — so that automated queries are consistent.

```yaml
---
# IDENTITY
title: ""
type: video | web-article | blog | talk | podcast
url: ""
cite_key: ""           # fill once a bib entry exists; empty until then

# PROVENANCE
author: ""             # person(s) or channel name
organisation: ""       # institution, conference, or publisher behind the source
site_name: ""          # blog/site name (web) or channel/conference series (video)
date_published: ""     # YYYY-MM-DD or YYYY (when the source was published)
date_accessed: ""      # YYYY-MM-DD (when you retrieved it — web sources can disappear)
duration: ""           # HH:MM:SS or MM:SS; empty for non-video sources
platform: ""           # YouTube | Vimeo | conference-server | etc.; empty for non-video

# WORKFLOW
date_added: ""         # YYYY-MM-DD (when it entered this radar)
status: unread         # see status vocabulary above
tags: []               # topic keywords for filtering
priority: medium       # low | medium | high

# TRIAGE
relevance: ""          # one sentence: why is this potentially relevant to the research?
transcript_path: ""    # relative path to raw transcript file, if it exists
---
```

---

## Body structure

```markdown
# <Title>

## Why on radar
<One paragraph: what about this source is potentially relevant to the research,
and which research question(s) or design decisions it might speak to.>

## Source quality
<Brief note: is this peer-reviewed, industry/practitioner, grey literature, or
opinion? What is the credibility basis? This prevents treating a YouTube tutorial
equivalently to a conference paper.>

## Summary
<Summary of the main argument/content. At radar stage this may be auto-generated
from the transcript or page text. Update when you watch/read the source fully.>

## Key claims
- <bullet: main point>
- <bullet: main point>

## Connections to research
- Links to related notes, research questions, or proposal sections

## Transcript / Notes
<Raw transcript (for videos) or extracted text/notes (for web articles).>
```

---

## Naming convention

- Videos: `youtube-<title-slug>.md` until a cite key is assigned
- Web articles: `web-<site-slug>-<title-slug>.md` until a cite key is assigned
- Once a cite key is assigned: rename to `<cite-key>.md` (matches `references.bib`)
