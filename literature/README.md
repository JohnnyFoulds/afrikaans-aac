# Literature Directory — Structure and Workflow

This directory holds the physical source material for every citation used in the
PhD proposal. It is organised around a single principle: **the BibTeX cite key is
the canonical identifier for a paper**, and every file related to that paper uses
that key as its filename stem.

---

## Directory layout

```
literature/
  papers/    — original PDFs, named <cite-key>.pdf
  mkv/       — full-text Markdown conversions, named <cite-key>.md
  img/       — images extracted during OCR conversion
    <cite-key>/
      img-0000.jpeg
      img-0001.jpeg
      ...
```

`mkv` stands for **Markdown conversions** (historical shorthand). Despite the
unfortunate collision with the video container format, the name is kept for
continuity.

`img/<cite-key>/` is only created when a PDF contains embedded figures (i.e. when
Mistral OCR extracts images). Journal articles typically have no `img/` directory;
books with figures do. MKV files reference images with relative paths:
`../img/<cite-key>/img-NNNN.jpeg` — these render inline in Obsidian and VS Code.

---

## The link: cite key → PDF → Markdown → BibTeX → proposal

```
literature/references.bib          — source of truth for cite keys and metadata
        │
        │  cite key (e.g. lewis-2020-rag)
        ├──────────────────────────────────┬──────────────────────────────┐
        │                                  │                              │
literature/papers/lewis-2020-rag.pdf  literature/mkv/lewis-2020-rag.md  literature/img/lewis-2020-rag/
   (original PDF)                       (full-text Markdown)              (extracted figures, if any)
                                                   │
                                    used by verify-claims.py for
                                    strong citation verification
                                                   │
proposal/01-introduction.md        proposal/03-literature-review.md  ...
   [@lewis-2020-rag] ...                [@lewis-2020-rag] ...
```

**Rule:** every file in `papers/` and `mkv/` must be named exactly `<cite-key>.ext`,
where `<cite-key>` is the entry key from `references/references.bib`. No journal
article IDs, no ERIC accession numbers, no descriptive names, no author-year
variants — only the bib cite key.

---

## Adding a new paper — step by step

### 1. Add the BibTeX entry first

Open `references/references.bib` and add a new entry. Choose a cite key following
the convention `firstauthor-year-keyword` (e.g. `robertson-2009-bm25`).

```bibtex
@article{robertson-2009-bm25,
  author  = {Robertson, Stephen and Zaragoza, Hugo},
  title   = {The Probabilistic Relevance Framework: {BM25} and Beyond},
  year    = {2009},
  doi     = {10.1561/1500000019},
}
```

The cite key you choose here becomes the canonical filename stem for everything
that follows.

### 2. Get the PDF

Download the PDF and save it as `literature/papers/<cite-key>.pdf`.

Sources (in order of preference):

**1. Unpaywall** — legal, free; try first for post-2018 papers:

```bash
curl "https://api.unpaywall.org/v2/<doi>?email=your@email.com"
# use best_oa_location.url_for_pdf from the response
```

**2. arXiv:**

```bash
curl -L -o literature/papers/<cite-key>.pdf https://arxiv.org/pdf/<id>
```

**3. Anna's Archive** — books and paywalled papers; requires membership key in `.env`; see `notes/pdf-acquisition.md` for setup:

```bash
source .env
ANNAS_DOWNLOAD_PATH=literature/papers annas-mcp book-search "<title author year>"
ANNAS_DOWNLOAD_PATH=literature/papers annas-mcp book-download <md5> <cite-key>.pdf
# or for articles by DOI:
ANNAS_DOWNLOAD_PATH=literature/papers annas-mcp article-download "<doi>"
# rename to <cite-key>.pdf if needed
```

**4. scidownl** — Sci-Hub with automatic working-domain discovery:

```bash
scidownl download --doi <doi> --out literature/papers/
# rename to <cite-key>.pdf
```

**5. Sabinet / journals.co.za** — African journals; Cloudflare blocks all automation. Open Chrome → `https://journals.co.za/doi/<doi>` → click PDF → download → save as `literature/papers/<cite-key>.pdf`.

### 3. Convert the PDF to Markdown

Three methods, in order of preference. Use Bedrock for journal articles; Mistral OCR for books or scanned PDFs.

**Method 1 — Bedrock streaming** (journal articles, ≤100 pages, text-based PDFs):

