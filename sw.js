/* Vulgate Reader service worker.
 *
 * Strategy:
 *   - App shell (index.html, "/") : network-first, fall back to cache offline.
 *     Keeps the reader updating as the v1.5 draft is revised, while staying
 *     usable offline once visited.
 *   - Book fragments (books/*.html) and data (data/*.json) : stale-while-
 *     revalidate — serve the cached copy instantly, refresh it in the
 *     background for next time.
 *
 * Bump CACHE_VERSION on each deploy so old caches are purged. The in-app
 * "Refresh content" button also clears all caches.
 */
const CACHE_VERSION = 'vulgate-v1.5-2026-05-29c';
const SHELL = ['./', 'index.html'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(names.filter((n) => n !== CACHE_VERSION).map((n) => caches.delete(n)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // let cross-origin (fonts) pass through

  const isShell = url.pathname.endsWith('/') || url.pathname.endsWith('index.html');

  if (isShell) {
    // Network-first for the shell.
    event.respondWith(
      fetch(req)
        .then((resp) => {
          const copy = resp.clone();
          caches.open(CACHE_VERSION).then((c) => c.put(req, copy));
          return resp;
        })
        .catch(() => caches.match(req).then((m) => m || caches.match('index.html')))
    );
    return;
  }

  // Stale-while-revalidate for everything else (book HTML, JSON).
  event.respondWith(
    caches.match(req).then((cached) => {
      const fetching = fetch(req)
        .then((resp) => {
          const copy = resp.clone();
          caches.open(CACHE_VERSION).then((c) => c.put(req, copy));
          return resp;
        })
        .catch(() => cached);
      return cached || fetching;
    })
  );
});
