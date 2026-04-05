# fetch-page-auth

Fetch a URL using your real Chrome cookies injected into a headless Playwright browser. Fully invisible — no Chrome window opened, your normal Chrome is completely untouched.

Use this for:
- Paywalled journal sites you are logged into (ScienceDirect, Springer, IEEE Xplore, Wiley)
- ResearchGate, Academia.edu (logged-in view)
- Gmail, Google Scholar (logged-in view)
- LinkedIn (authenticated profile pages)
- UNISA student portal or library resources
- Any site where anonymous access returns a paywall or login prompt

**Usage:** `/fetch-page-auth <url> <cookie-domain> [options]`

**Options:**
- `--html` — return raw HTML source instead of inner_text (use this first for DOM inspection before writing click scripts)
- `--click "sel1,sel2"` — CSS selectors to click after page load (comma-separated; inspect DOM with `--html` first to find correct selectors)
- `--wait "selector"` — wait for a CSS selector to appear before extracting (more reliable than blind sleep)
- `--scroll` — scroll to bottom incrementally before extracting (triggers lazy-load)
- `--wait-seconds N` — override default wait time (default: 8s)

## When to use vs alternatives

| Situation | Tool |
|-----------|------|
| Public REST API (Semantic Scholar, arXiv API) | `curl` — fastest, no browser needed |
| Public JS-rendered page (IRRODL, SAJIM, Sci-Hub) | `/fetch-page` — anonymous headless Chromium |
| Site you are **actually logged into** in Chrome | `/fetch-page-auth` — this skill |
| Paywalled and NOT logged in (IEEE Xplore, ScienceDirect, Springer) | `curl https://sci-hub.se/<doi>` |
| PDF download | `wget` or `curl -L -o file.pdf <url>` |

## Cookie domains

| Site | Domain argument |
|------|----------------|
| Gmail, Google Scholar | `.google.com` |
| ScienceDirect | `.sciencedirect.com` |
| Springer | `.springer.com` |
| IEEE Xplore | `.ieee.org` |
| LinkedIn | `.linkedin.com` |
| ResearchGate | `.researchgate.net` |
| Academia.edu | `.academia.edu` |

**Prerequisite:** `browser_cookie3` must be installed in the `afrikaans-aac` env:

```bash
conda run -n afrikaans-aac pip install browser-cookie3
```

On first use macOS will prompt for your **Mac login password** to decrypt the Chrome cookie store from Keychain. This is a standard macOS security prompt — enter your login password (same one used to unlock your Mac).

---

## Two-pass workflow for sites with collapsed content

Many sites (LinkedIn, Google Scholar, journal pages) hide content behind "Show more" / "Show all" buttons. You cannot know the correct CSS selectors in advance. Use this two-pass approach:

**Pass 1 — Inspect the DOM:**

```
/fetch-page-auth <url> <domain> --html
```

Read the raw HTML output. Find the selector for the "Show more" / expand button.

**Pass 2 — Extract with clicks:**

```
/fetch-page-auth <url> <domain> --click "button.show-more,a[data-action='expand']" --scroll
```

---

## How it works

`browser_cookie3` reads and decrypts cookies directly from your real Chrome profile on disk. They are injected into a headless Chromium context via Playwright. No Chrome window is opened. Your running Chrome is not touched.

---

## Execute

Always use a script file to avoid shell escaping issues:

```bash
conda run -n afrikaans-aac python /Users/johannes/code/unisa/unisa-phd-proposal/.claude/scripts/fetch_auth.py "$ARGUMENTS"
```

---

## Notes

- **`--html` first**: Always inspect the raw HTML before writing click selectors. Guessing selectors without seeing the DOM is unreliable.
- **`--scroll`**: Use for LinkedIn, Google Scholar results, and any site that lazy-loads content as you scroll.
- **`--wait "selector"`**: More reliable than `--wait-seconds` for SPAs — waits until a specific element appears in the DOM.
- **Multiple clicks**: `--click` will attempt every matching element for each selector. If a button disappears after clicking, subsequent clicks on missing elements are silently skipped.
- **Scroll + click order**: Scroll happens before clicks. This ensures lazy-loaded buttons are present before attempting to click them.
- **Keychain prompt**: macOS prompts once per session for your login password. After granting access, subsequent calls in the same session do not prompt again.
- **Cookie freshness**: Cookies are read live from Chrome's profile on disk — always current. No need to re-export.
- **Script file**: Always write to `/tmp/fetch_auth.py` — inline `-c` breaks on quotes and newlines.

---

## Security note

Cookies are read from your local Chrome profile on disk and used only for the single page fetch. They are not stored, logged, or transmitted anywhere. The headless browser opens one page and closes immediately.
