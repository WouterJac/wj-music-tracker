// Service worker: keeps the app shell (the page and its built files) so the app opens quickly
// and shows its screens when the server is slow. It never handles /api or /health, so music
// data and the access token are never cached here.

const CACHE = "wj-shell-v1";
const SHELL = "/";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll([SHELL]))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

function isApiRequest(url) {
  return url.pathname.startsWith("/api/") || url.pathname === "/health";
}

// Built files have hashed names, so a cached copy is never stale.
function cacheFirst(request, url) {
  return caches.open(CACHE).then((cache) =>
    cache.match(url.pathname).then(
      (cached) =>
        cached ||
        fetch(request).then((response) => {
          if (response.ok) cache.put(url.pathname, response.clone());
          return response;
        }),
    ),
  );
}

// Every page URL is answered with the same index.html, so one copy of it is kept under "/".
function networkFirstShell(request) {
  return caches.open(CACHE).then((cache) =>
    fetch(request)
      .then((response) => {
        if (response.ok) cache.put(SHELL, response.clone());
        return response;
      })
      .catch(() => cache.match(SHELL)),
  );
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin || isApiRequest(url)) {
    return;
  }
  if (request.mode === "navigate") {
    event.respondWith(networkFirstShell(request));
  } else if (url.pathname.startsWith("/assets/")) {
    event.respondWith(cacheFirst(request, url));
  }
});
