// Keeps the demo working offline. Pages and files come from the network when it is reachable,
// so visitors always get the current version, and from the cache when it is not.
// Bump CACHE when the list below changes.
const CACHE = "lexdays-v1";
const LANGS = ["en", "tr", "de", "fr", "es", "it", "pt", "nl", "ru", "ar", "zh", "ja"];
const CORE = [
  "./",
  "app.js",
  "ics.js",
  "labels.js",
  "style.css",
  "assets/lexdays.js",
  "manifest.webmanifest",
  "assets/icon-192.png",
  "assets/icon-512.png",
  ...LANGS.map((l) => `${l}/`),
  ...LANGS.map((l) => `i18n/${l}.js`),
];
const FONT_HOSTS = new Set(["fonts.googleapis.com", "fonts.gstatic.com"]);

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  const sameOrigin = url.origin === self.location.origin;
  if (!sameOrigin && !FONT_HOSTS.has(url.hostname)) return;
  // Own files are revalidated with the server instead of taken from the browser's HTTP cache, so a
  // new app.js never runs against an older assets/lexdays.js. (A page request cannot be copied
  // with other options; the browser checks those itself.)
  const fresh = sameOrigin && request.mode !== "navigate" ? new Request(request, { cache: "no-cache" }) : request;
  event.respondWith(
    fetch(fresh)
      .then((response) => {
        if (response.ok || response.type === "opaque") {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(request, copy));
        }
        return response;
      })
      // Offline: the same file from the cache. Pages are matched without their query string,
      // so /tr/?pack=tr/hmk&date=... opens the cached Turkish page.
      .catch(() =>
        caches.match(request, { ignoreSearch: request.mode === "navigate" })
          .then((hit) => hit ?? (request.mode === "navigate" ? caches.match("./") : Response.error())),
      ),
  );
});
