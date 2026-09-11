/* §13a FAGG: Umschaltung der Fussleisten-Funktion zum Stichtag 1. Oktober 2026.
 *
 * Bis dahin genügt der normale, gleichrangige Link "Rücktrittsrecht" im
 * Legal-Footer - das steht schon so im HTML, ganz ohne dieses Skript hier.
 * Ab dem Stichtag muss die Funktion als eigenständig erkennbar hervorgehoben
 * sein: Text wird zu "Vertrag widerrufen", dazu ein dezenter Rahmen
 * (.widerruf-hervorgehoben in legal.css).
 *
 * Die Beschriftung richtet sich nach dem <html lang> der Seite: unter /en/
 * heißt der Link "Right of withdrawal" bzw. ab dem Stichtag "Withdraw from
 * contract".
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

  // Seit es die Rechtstexte auch unter /en/ gibt, steht dasselbe Skript auf
  // deutschen und englischen Seiten. Welche Sprache gilt, sagt das <html lang>
  // der ausgelieferten Seite - dieselbe Quelle wie in lang-switch.js. Ein
  // eigenes Woerterbuch waere fuer zwei Begriffspaare zu viel.
  var SPRACHE = (document.documentElement.getAttribute('lang') || 'de')
    .slice(0, 2).toLowerCase() === 'en' ? 'en' : 'de';

  var TEXTE = {
    de: { pflicht: 'Vertrag widerrufen', normal: 'Rücktrittsrecht' },
    en: { pflicht: 'Withdraw from contract', normal: 'Right of withdrawal' },
  }[SPRACHE];

  function anwenden(pflicht) {
    document.querySelectorAll('a[data-widerruf-link]').forEach(function (a) {
      a.textContent = pflicht ? TEXTE.pflicht : TEXTE.normal;
      a.classList.toggle('widerruf-hervorgehoben', pflicht);
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