```bash
conda run -n claude-llm python3 -c "
import boto3, base64, json
from pathlib import Path
from botocore.config import Config

client = boto3.client('bedrock-runtime', region_name='eu-west-1',
    config=Config(read_timeout=600, connect_timeout=60))
model_id = 'arn:aws:bedrock:eu-west-1:557116085116:application-inference-profile/vb6ydtnx7fbs'

pdf_b64 = base64.standard_b64encode(Path('literature/papers/<cite-key>.pdf').read_bytes()).decode('ascii')
body = json.dumps({
    'anthropic_version': 'bedrock-2023-05-31',
    'max_tokens': 64000,
    'messages': [{'role': 'user', 'content': [
        {'type': 'document', 'source': {'type': 'base64', 'media_type': 'application/pdf', 'data': pdf_b64}},
        {'type': 'text', 'text': 'Convert this academic paper to clean Markdown. Preserve all sections and headings. Render equations in LaTeX. Include all tables, figure captions, and footnotes. Do not summarise — output the full paper text verbatim.'}
    ]}]
})
response = client.invoke_model_with_response_stream(modelId=model_id, body=body)
chunks = []
for event in response['body']:
    chunk = json.loads(event['chunk']['bytes'])
    if chunk.get('type') == 'content_block_delta':
        chunks.append(chunk['delta'].get('text', ''))
text = ''.join(chunks)
Path('literature/mkv/<cite-key>.md').write_text(text, encoding='utf-8')
print(f'done — {len(text)} chars written')
"
```

Bedrock rejects PDFs that are: (a) over 100 pages, (b) scanned/image-based, or (c) copyright-fingerprinted. Use Mistral OCR in those cases.

**Method 2 — Mistral OCR** (books, scanned PDFs, or Bedrock rejections):

Mistral OCR handles scanned pages, extracts embedded figures, and has no page-count limit per call (tested up to 453 pages in 100-page chunks). It also extracts images, which are saved to `literature/img/<cite-key>/` and referenced from the MKV with relative paths.

```bash
conda run -n claude-llm python3 -c "
import sys, base64, fitz, time
sys.path.insert(0, '/opt/homebrew/Caskroom/miniconda/base/envs/aib-genai-agent-core-session-manager/lib/python3.12/site-packages')
from mistralai.client.sdk import Mistral
from pathlib import Path

CITE_KEY = '<cite-key>'
CHUNK = 100  # pages per API call; reduce to 50 if timeouts occur

client = Mistral(api_key=__import__('os').environ['MISTRAL_API_KEY'])
doc = fitz.open(f'literature/papers/{CITE_KEY}.pdf')
img_dir = Path(f'literature/img/{CITE_KEY}')
img_dir.mkdir(parents=True, exist_ok=True)
rel_prefix = f'../img/{CITE_KEY}/'

all_text, global_img_idx = [], 0
for start in range(0, doc.page_count, CHUNK):
    end = min(start + CHUNK, doc.page_count)
    print(f'pages {start+1}-{end}...')
    chunk = fitz.open()
    chunk.insert_pdf(doc, from_page=start, to_page=end-1)
    pdf_b64 = base64.standard_b64encode(chunk.write()).decode('ascii')
    chunk.close()
    result = client.ocr.process(
        model='mistral-ocr-latest',
        document={'type': 'document_url', 'document_url': f'data:application/pdf;base64,{pdf_b64}'},
        include_image_base64=True
    )
    img_map = {}
    for page in result.pages:
        for img in (page.images or []):
            ext = img.id.rsplit('.', 1)[-1] if '.' in img.id else 'jpeg'
            name = f'img-{global_img_idx:04d}.{ext}'
            global_img_idx += 1
            if img.image_base64:
                (img_dir / name).write_bytes(base64.b64decode(img.image_base64))
            img_map[img.id] = name
    parts = []
    for page in result.pages:
        md = page.markdown
        for local, name in img_map.items():
            md = md.replace(f']({local})', f']({rel_prefix}{name})')
        parts.append(md)
    all_text.append('\n\n'.join(parts))
    if end < doc.page_count:
        time.sleep(10)

Path(f'literature/mkv/{CITE_KEY}.md').write_text('\n\n---\n\n'.join(all_text), encoding='utf-8')
print(f'done — {global_img_idx} images, {sum(len(t) for t in all_text)} chars')
"
```

