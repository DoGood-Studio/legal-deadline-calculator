// Keeps the demo working offline. Pages and files come from the network when it is reachable,
// always revalidated with the server (GitHub Pages lets browsers reuse a copy for ten minutes),
// so a visitor never gets an old page with new scripts; from the cache when it is not.
// Each page is stored once, under its address without the query (?pack=…&date=… only fills in
// the form), so the cache holds the latest copy of every page and does not grow with each link.
// Bump CACHE when the list below changes.
const CACHE = "lexdays-v2";
const PREFIX = "lexdays-"; // other sites on dogood-studio.github.io keep their own caches
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
const SCOPE = self.registration.scope;

// Shown for a page that was never opened on this device (an act page, say) while offline.
const OFFLINE = `<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>lexdays</title></head>
<body style="margin:0;padding:48px max(16px,env(safe-area-inset-left));font:16px/1.55 system-ui,sans-serif;color:#1b2533;background:#f7f9fc">
<main style="max-width:36rem;margin:0 auto"><h1 style="font-size:1.6rem">Çevrimdışısınız · You are offline</h1>
<p>Bu sayfa bu cihaza henüz kaydedilmedi. Hesaplayıcı internet olmadan da çalışır.</p>
<p>This page has not been saved on this device yet. The calculator works without a connection.</p>
<p><a href="${SCOPE}" style="color:#2a5389;font-weight:600">lexdays</a></p></main></body></html>`;

const pageKey = (url) => {
  const key = new URL(url);
  key.search = "";
  key.hash = "";
  return key.href;
};

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith(PREFIX) && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

async function fromNetwork(request, url, page, sameOrigin) {
  if (page) {
    // A page request cannot be copied with other options, so the same address is fetched afresh;
    // a redirect (/tr to /tr/) is left to the browser.
    const response = await fetch(url.href, { cache: "no-cache", credentials: "same-origin" });
    return response.redirected ? fetch(request) : response;
  }
  return fetch(sameOrigin ? new Request(request, { cache: "no-cache" }) : request);
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  const sameOrigin = url.origin === self.location.origin;
  if (!sameOrigin && !FONT_HOSTS.has(url.hostname)) return;
  const page = request.mode === "navigate";
  const key = page ? pageKey(url) : request;
  event.respondWith(
    (async () => {
      try {
        const response = await fromNetwork(request, url, page, sameOrigin);
        const keep = page ? response.ok && !response.redirected : response.ok || response.type === "opaque";
        if (keep) {
          const copy = response.clone();
          event.waitUntil(caches.open(CACHE).then((cache) => cache.put(key, copy)));
        }
        return response;
      } catch {
        const hit = await caches.match(key);
        if (hit || !page) return hit ?? Response.error();
        return new Response(OFFLINE, { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } });
      }
    })(),
  );
});
