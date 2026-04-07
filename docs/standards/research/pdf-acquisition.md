# Academic PDF and Book Acquisition

Operational reference for fetching PDFs needed by the literature pipeline.

---

## Web Fetching Tool Priority

**Rule:** `/fetch-page-auth` or `/fetch-page` (Playwright) as the default. Do NOT reach for curl or WebFetch first.

| Tool | Use case | Reliability |
| ---- | -------- | ----------- |
| `WebFetch` (Claude built-in) | Almost always bad | Fails on JS-rendered pages, blocked by academic sites |
| `curl` | Fast but fragile | DNS blocked for Sci-Hub/LibGen/Anna's Archive mirrors; empty bodies on JS-rendered sites |
| `/fetch-page` | Headless Playwright, anonymous | Renders JS; works for most public sites (Semantic Scholar, arXiv, IRRODL); not logged in |
| `/fetch-page-auth` | CDP against running Chrome | Full browser session with user's cookies/login; use for paywalled sites |

**Decision tree:**

- Public page with no login required → `/fetch-page`
- Paywalled or login-gated → `/fetch-page-auth`
- Known direct PDF URL (e.g. arXiv `arxiv.org/pdf/...`) → `curl -L -o file.pdf <url>`
- Public REST API (Semantic Scholar, Unpaywall, arXiv API) → `curl`
- Never: `WebFetch`

---

## Papers by DOI

### Unpaywall (free, legal — try first)

```bash
curl "https://api.unpaywall.org/v2/{doi}?email=your@email.com"
```

Returns JSON with `best_oa_location.url_for_pdf` when available. Legal open-access PDFs for a large fraction of 2018+ papers.

### Sci-Hub

**Status (March 2026):** `sci-hub.se` DNS-blocked; `sci-hub.st` connects but returns empty body via curl.

**Working approach:** Use `/fetch-page-auth` with Chrome logged into a working Sci-Hub mirror.

**Best CLI tool:** `scidownl` (pip) — auto-discovers working Sci-Hub domains:

```bash
pip install scidownl
scidownl download --doi 10.1109/ACCESS.2019.2934819 --out ./literature/papers/
```

---

## Books — Anna's Archive

### `annas-mcp` — the primary tool

**Repo:** `github.com/iosifache/annas-mcp` | Go binary | v0.0.5

Does four things: search books, download book by MD5, search articles (by DOI/keywords), download article by DOI.

**Binary installed at:** `~/bin/annas-mcp`

**CLI usage** (env vars from `.env`):

```bash
source .env
ANNAS_DOWNLOAD_PATH=~/Downloads/papers annas-mcp book-search "Yin case study research 2018"
ANNAS_DOWNLOAD_PATH=~/Downloads/papers annas-mcp book-download <md5> yin-2018.pdf
ANNAS_DOWNLOAD_PATH=~/Downloads/papers annas-mcp article-download "10.2307/25148625"
```

**MCP server:** registered in `~/.claude.json` as `anna-mcp`. After restarting Claude Code, you can ask it to download books/articles directly in conversation.

### Mirror status (March 2026)

| Domain | Status |
| ------ | ------ |
| `annas-archive.org` | DNS-blocked |
| `annas-archive.li` | DNS-blocked |
| `annas-archive.se` | DNS-blocked |
| `annas-archive.pm` | DNS-blocked |
| `annas-archive.in` | DNS-blocked |
| `annas-archive.gl` | **Active** |
| `annas-archive.pk` | **Active** |
| `annas-archive.gd` | **Active** |

Monitor: `open-slum.org`. Current `ANNAS_BASE_URL` in `.env`: `annas-archive.gl` (bare domain, no scheme).

### Anna's Archive API key

Donation-based. Donate at `annas-archive.gl`, retrieve key from `/account/secret_key`. Key stored in `.env` as `ANNAS_SECRET_KEY`.

Tiers: Tier 2 = 25 downloads/day at $7/month (minimum useful tier).

---

## New Laptop Setup

**Step 1 — Get Anna's Archive key.** Donate at `annas-archive.gl`, retrieve from `/account/secret_key`.

**Step 2 — Download `annas-mcp` binary:**

```bash
curl -L -o ~/bin/annas-mcp https://github.com/iosifache/annas-mcp/releases/download/v0.0.5/annas-mcp-darwin-arm64
chmod +x ~/bin/annas-mcp
~/bin/annas-mcp --version  # verify: v0.0.5
```

Check the releases page for a newer version and update the URL accordingly.

**Step 3 — Add keys to `.env`** in the project root:

```text
ANNAS_SECRET_KEY=<your-key>
ANNAS_BASE_URL=annas-archive.gl
```

