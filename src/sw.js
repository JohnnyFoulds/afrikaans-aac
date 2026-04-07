// sw.js — Cache-first service worker for Pa se App
//
// Strategy: precache entire app shell + all audio at install time.
// This ensures the app works fully offline from the very first visit,
// even for phrases the user has never tapped.
//
// When you add new phrases or regenerate audio, increment CACHE_VERSION
// to force all clients to re-install the SW and re-cache everything.

const CACHE_VERSION = 'v1';
const CACHE_NAME = `pa-se-app-${CACHE_VERSION}`;

const SHELL_FILES = [
  '/',
  '/index.html',
  '/manifest.json',
  '/phrases.json',
];

// ── Install ───────────────────────────────────────────────────────────────────
// Fetch phrases.json to discover all audio paths, then cache everything.
self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);

      // 1. Cache the static shell so the app can open even if audio
      //    precaching is slow or fails on a weak connection.
      await cache.addAll(SHELL_FILES);

      // 2. Fetch phrases.json to get the full audio file list dynamically.
      let audioFiles = [];
      try {
        const resp = await fetch('/phrases.json');
        const data = await resp.json();
        audioFiles = extractAudioPaths(data);
      } catch (err) {
        // Network unavailable during install — shell is cached, audio is not.
        // The runtime fetch handler below will cache audio on first play.
        console.warn('[SW] Could not fetch phrases.json during install:', err);
      }

      // 3. Cache all audio files. Use individual fetch+put rather than addAll()
      //    so a single missing file does not abort the entire install.
      await Promise.allSettled(
        audioFiles.map(async (path) => {
          try {
            const response = await fetch(path);
            if (response.ok) {
              await cache.put(path, response);
            }
          } catch (err) {
            console.warn('[SW] Could not precache:', path, err);
          }
        })
      );

      // Take control immediately — do not wait for old SW to be released.
      await self.skipWaiting();
    })()
  );
});

// ── Activate ──────────────────────────────────────────────────────────────────
// Delete caches from previous versions.
self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      );
      await self.clients.claim();
    })()
  );
});

// ── Fetch ─────────────────────────────────────────────────────────────────────
// Cache-first for all same-origin GET requests.
// Falls back to network, then stores the response for future offline use.
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(event.request);
      if (cached) return cached;

      try {
        const response = await fetch(event.request);
        if (response.ok) {
          await cache.put(event.request, response.clone());
        }
        return response;
      } catch {
        return new Response('Offline — hierdie hulpbron is nie beskikbaar nie.', {
          status: 503,
          statusText: 'Service Unavailable',
        });
      }
    })()
  );
});

// ── Helpers ───────────────────────────────────────────────────────────────────
/**
 * Extract all unique audio paths from the phrases.json data structure.
 * Traverses always_visible, categories[].phrases, and categories[].secondary.phrases.
 * Returns absolute paths like ["/audio/ja.mp3", ...].
 */
function extractAudioPaths(data) {
  const seen = new Set();
  const paths = [];

  function add(audioPath) {
    if (audioPath && !seen.has(audioPath)) {
      seen.add(audioPath);
      // phrases.json stores paths as "audio/ja.mp3" (relative).
      // Cache keys must be absolute paths to match browser request URLs.
      paths.push('/' + audioPath);
    }
  }

  for (const entry of data.always_visible || []) add(entry.audio);
  for (const cat of data.categories || []) {
    for (const p of cat.phrases || []) add(p.audio);
    for (const p of (cat.secondary?.phrases) || []) add(p.audio);
  }

  return paths;
}
