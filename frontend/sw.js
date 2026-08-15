// FLEXR Service Worker - bewusst minimal gehalten.
// Strategie: Netz zuerst (damit nie eine veraltete App-Version hängen bleibt),
// Cache nur als Offline-Fallback für die App-Shell. API-Requests werden nie
// gecacht.
// Bei jedem Icon-Wechsel gemeinsam hochzaehlen: hier, in index.html und in
// manifest.json - sonst bleibt das alte Icon im Browser-Cache haengen.
const CACHE = 'flexr-shell-v6';
// Seit dem 15.08.2026 liegt die App unter /app/, an der Wurzel steht die
// oeffentliche Landingpage. Beide gehoeren in die Shell: die Landingpage,
// weil sie der Einstieg ist, die App, weil sie offline funktionieren soll.
const SHELL = ['/', '/index.html', '/app/', '/app/index.html',
               '/manifest.json', '/favicon.ico?v=4', '/legal.css?v=1',
               '/fonts/work-sans.woff2?v=1', '/fonts/oswald.woff2?v=1',
               '/icons/icon-192.png?v=4', '/icons/icon-512.png?v=4'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  // API und alles Nicht-GET: immer direkt zum Netz, kein Cache
  if (event.request.method !== 'GET' || url.pathname.startsWith('/api/')) return;

  event.respondWith(
    fetch(event.request)
      .then((resp) => {
        // Frische Antwort in den Shell-Cache legen (nur eigene Origin)
        if (resp.ok && url.origin === location.origin) {
          const copy = resp.clone();
          caches.open(CACHE).then((c) => c.put(event.request, copy));
        }
        return resp;
      })
      // Offline-Rueckfall: Wer in der App war, soll die App sehen, nicht die
      // Landingpage - sonst landet er beim Marketing statt bei seinen Chats.
      .catch(() => caches.match(event.request).then((hit) =>
        hit || caches.match(url.pathname.startsWith('/app') ? '/app/index.html' : '/index.html')))
  );
});
