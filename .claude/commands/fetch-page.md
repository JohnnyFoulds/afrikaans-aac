# fetch-page

Fetch a URL using a headless anonymous Playwright Chromium browser and return the full rendered page text.

Use this for:
- Semantic Scholar, arXiv, IRRODL, SAJIM, and other public academic sites
- Any page that requires JavaScript rendering (React/Next.js SPAs)
- Sites where curl/wget returns empty or minimal HTML

**Usage:** `/fetch-page <url> [options]`

**Options:**
- `--html` — return raw HTML source instead of inner_text (use this first for DOM inspection before writing click scripts)
- `--click "sel1,sel2"` — CSS selectors to click after page load (comma-separated; inspect DOM with `--html` first to find correct selectors)
- `--wait "selector"` — wait for a CSS selector to appear before extracting (more reliable than blind sleep)
- `--scroll` — scroll to bottom incrementally before extracting (triggers lazy-load)
- `--wait-seconds N` — override default wait time (default: 5s)

## When to use vs alternatives

| Situation | Tool |
|-----------|------|
| Public REST API (Semantic Scholar, arXiv API) | `curl` — faster and simpler |
| JS-rendered page, anonymous | `/fetch-page` |
| Site you are **actually logged into** in Chrome | `/fetch-page-auth` |
| Paywalled and NOT logged in (IEEE, ScienceDirect, Springer) | `curl https://sci-hub.se/<doi>` |
| PDF download | `wget` or `curl -L -o file.pdf <url>` |

## Two-pass workflow for sites with collapsed content

Many sites (LinkedIn, Google Scholar, journal pages) hide content behind "Show more" / "Show all" buttons. You cannot know the correct CSS selectors in advance. Use this two-pass approach:

**Pass 1 — Inspect the DOM:**
```
/fetch-page <url> --html
```
Read the raw HTML output. Find the selector for the "Show more" / expand button.

**Pass 2 — Extract with clicks:**
```
/fetch-page <url> --click "button.show-more,a[data-action='expand']" --scroll
```

## Execute

Write the script to `/tmp/fetch_page.py` and run it:

```bash
conda run -n afrikaans-aac python /Users/johannes/code/personal/afrikaans-aac/.claude/scripts/fetch_page.py "$ARGUMENTS"
```

Then read and summarise the page content for the user.

## Notes

- **`--html` first**: Always inspect the raw HTML before writing click selectors. Guessing selectors without seeing the DOM is unreliable.
- **`--scroll`**: Use for LinkedIn, Google Scholar results, and any site that lazy-loads content as you scroll.
- **`--wait "selector"`**: More reliable than `--wait-seconds` for SPAs — waits until a specific element appears in the DOM.
- **Multiple clicks**: `--click` will attempt every matching element for each selector. If a button disappears after clicking, subsequent clicks on missing elements are silently skipped.
- **Scroll + click order**: Scroll happens before clicks. This ensures lazy-loaded buttons are present before attempting to click them.
