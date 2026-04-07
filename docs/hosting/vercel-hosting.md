# Vercel Hosting Guide — Pa se App

## Overview

Pa se App is a vanilla HTML/CSS/JS PWA with no build step and no server-side logic. It serves a phrase bank (`phrases.json`) and 78 pre-generated Afrikaans TTS audio files (`audio/*.mp3`, 1.1 MB total). Vercel's Hobby (free) tier hosts this class of application natively — you point it at the `src/` directory and it serves everything from a global CDN behind automatic HTTPS.

The Vercel deployment is **additive**. The tablet (Termux localhost server, Chrome fullscreen PWA) continues unchanged. Vercel gives family members remote access from any device and phone, and provides an off-device backup of the full working app.

---

## Vercel Free Tier — Confirmed Limits (2025)

| Limit | Hobby (free) | This app |
| --- | --- | --- |
| Bandwidth per month | 100 GB | ~1.1 MB per full cache warm (trivial) |
| Files per deployment | 15,000 max | 82 files |
| HTTPS / SSL | Automatic (Let's Encrypt) | ✓ |
| CDN | Global edge network | ✓ same as paid |
| Custom domain | Free, up to 50 per project | ✓ |
| Password protection | Not included — see §Access Control | Edge Middleware workaround |
| Commercial use | Restricted (personal/research OK) | ✓ research use |

---

## Architecture: What Changes, What Stays the Same

### What changes

| File | Status | Purpose |
| --- | --- | --- |
| `vercel.json` | **New** (repo root) | Tell Vercel to serve `src/`, set cache headers |
| `src/sw.js` | **New** | Service worker — full offline support after first visit |
| `src/icon.svg` | **New** | PWA home screen icon (was `"icons": []`) |
| `middleware.ts` | **New** (repo root) | Edge Middleware password gate |
| `src/manifest.json` | **Modified** | Added `icons` array |
| `src/index.html` | **Modified** | Added SW registration (9 lines near `</body>`) |
| `.gitignore` | **Modified** | Removed vestigial `*.mp3` entry (all 78 files already tracked) |

### What stays the same

- `src/index.html` app logic — untouched. `new Audio(src)` works identically on HTTPS.
- `src/phrases.json` — unchanged.
- `src/generate_audio.py` — run locally on Mac, commit the MP3s, push.
- The tablet deployment — unaffected. Termux localhost server keeps running.
- The `checkAudio()` HEAD-request function — works on HTTPS; Vercel responds 200 for all deployed files.

---

## New and Modified Files — Full Contents

### `vercel.json` (repo root)

```json
{
  "version": 2,
  "outputDirectory": "src",
  "headers": [
    {
      "source": "/audio/(.*)\\.mp3",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    },
    {
      "source": "/sw.js",
      "headers": [
        { "key": "Cache-Control", "value": "no-cache, no-store, must-revalidate" },
        { "key": "Service-Worker-Allowed", "value": "/" }
      ]
    },
    {
      "source": "/phrases.json",
      "headers": [
        { "key": "Cache-Control", "value": "no-cache" }
      ]
    },
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" }
      ]
    }
  ]
}
```

**Header rationale:**

- **`/audio/*.mp3` — `immutable, max-age=31536000`**: Audio files never change in-place; new phrases get new filenames. A 1-year browser and CDN cache is correct. Eliminates repeated network requests after first play.
- **`/sw.js` — `no-cache`**: The browser must always re-check the SW script on page load. If you cache `sw.js` itself, users get stuck on stale versions after a redeploy. This is mandatory for all SW deployments.
- **`/phrases.json` — `no-cache`**: Allows the phrase bank to be updated without a SW cache bust. The SW's own cache still serves it offline.
- **`/(.*)`**: `X-Content-Type-Options` prevents MIME-type sniffing. `X-Frame-Options: DENY` prevents the app being embedded in an iframe on a third-party site.

---

### `src/sw.js` — Service Worker

The SW uses **dynamic precaching at install time**: it fetches `phrases.json` to discover all 78 audio paths, then caches everything before the SW activates. This means the app is fully offline-capable from the very first visit — the user never needs to tap every button once before going offline.

`Promise.allSettled` is used for audio caching so a single slow or missing file does not abort the entire install.

When you add new phrases, increment `CACHE_VERSION` (e.g. `'v1'` → `'v2'`). This causes the SW to reinstall, re-fetch `phrases.json`, and precache the new audio. Without a version bump, existing clients will not discover new audio until they clear their cache manually.

See [src/sw.js](../../src/sw.js) for the full implementation.

---

### `src/icon.svg` — PWA Icon

A minimal 192×192 dark-grey square with a white "P", matching the app's `#212121` background. Used by Android Chrome for the home screen icon and PWA install prompt.

`manifest.json` references it with `"sizes": "any"` (correct for SVG — infinitely scalable) and `"purpose": "any maskable"`.

---

### `middleware.ts` — Access Control (Edge Middleware)

The app contains personal names (Francisca, Hannes, Carey-Anne, Elaine, Fanie) and is a medical device. The Vercel Hobby plan does not include password protection, but **Vercel Edge Middleware** runs at the CDN edge before any file is served and is included free on all plans.

The middleware:
1. Checks for a `pa-se-app-auth` cookie
2. If the cookie matches `APP_PASSWORD` env var → allows the request through
3. If the URL contains `?pw=<correct-password>` → sets the cookie (1-year expiry) and redirects to the clean URL
4. Otherwise → serves a minimal Afrikaans login page (password input form)

Family members log in once on each device. The cookie persists for 1 year.

**The password is never in source code.** It is set as an environment variable in the Vercel dashboard (see §Setup Steps below).

See [middleware.ts](../../middleware.ts) for the full implementation.

---

## MP3 Files — Git Status Clarification

`.gitignore` contained a `*.mp3` entry, but **all 78 audio files are already committed to the repository**. Git only ignores files that have never been tracked; once committed, `.gitignore` has no effect on them. The entry was vestigial and has been removed.

This means **git-connected Vercel deployment includes the audio files automatically** on every push. No special CLI deploy or workaround is needed.

---

## One-Time Setup

### 1. Connect the repo to Vercel

1. Go to [vercel.com/johnnyfoulds-projects](https://vercel.com/johnnyfoulds-projects)
2. Click **Add New → Project**
3. Import the `afrikaans-aac` GitHub repository
4. On the configure screen:
   - **Framework Preset**: Other
   - **Root Directory**: `.` (repo root — `vercel.json` at root points to `src/`)
   - **Build Command**: leave blank
   - **Output Directory**: leave blank (controlled by `vercel.json`)
5. Click **Deploy**

Vercel will assign a URL like `pa-se-app.vercel.app` (or similar).

### 2. Set the access password

Before sharing the URL with anyone:

1. Vercel dashboard → your project → **Settings → Environment Variables**
2. Add: `APP_PASSWORD` = `<your chosen password>` (scope: Production + Preview)
3. Click **Save**
4. Go to **Deployments** → click the latest deployment → **Redeploy** (env vars take effect on next deploy)

Share the URL and password with family members verbally or via a private message. They log in once; the cookie lasts a year.

To rotate the password later: change `APP_PASSWORD` in the dashboard — no redeploy needed. Existing cookies become invalid immediately.

### 3. (Optional) Add a custom domain

1. Vercel dashboard → project → **Settings → Domains**
2. Enter your domain (e.g. `pasesapp.co.za`)
3. Add a DNS record at your registrar:
   - For an apex domain (`pasesapp.co.za`): **A record** → `76.76.21.21`
   - For a subdomain (`app.pasesapp.co.za`): **CNAME** → `cname.vercel-dns.com`
4. Vercel auto-provisions HTTPS once DNS propagates (15–30 min typically)

You do **not** need to change nameservers to Vercel.

---

## Ongoing Update Workflow

### Text-only changes (no new audio)

```bash
# Edit phrases.json, index.html, or any other file
git add src/phrases.json   # or whichever file changed
git commit -m "chore: update phrases"
git push
# Vercel redeploys automatically — takes ~10 seconds
```

### Adding new phrases with audio

```bash
# 1. Add the new phrase to src/phrases.json

# 2. Generate the new MP3
conda activate afrikaans-aac
python3 src/generate_audio.py
# (only generates files that don't already exist)

# 3. Increment CACHE_VERSION in src/sw.js
#    Change: const CACHE_VERSION = 'v1';
#    To:     const CACHE_VERSION = 'v2';
#    This forces all web clients to reinstall the SW and precache new audio.

# 4. Commit everything
git add src/phrases.json src/audio/<new-phrase>.mp3 src/sw.js
git commit -m "feat: add phrase '<new phrase label>'"
git push
# Vercel redeploys automatically
```

### Rotating the access password

No code change needed. Go to Vercel dashboard → Settings → Environment Variables → edit `APP_PASSWORD`. The new value takes effect immediately at the edge.

---

## Tablet vs. Vercel — Comparison

| Dimension | Tablet (Termux) | Vercel |
| --- | --- | --- |
| Availability | When tablet is on and Termux running | 99.9% uptime, global CDN |
| Offline | Always (local server) | After first load (SW cache) |
| Access | Local network only | Anywhere via HTTPS |
| HTTPS | No (HTTP localhost) | Yes (automatic) |
| PWA install | Yes (Chrome localhost exception) | Yes (proper HTTPS, any Android/iOS) |
| Service worker | Not applicable (localhost HTTP) | Full SW support |
| Deploy method | SSH + rsync | `git push` |
| Audio files | rsync'd directly | Git-tracked, auto-deployed |
| Cost | Power bill | Free (Hobby tier) |
| Family remote access | Not possible without VPN | Any phone with the password |
| Update latency | Immediate after rsync | ~10 seconds after push |

---

## Verification Checklist

After initial deploy, confirm:

- [ ] App loads at the Vercel URL — login page appears
- [ ] Enter password → redirected to app, category grid renders
- [ ] Tap a category → phrase screen shows
- [ ] Tap a phrase → audio plays
- [ ] Load page, disconnect wifi, reload → app still works from SW cache
- [ ] Chrome DevTools → Application → Service Workers → shows `sw.js` as active
- [ ] Chrome DevTools → Application → Cache Storage → shows `pa-se-app-v1` with all 78 audio entries
- [ ] On Android Chrome: three-dot menu → "Add to Home Screen" → app installs, opens fullscreen landscape
- [ ] Tap "NOODGEVAL" → loud alert audio plays
- [ ] Tap "Roep vir Francisca" in always-bar → audio plays

---

## Gotchas and Edge Cases

**SW install on first visit:** The SW registers after `window.load` and installs in the background. On the very first visit, the page loads from the network normally. On second visit (or ~5 seconds after first), all assets are served from the SW cache. This is correct PWA first-load behaviour.

**`checkAudio()` HEAD requests are not intercepted by the SW:** The app sends `HEAD` requests to check audio availability and dim missing buttons. The SW only handles `GET`. On Vercel, every deployed file returns 200 to HEAD, so no buttons are dimmed. Correct.

**Duplicate audio paths in `phrases.json`:** `audio/verstaan_nie.mp3` is referenced twice (ids `verstaan_nie` and `verstaan_nie2`). `audio/praat_stadiger.mp3` is similarly referenced twice. The SW's `extractAudioPaths()` uses a `Set` to deduplicate — one file, one cache entry.

**Middleware and the SW/manifest:** The middleware matcher passes through `/sw.js`, `/manifest.json`, `/phrases.json`, and `/audio/*` for authenticated requests. The auth cookie is checked on every request, but with `httpOnly: true` and a 1-year expiry, this is invisible to users after first login.

**`middleware.ts` on a static site:** Vercel Edge Middleware works for any project type, not just Next.js apps. The `import { NextRequest, NextResponse } from 'next/server'` import is resolved by Vercel's bundled edge runtime — you do not need to install Next.js or any `package.json`.

**Vercel free tier commercial use restriction:** The Hobby plan is for personal and non-commercial use. This app is a personal assistive device used in academic research — it qualifies. If Vodacom or another commercial entity formally adopts it, upgrade to the Pro plan ($20/month) or use a different host.
