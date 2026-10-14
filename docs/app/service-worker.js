const CACHE_NAME = "universo-rebeldia-v6";
const APP_SHELL = [
  "./",
  "./index.html",
  "./manifest.json",
  "./assets/css/app.css",
  "./assets/js/db.js",
  "./assets/js/app.js",
  "./assets/icons/icon.svg",
  "./pages/dashboard.html",
  "./pages/livro.html",
  "./pages/conceitos.html",
  "./pages/enciclopedia.html",
  "./pages/desafios.html",
  "./pages/laboratorio.html",
  "./pages/timeline.html",
  "./pages/configuracoes.html",
  "./data/capitulos.json",
  "./data/conceitos.json",
  "./data/glossario.json",
  "./data/desafios.json",
  "./data/timeline.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET" || new URL(request.url).origin !== self.location.origin) return;

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        }
        return response;
      });
    })
  );
});