Load `MISTRAL_API_KEY` from `.env` before running, or inline it. If no images are extracted (journal article), the `img/<cite-key>/` directory will be empty — delete it.

**Method 3 — Anthropic API direct** (fallback if Bedrock returns a content-filtering error):

Same as Method 1 but use `ANTHROPIC_API_KEY` from `.env` with the direct API instead of Bedrock. See `CLAUDE.md` for details.

### 4. Cite in the proposal

Use the standard APA author-year format in `proposal/*.md`:

```
Lewis et al. (2020) demonstrated ...
... as shown in the literature (Lewis et al., 2020).
```

The `verify-claims` tool (`/verify-claims`) will automatically resolve these
author-year citations back to the bib entry, locate the mkv file, and perform
strong citation verification — but only if the naming convention is followed.

---

## Verification: check naming consistency

```bash
python3 -c "
import re
from pathlib import Path
bib_keys = set(re.findall(r'^@\w+\{([^,\s]+),', Path('literature/references.bib').read_text(), re.MULTILINE))
papers = {p.stem for p in Path('literature/papers').glob('*.pdf')}
mkv = {p.stem for p in Path('literature/mkv').glob('*.md')}
print('PDFs not matching bib key:', papers - bib_keys)
print('MKVs not matching bib key:', mkv - bib_keys)
print('In bib, no PDF:', sorted(bib_keys - papers))
print('In bib, no MKV:', sorted(bib_keys - mkv))
"
```

Run this before committing any new literature files.

---

## Current state (as of 2026-04-05)

| Has PDF + MKV | Has PDF only | Has MKV only | BIB only (not yet downloaded) |
|:---:|:---:|:---:|:---:|
| 14 | 0 | 0 | 0 |

### Academic papers (4)

| Cite key | Description | PDF | MKV |
|---|---|:---:|:---:|
| `beukelman-2020-aac` | Beukelman & Light (2020) — *AAC* 5th ed., Paul H. Brookes | ✓ | ✓ |
| `hattingh-2020-afrikaans-vocab` | Hattingh & Tönsing (2020) — Afrikaans Grade R core vocab, SAJCD | ✓ | ✓ |
| `koul-2011-aac-aphasia` | Koul & Beck (2011) — *AAC for Adults with Aphasia*, Brill | ✓ | ✓ |
| `odendaal-2022-sa-slts` | Odendaal (2022) — SA SLT perspectives on AAC for post-stroke aphasia, UP Master's | ✓ | ✓ |

### Clinical guides and communication boards (10)

| Cite key | Description | PDF | MKV |
|---|---|:---:|:---:|
| `bornman-2025-saslha-medical` | Bornman & Koekemoer (2025) — SASLHA Afrikaans Medical Context Board | ✓ | ✓ |
| `bornman-2025-saslha-school` | Bornman & Koekemoer (2025) — SASLHA Afrikaans School Board | ✓ | ✓ |
| `bornman-2025-saslha-preschool` | Bornman & Koekemoer (2025) — SASLHA Afrikaans Preschool Board | ✓ | ✓ |
| `caac-2025-healthcare-board` | UP CAAC (2025) — Afrikaans Healthcare Communication Board | ✓ | ✓ |
| `lowis-2024-caya-aac-aphasia` | Lowis et al. (2024) — CAYA AAC Resource for Aphasia | ✓ | ✓ |
| `touchchat-2024-aphasia-guide` | TouchChat (2024) — Communication Journey: Aphasia guide | ✓ | ✓ |
| `tobii-aphasia-therapy-guide` | Tobii Dynavox — Communication Activity and Therapy Guide for Aphasia | ✓ | ✓ |
| `tobii-aac-needs-assessment` | Tobii Dynavox — AAC Needs Assessment Guide | ✓ | ✓ |
| `weissling-aphasia-communication` | Weissling — Post-stroke aphasia communication strategies for non-SLPs | ✓ | ✓ |
| `stroke-comm-high-low-tech` | High/Low tech AAC after stroke — for non-SLP disciplines | ✓ | ✓ |

---

## Auto-fetch for missing papers

The `verify-claims` tool can automatically download and convert missing papers
when run with `--auto-fetch`. It tries arXiv first (for papers with an `eprint`
or arXiv URL in the bib entry), then Sci-Hub via DOI. The resulting mkv file is
saved using the bib cite key as the filename.

```bash
/verify-claims --context proposal/01-introduction.md --auto-fetch
```