Note: `ANNAS_BASE_URL` must be the bare domain — no `https://` prefix. The binary prepends the scheme itself; passing `https://annas-archive.gl` produces a doubled URL (`https://https//...`) and fails.

**Step 4 — Register `annas-mcp` as MCP server in Claude Code:**

```bash
claude mcp add --scope user anna-mcp -- ~/bin/annas-mcp mcp
```

Then edit `~/.claude.json` → find `mcpServers.anna-mcp.env` → set:

```json
{
  "ANNAS_SECRET_KEY": "<your-key>",
  "ANNAS_BASE_URL": "https://annas-archive.gl",
  "ANNAS_DOWNLOAD_PATH": "/Users/<you>/Downloads/papers"
}
```

Note: MCP servers go in `~/.claude.json`, NOT `~/.claude/settings.json` (that file rejects `mcpServers`).

**Step 5 — Create download directory:**

```bash
mkdir -p ~/Downloads/papers
```

**Step 6 — Restart Claude Code.** MCP server connects on startup. Test by asking Claude to search for a book.

**Step 7 — Check mirror if downloads fail.** Visit `open-slum.org` for current active mirrors, update `ANNAS_BASE_URL` in both `.env` and `~/.claude.json`.

---

## PDF-to-MKV Converter Tier Order

| Tier | Tool | Condition |
|------|------|-----------|
| 1 | Mistral OCR + Gemini (`--describe-images`) | **Default for all papers** — 95% cheaper than Bedrock; figures visible to humans (JPEG) and agents (`<details>` prose); handles copyright-blocked PDFs |
| 2 | Bedrock (Anthropic PDF API) | Fallback if `GEMINI_API_KEY` unavailable or Mistral API is down |

Run conversions via:

```bash
conda run -n aib-genai-agent-core-session-manager python3 scripts/mistral-ocr.py --cite-key <key> --describe-images
```

---

## Mistral OCR — Known Quirks

### Unclosed fences (callout boxes)

Mistral OCR occasionally wraps visually-boxed content (tip boxes, sidebars,
shaded callouts) in ` ```markdown ` fences **without a closing fence**.  Because
markdown fences do not nest, this causes every line from that point to end-of-file
to be hidden inside a code block — prose that should be readable text becomes a
raw code dump.

The `mistral-ocr.py` script detects this automatically after writing the MKV:
it walks the fence open/close state machine and removes any opening line that
has no matching close.  If triggered, it prints:

```text
WARNING: unclosed fence at line N ('```markdown') — removing spurious opening line.
```

**This is safe** because:

- Closed fences (balanced open + close) are never touched, regardless of length.
- Only an *unclosed* opening line — one with no matching close anywhere in the
  file — is removed.
- Legitimate long code listings are closed fences and are left intact.

If you see the warning, inspect the MKV around the reported line to confirm the
callout content reads correctly as prose.

### Italic citation brackets

Mistral OCR consistently wraps inline citations in italics: `*[1]*`, `*[2, 3]*` instead
of the standard `[1]`, `[2, 3]`.  Fixed automatically by `_fix_italic_citations()` —
strips the asterisks around any bracket whose content is digits, commas, and spaces.
Intentional italic markup elsewhere is not affected.

### Heading level collapse

Mistral OCR occasionally emits deep subsections at the wrong heading level — for
example, section `3.2.1` rendered as H1 (`#`) instead of H4 (`####`).  Fixed
automatically by `_fix_heading_levels()`: for headings whose text begins with a numeric
section number (e.g. `3`, `3.2`, `3.2.1`), the correct depth is inferred from the number
of dot-separated components (N components → H(N+1), capped at H6).  Headings without a
numeric prefix (Abstract, Introduction, etc.) are left exactly as Mistral produced them.

### Spaced math identifiers

When the source PDF uses tracked letter-spacing in display math, Mistral OCR spaces out
individual characters inside LaTeX commands:

```latex
\operatorname {A t t e n t i o n}
\text {e m b e d}
```

Fixed automatically by `_fix_spaced_math_identifiers()` — collapses single-character
tokens separated by spaces inside brace groups back to contiguous strings:
`\operatorname{Attention}`, `\text{embed}`.  Multi-character tokens are left untouched.

### Source PDF traceability comment

The script prepends `<!-- Source PDF: <filename>.pdf -->` to every MKV so the origin PDF
is traceable even if the file is moved or renamed.

---

## Books — Libgen (fallback)

```bash
# Search by title
curl "http://libgen.rs/json.php?q=yin+case+study+research&fields=id,title,author,md5,extension"

# Download by MD5
curl -L -o book.pdf "https://download.library.lol/main/<md5>"
```

---

## Cloudflare Bypass — FlareSolverr (last resort)

```bash
docker run -d --name flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest
```

Handles JS challenges but NOT interactive CAPTCHAs.
