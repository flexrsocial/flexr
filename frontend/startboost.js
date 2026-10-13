/* Startboost: voller Suchumkreis bis 580 km für alle bis 31.12.2026.
 *
 * Die Zusätze dazu („bis 31.12.2026 für alle frei“) stehen fest im HTML der
 * öffentlichen Seiten (Landingpage DE/EN, FAQ DE/EN, Such-Einstiegsseiten),
 * jeweils als <span class="startboost">. Ab dem 01.01.2027 (Europe/Vienna)
 * blendet dieses Skript sie aus, damit dort kein abgelaufenes Angebot stehen
 * bleibt. Der Server setzt die Grenze zum selben Zeitpunkt von selbst zurück
 * (backend/app/premium.py, radius_boost_active), die Web-App blendet ihre
 * Hinweise anhand von GET /api/billing/status aus.
 *
 * Bewusst die Uhr des Browsers und kein API-Abruf wie in legal-status.js: Es
 * geht um einen Werbezusatz, an dem keine Rechtsfolge hängt, und das Skript
 * soll vor dem ersten Zeichnen fertig sein (deshalb ohne defer im <head>,
 * sonst blitzt der Zusatz kurz auf).
 *
 * Wird der Boost verlängert (RADIUS_BOOST_LAST_DAY), müssen dieses Datum und
 * die Texte mitziehen. Nach dem Boost können Skript und Spans entfallen.
 */
(function () {
  var LETZTER_TAG = '2026-12-31';
  var heute;
  try {
    // en-CA formatiert als JJJJ-MM-TT, das lässt sich als Text vergleichen.
    heute = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Europe/Vienna', year: 'numeric', month: '2-digit', day: '2-digit'
    }).format(new Date());
  } catch (e) {
    heute = new Date().toISOString().slice(0, 10);
  }
  if (heute <= LETZTER_TAG) return;
  var stil = document.createElement('style');
  stil.textContent = '.startboost{display:none !important}';
  document.head.appendChild(stil);
})();
