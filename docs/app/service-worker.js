const CACHE_PREFIX = `universo-rebeldia:${self.registration.scope}:`;
const CACHE_NAME = `${CACHE_PREFIX}v8`;
const APP_SHELL = [
  "./",
  "./index.html",
  "./manifest.json",
  "./assets/css/app.css",
  "./assets/js/db.js",
  "./assets/js/app.js",
  "./assets/icons/icon.svg",
  "./assets/icons/icon-192.png",
  "./assets/icons/icon-512.png",
  "./pages/dashboard.html",
  "./pages/livro.html",
  "./pages/refletir.html",
  "./pages/conectar.html",
  "./pages/laboratorio.html",
  "./pages/configuracoes.html",
  "./data/capitulos.json",
  "./data/glossario.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
      .map((key) => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "CHECK_OFFLINE") {
    event.waitUntil((async () => {
      const cache = await caches.open(CACHE_NAME);
      const entries = await Promise.all(APP_SHELL.map((path) => cache.match(path)));
      event.source?.postMessage({ type: "OFFLINE_STATUS", ready: entries.every(Boolean) });
    })());
  }
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || !url.href.startsWith(self.registration.scope)) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);
    if (cached) return cached;
    if (request.mode === "navigate") {
      try {
        return await fetch(request);
      } catch {
        return (await cache.match("./index.html"))
          || new Response("Conteúdo offline indisponível. Conecte-se e abra o aplicativo novamente.", {
            status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" }
          });
      }
    }
    return fetch(request);
  })());
});
