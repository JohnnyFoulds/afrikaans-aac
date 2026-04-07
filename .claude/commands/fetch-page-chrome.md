# fetch-page-chrome

Download a file (PDF or otherwise) from a bot-protected site by instructing the
**running Chrome browser** via AppleScript to navigate to the URL and trigger the
download using Chrome's own session cookies.

Use this as the **last-resort fallback** when all other download methods fail due
to bot detection:

| Method | Fails when |
|--------|-----------|
| `wget` / `curl` | Site checks TLS fingerprint or `User-Agent` |
| `/fetch-page` (headless Playwright) | Site detects `navigator.webdriver`, absent human-interaction signals, or Cloudflare challenge |
| `/fetch-page-auth` (CDP) | Chrome not running with `--remote-debugging-port=9222` |
| Anna's Archive MCP | DOI misindexed; paper too new |
| Sci-Hub | Paper not indexed yet |
| `/mistral-ocr` | No PDF obtained yet |
| **`/fetch-page-chrome`** | **Almost nothing — Chrome has real cookies and a real TLS fingerprint** |

## Why this works

Chrome 127+ uses **App-Bound Encryption** for cookie storage: cookie values are
encrypted with a key tied to the Chrome process itself, making programmatic
decryption from outside the process impossible without the browser running.
Headless Playwright uses a separate Chromium binary with no cookies, triggering
bot-detection immediately.

AppleScript bypasses both problems by talking directly to the **running Chrome
app**: it creates a tab in the existing browser profile, navigating with the full
live session (all cookies, valid TLS handshake, real `User-Agent`). Chrome then
handles the download exactly as if the user clicked a link — using the same
cookies that were set during a real login session.

**Discovered 2026-03-26**: Used to download Li et al. 2025 (Computers and
Education: AI, DOI 10.1016/j.caeai.2025.100417) from ScienceDirect after
headless Playwright, curl, wget, Anna's Archive MCP, and Elsevier API all failed.
The paper is gold open-access but ScienceDirect serves bot-detection HTML to all
non-Chrome clients regardless.

## Requirements

- Chrome must be **running** (does not need `--remote-debugging-port`)
- The user must be **logged in** (or the page must be freely accessible with a
  real browser — gold OA articles on ScienceDirect work without login)
- macOS only (AppleScript)

## Usage

**`/fetch-page-chrome <url>`**

The skill navigates Chrome to `<url>`, waits for the download to land in
`~/Downloads/`, identifies the new file, and prints its path.

Typical use: provide the direct PDF download URL (e.g. a ScienceDirect `pdfft`
URL), not the landing page.

### Finding the direct PDF URL for ScienceDirect

For a ScienceDirect article with PII `S2666920X25000578`, the direct PDF URL is:

```
https://www.sciencedirect.com/science/article/pii/S2666920X25000578/pdfft?isDTMRedir=true&download=true
```

The PII can be found from:
1. DOAJ API: `curl "https://doaj.org/api/search/articles/doi:<doi>"` — check
   `bibjson.link[].url` for a ScienceDirect article URL containing the PII
2. Crossref: `curl "https://api.crossref.org/works/<doi>"` — check `link[]` array
3. The DOI redirect itself: `curl -sIL "https://doi.org/<doi>"` — final redirect
   URL contains the PII

## Execute

```bash
osascript -e "tell application \"Google Chrome\" to open location \"$ARGUMENTS\""
sleep 8
# Find the most recently modified PDF in ~/Downloads
LATEST=$(ls -t ~/Downloads/*.pdf 2>/dev/null | head -1)
echo "Downloaded: $LATEST"
file "$LATEST"
```

After running:

1. Verify the downloaded file is actually a PDF (`file` command output must say
   `PDF document`) — ScienceDirect sometimes returns an HTML error page if the
   article requires login or the URL is wrong.
2. Check the filename matches the expected paper (not a previously downloaded
   file with an older timestamp).
3. Copy to `literature/papers/<cite-key>.pdf`.
4. Follow up with Bedrock conversion (see CLAUDE.md) to create the MKV.

## Notes

- **Download directory**: Chrome saves to `~/Downloads/` by default. If the user
  has changed Chrome's download location, adjust accordingly.
- **Timing**: `sleep 8` is usually sufficient for a 2–5 MB PDF on a fast
  connection. Increase to `sleep 15` for large files or slow connections.
- **Multiple tabs**: The skill opens a new tab in a new window. Close it after
  confirming the download.
- **Not for login-required content**: This skill works for gold OA and any page
  accessible to a logged-in user. It does not bypass a paywall — it uses whatever
  access the browser session already has.
- **Alternative for non-PDF downloads**: Works for any file type Chrome can
  download (DOCX, ZIP, etc.) — not limited to PDFs.
