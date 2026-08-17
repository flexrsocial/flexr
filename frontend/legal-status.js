/* §13a FAGG: Umschaltung der Fussleisten-Funktion zum Stichtag 1. Oktober 2026.
 *
 * Bis dahin genügt der normale, gleichrangige Link "Rücktrittsrecht" im
 * Legal-Footer - das steht schon so im HTML, ganz ohne dieses Skript hier.
 * Ab dem Stichtag muss die Funktion als eigenständig erkennbar hervorgehoben
 * sein: Text wird zu "Vertrag widerrufen", dazu ein dezenter Rahmen
 * (.widerruf-hervorgehoben in legal.css).
 *
 * Maßgeblich ist die Serverzeit (Europe/Vienna) aus GET /api/withdrawal/status,
 * nicht die Uhr im Browser - die lässt sich verstellen. Schlägt der Abruf fehl
 * (API nicht erreichbar), bleibt es beim im HTML hinterlegten Vor-Stichtag-
 * Zustand - das ist vor dem 1. Oktober 2026 ohnehin korrekt und danach nur ein
 * konservativer Fallback (unterhervorgehoben statt fälschlich hervorgehoben).
 */
(function () {
  var API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : '';

  // Elemente, die es erst/nur ab dem Stichtag geben soll (Zusatzabsaetze auf
  // /widerruf.html, im Checkout-Hinweis und in der AGB-Verweiszeile).
  var NUR_AB_STICHTAG = [
    'widerruf-oct1-hinweis', 'istartOct1Hinweis',
    'agb-widerruf-oct1-funktion', 'agb-widerruf-oct1-zusatz',
  ];
  // Das Gegenstueck: nur VOR dem Stichtag sichtbar.
  var NUR_VOR_STICHTAG = ['agb-widerruf-oct1-formular'];

  function anwenden(pflicht) {
    document.querySelectorAll('a[data-widerruf-link]').forEach(function (a) {
      if (pflicht) {
        a.textContent = 'Vertrag widerrufen';
        a.classList.add('widerruf-hervorgehoben');
      } else {
        a.textContent = 'Rücktrittsrecht';
        a.classList.remove('widerruf-hervorgehoben');
      }
    });
    NUR_AB_STICHTAG.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.style.display = pflicht ? '' : 'none';
    });
    NUR_VOR_STICHTAG.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.style.display = pflicht ? 'none' : '';
    });
  }

  fetch(API_BASE + '/api/withdrawal/status')
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) { if (d) anwenden(!!d.legally_required); })
    .catch(function () { /* Fallback bleibt der im HTML hinterlegte Zustand. */ });
})();
