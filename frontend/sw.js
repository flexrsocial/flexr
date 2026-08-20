// FLEXR Service Worker - bewusst minimal gehalten.
// Strategie: Netz zuerst (damit nie eine veraltete App-Version hängen bleibt),
// Cache nur als Offline-Fallback für die App-Shell. API-Requests werden nie
// gecacht.
// Bei jedem Icon-Wechsel gemeinsam hochzaehlen: hier, in index.html und in
// manifest.json - sonst bleibt das alte Icon im Browser-Cache haengen.
// v7 am 15.08.2026: Zwischen zwei Deploys desselben Tages lag eine Fassung von
// /app/index.html mit dem Unsplash-Demo-Deck im Cache. "Netz zuerst" holt zwar
// bei jedem Online-Aufruf frisch, aber der Offline-Rueckfall haette die alte
// Fassung noch ausgeliefert - mitsamt Fremdaufrufen, die die CSP dann
// blockiert. Ein Hochzaehlen loescht alle alten Caches im activate-Schritt.
// v8: Runtime-Cache auf die tatsaechliche Shell und oeffentliche statische
// Assets begrenzt. Nutzerfotos, Downloads und beliebige GET-Antworten gehoeren
// weder aus Datenschutz- noch aus Speichergruenden in diesen Cache.
const CACHE = 'flexr-shell-v8';
// Seit dem 15.08.2026 liegt die App unter /app/, an der Wurzel steht die
// oeffentliche Landingpage. Beide gehoeren in die Shell: die Landingpage,
// weil sie der Einstieg ist, die App, weil sie offline funktionieren soll.
const SHELL = ['/', '/index.html', '/app/', '/app/index.html',
               '/manifest.json', '/favicon.ico?v=4', '/legal.css?v=1',
               '/fonts/work-sans.woff2?v=1', '/fonts/oswald.woff2?v=1',
               '/icons/icon-192.png?v=4', '/icons/icon-512.png?v=4'];
const SHELL_PATHS = new Set(SHELL.map((path) => new URL(path, self.location.origin).pathname));
const STATIC_PREFIXES = ['/fonts/', '/icons/', '/brand/demo/'];

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
  // API, Fremd-Origins und alles Nicht-GET: immer direkt zum Netz, kein Cache.
  // /photos/ und /dl-* bleiben ebenfalls bewusst ausserhalb: keine
  // Nutzerbilder und keine mehrmegabytegrossen AAB-Dateien im Shell-Cache.
  if (event.request.method !== 'GET' || url.origin !== self.location.origin ||
      url.pathname.startsWith('/api/') || url.pathname.startsWith('/photos/') ||
      url.pathname.startsWith('/dl-')) return;

  const isNavigation = event.request.mode === 'navigate';
  const isStaticAsset = STATIC_PREFIXES.some((prefix) => url.pathname.startsWith(prefix));
  const isShellAsset = SHELL_PATHS.has(url.pathname);

  // Andere Unterressourcen laufen normal ueber den Browser. So wird aus einem
  // fehlenden Bild offline nicht versehentlich die HTML-Landingpage.
  if (!isNavigation && !isStaticAsset && !isShellAsset) return;

  event.respondWith(
    fetch(event.request)
      .then((resp) => {
        // Nur explizit freigegebene, nicht-personenbezogene Assets speichern.
        if (resp.ok && (isStaticAsset || isShellAsset)) {
          const copy = resp.clone();
          caches.open(CACHE).then((c) => c.put(event.request, copy));
        }
        return resp;
      })
      .catch(() => caches.match(event.request).then((hit) => {
        if (hit) return hit;
        if (!isNavigation) return Response.error();
        // Wer in der App oder im Aktivierungslink war, soll offline die App
        // sehen, nicht die Marketingseite.
        const appRoute = url.pathname.startsWith('/app') || url.pathname === '/mail-bestaetigen';
        return caches.match(appRoute ? '/app/index.html' : '/index.html');
      }))
  );
});
