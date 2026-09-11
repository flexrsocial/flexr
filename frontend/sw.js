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
// v9: Die Zweisprachigkeit kam dazu. /i18n.js und /app/i18n-app.js gehoeren in
// die Shell - ohne sie zeigt die App offline die rohen Uebersetzungsschluessel.
// v10: Die Landingpage gibt es jetzt zweisprachig unter zwei Adressen (/ und
// /en/). Beide gehoeren in die Shell, dazu lang-switch.js; i18n-landing.js ist
// dagegen raus - es ist nur noch Eingabe fuer build-en.py und wird von keiner
// Seite mehr geladen.
// v12: Auch die Rechtstexte gibt es jetzt unter /en/. lang-switch.js liest die
// beiden Adressen einer Seite seither aus dem Regler im Markup und laeuft
// deshalb auch dort; legal.css und legal-status.js haben sich mitgeaendert.
// Die Rechtstexte selbst bleiben bewusst AUSSERHALB der Shell: sie sind viele
// und selten gebraucht, und eine im Cache eingefrorene alte Fassung eines
// Vertragstextes waere das falsche Offline-Verhalten. "Netz zuerst" holt sie
// bei jedem Online-Aufruf frisch.
// v13: Die Sprachwahl geht jetzt ans Profil (PATCH /api/profiles/me), damit der
// Server seine E-Mails in derselben Sprache schreibt. Betrifft /app/index.html
// und die beiden oeffentlichen Formulare - eine offline eingefrorene alte
// Fassung wuerde die Sprache nie melden.
// v14: Der Offline-Rueckfall galt fuer jede Navigation und hat damit die
// Landingpage unter die Adresse jedes Vertragstextes gelegt - also genau die
// Seiten, die seit v12 bewusst ausserhalb der Shell liegen. War der Cache noch
// leer, lieferte caches.match() undefined und respondWith() machte daraus einen
// harten Netzfehler. Der Rueckfall greift jetzt nur noch fuer Adressen, die die
// Shell wirklich abdeckt; /en/ landet dabei auf der englischen Fassung und
// nicht mehr auf der deutschen.
const CACHE = 'flexr-shell-v14';
// Seit dem 15.08.2026 liegt die App unter /app/, an der Wurzel steht die
// oeffentliche Landingpage. Beide gehoeren in die Shell: die Landingpage,
// weil sie der Einstieg ist, die App, weil sie offline funktionieren soll.
const SHELL = ['/', '/index.html', '/en/', '/en/index.html',
               '/app/', '/app/index.html',
               '/lang-switch.js?v=2', '/i18n.js?v=4', '/app/i18n-app.js?v=4',
               '/manifest.json', '/favicon.ico?v=4', '/legal.css?v=2',
               '/fonts/work-sans.woff2?v=1', '/fonts/oswald.woff2?v=1',
               '/icons/icon-192.png?v=4', '/icons/icon-512.png?v=4'];
const SHELL_PATHS = new Set(SHELL.map((path) => new URL(path, self.location.origin).pathname));
const STATIC_PREFIXES = ['/fonts/', '/icons/', '/brand/demo/'];

// Welche Shell-Seite vertritt diese Adresse offline? null heisst: keine - dann
// bleibt es beim Netzfehler des Browsers.
function shellDocumentFor(pathname) {
  // Wer in der App oder im Aktivierungslink war, soll offline die App sehen,
  // nicht die Marketingseite.
  if (pathname.startsWith('/app') || pathname === '/mail-bestaetigen') return '/app/index.html';
  if (pathname === '/en/' || pathname === '/en/index.html') return '/en/index.html';
  if (pathname === '/' || pathname === '/index.html') return '/index.html';
  return null;
}

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
      .catch(() => caches.match(event.request).then(async (hit) => {
        if (hit) return hit;
        if (!isNavigation) return Response.error();
        // Nur Adressen, die die Shell abdeckt, bekommen einen Rueckfall. Fuer
        // alles andere - vor allem die Rechtstexte - ist die Offline-Meldung
        // des Browsers die ehrlichere Auskunft als die Landingpage unter der
        // Adresse eines Vertragstextes.
        const fallback = shellDocumentFor(url.pathname);
        if (!fallback) return Response.error();
        // Ohne das Oder waere die Antwort undefined, sobald der Cache leer ist
        // (erster Aufruf, geleerter Speicher); respondWith() macht daraus einen
        // harten Netzfehler statt einer Offline-Seite.
        return (await caches.match(fallback)) || Response.error();
      }))
  );
});
