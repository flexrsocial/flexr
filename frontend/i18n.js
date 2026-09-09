/* FLEXR - Zweisprachigkeit (Deutsch / Englisch)
   ============================================================================
   Deutsch ist die Ausgangssprache. Die Schluessel tragen deshalb den deutschen
   Text als Original; was in `en` fehlt, faellt auf `de` zurueck statt auf den
   nackten Schluessel - eine vergessene Uebersetzung sieht dann nach deutschem
   Text aus und nicht nach einem Fehler.

   Welche Sprache beim ersten Aufruf gilt, entscheidet der Standort des
   Besuchers und nicht der Zufall (Vorgabe: DACH-Raum -> Deutsch). Die Zeitzone
   ist dafuer das verlaesslichere Signal als die Browsersprache: ein in Wien
   gekauftes Handy mit englischer Systemsprache steht trotzdem auf
   Europe/Vienna. Erst wenn die Zeitzone nichts hergibt, entscheidet die
   Sprachliste des Browsers. Eine ausdrueckliche Wahl ueber den Schieberegler
   schlaegt beides und ueberlebt im localStorage.

   Diese Datei wird von der Landingpage (/index.html), der Web-App (/app/) und
   den Rechtstexten gemeinsam geladen; sie darf deshalb nichts voraussetzen,
   was es nur in der App gibt.
   ========================================================================== */
window.FlexrI18n = (function(){
  'use strict';

  var STORE_KEY = 'flexr_lang';
  var LANGS = ['de', 'en'];
  var DEFAULT_LANG = 'de';

  // Zeitzonen des deutschsprachigen Raums. Busingen (deutsche Exklave in der
  // Schweiz) und Vaduz (Liechtenstein) sind eigene IANA-Zonen und wuerden
  // sonst als "nicht DACH" durchfallen.
  var DACH_ZONES = [
    'Europe/Vienna', 'Europe/Berlin', 'Europe/Zurich',
    'Europe/Busingen', 'Europe/Vaduz'
  ];

  var DICT = {de: {}, en: {}};
  var lang = DEFAULT_LANG;
  var listeners = [];

  function stored(){
    try{
      var v = localStorage.getItem(STORE_KEY);
      return LANGS.indexOf(v) >= 0 ? v : null;
    }catch(e){ return null; }   // localStorage gesperrt (privater Modus)
  }

  function detect(){
    var saved = stored();
    if(saved) return saved;

    // ?lang=en erlaubt einen sprachspezifischen Link, ohne dass der Besucher
    // erst den Regler suchen muss.
    try{
      var q = new URLSearchParams(location.search).get('lang');
      if(q && LANGS.indexOf(q.toLowerCase()) >= 0) return q.toLowerCase();
    }catch(e){}

    // 1. Der Ort. Ein in Wien gekauftes Handy mit englischer Systemsprache
    //    steht trotzdem auf Europe/Vienna - hier gilt die Vorgabe
    //    "DACH-Raum -> Deutsch" auch gegen die Browsersprache.
    try{
      var tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if(tz && DACH_ZONES.indexOf(tz) >= 0) return 'de';
    }catch(e){}

    // 2. Die Browsersprache. Ausserhalb des DACH-Raums entscheidet sie: wer
    //    seinen Browser auf Deutsch gestellt hat, bekommt Deutsch, auch aus
    //    Mailand oder Chicago. Englisch ist der Rueckfall fuer alles andere -
    //    nicht die Strafe fuer eine Zeitzone.
    var tags = (navigator.languages && navigator.languages.length)
      ? navigator.languages
      : [navigator.language || ''];
    for(var i = 0; i < tags.length; i++){
      var tag = String(tags[i] || '').toLowerCase();
      if(!tag) continue;
      if(tag.indexOf('de') === 0) return 'de';
      return 'en';   // erste gesetzte Sprache ist nicht Deutsch
    }
    return DEFAULT_LANG;   // gar kein Signal: Standardsprache
  }

  /* Uebersetzung nachschlagen. `vars` fuellt Platzhalter der Form {name}. */
  function t(key, vars){
    var table = DICT[lang] || {};
    var text = table[key];
    if(text === undefined) text = (DICT[DEFAULT_LANG] || {})[key];
    if(text === undefined) return key;
    if(vars){
      text = text.replace(/\{(\w+)\}/g, function(whole, name){
        return Object.prototype.hasOwnProperty.call(vars, name) ? String(vars[name]) : whole;
      });
    }
    return text;
  }

  function has(key){
    return (DICT[lang] && DICT[lang][key] !== undefined)
        || (DICT[DEFAULT_LANG] && DICT[DEFAULT_LANG][key] !== undefined);
  }

  /* Woerterbuecher nachreichen. Jede Seite bringt ihre eigenen Texte mit; die
     gemeinsamen (Rechts-Links, Sprachregler) stehen unten in dieser Datei. */
  function register(tables){
    LANGS.forEach(function(code){
      var add = tables[code];
      if(!add) return;
      Object.keys(add).forEach(function(k){ DICT[code][k] = add[k]; });
    });
  }

  /* Alle Knoten unter `root` uebersetzen.
       data-i18n        -> textContent
       data-i18n-html   -> innerHTML (nur fuer eigene Texte mit Markup)
       data-i18n-ph     -> placeholder
       data-i18n-aria   -> aria-label
       data-i18n-title  -> title
       data-i18n-alt    -> alt
       data-i18n-content-> content (Meta-Tags)                                */
  var ATTR_MAP = {
    'data-i18n-ph': 'placeholder',
    'data-i18n-aria': 'aria-label',
    'data-i18n-title': 'title',
    'data-i18n-alt': 'alt',
    'data-i18n-content': 'content'
  };

  function apply(root){
    var scope = root || document;
    scope.querySelectorAll('[data-i18n]').forEach(function(el){
      el.textContent = t(el.getAttribute('data-i18n'));
    });
    scope.querySelectorAll('[data-i18n-html]').forEach(function(el){
      el.innerHTML = t(el.getAttribute('data-i18n-html'));
    });
    Object.keys(ATTR_MAP).forEach(function(dataAttr){
      scope.querySelectorAll('[' + dataAttr + ']').forEach(function(el){
        el.setAttribute(ATTR_MAP[dataAttr], t(el.getAttribute(dataAttr)));
      });
    });
    syncSwitches(scope);
  }

  function htmlLangTag(){
    // Oesterreich ist der Heimatmarkt - das Deutsch der Texte ist oesterreichisch.
    return lang === 'de' ? 'de-AT' : 'en';
  }

  function set(next, opts){
    if(LANGS.indexOf(next) < 0 || next === lang) return;
    lang = next;
    if(!opts || opts.persist !== false){
      try{ localStorage.setItem(STORE_KEY, lang); }catch(e){}
    }
    document.documentElement.setAttribute('lang', htmlLangTag());
    apply(document);
    listeners.forEach(function(fn){ try{ fn(lang); }catch(e){ console.error(e); } });
  }

  /* Wird nach jedem Sprachwechsel gerufen - dort neu zeichnen, was nicht ueber
     data-i18n laeuft (Listen, Karten, Chatverlauf). */
  function onChange(fn){ listeners.push(fn); }

  function current(){ return lang; }

  /* ---- Sprachregler ------------------------------------------------------
     Zwei Segmente mit gleitendem Knopf. Beliebig oft im Dokument einsetzbar
     (Kopfzeile und Kontobereich zeigen denselben Zustand).                  */
  function syncSwitches(root){
    (root || document).querySelectorAll('.lang-switch').forEach(function(sw){
      sw.setAttribute('data-active', lang);
      sw.querySelectorAll('button[data-lang]').forEach(function(btn){
        var on = btn.getAttribute('data-lang') === lang;
        btn.setAttribute('aria-pressed', on ? 'true' : 'false');
        btn.classList.toggle('on', on);
      });
    });
  }

  function bindSwitches(root){
    (root || document).querySelectorAll('.lang-switch').forEach(function(sw){
      if(sw.dataset.bound) return;
      sw.dataset.bound = '1';
      sw.addEventListener('click', function(e){
        var btn = e.target.closest('button[data-lang]');
        if(btn) set(btn.getAttribute('data-lang'));
      });
    });
    syncSwitches(root);
  }

  /* Gemeinsame Texte: Sprachregler und Fussleisten-Links. Seiten-eigene Texte
     kommen ueber register() dazu. */
  register({
    de: {
      'lang.group': 'Sprache',
      'lang.de': 'Deutsch',
      'lang.en': 'Englisch',
      'lang.label': 'Sprache',
      'lang.hint': 'Gilt für die gesamte App. Rechtstexte bleiben auf Deutsch verbindlich.',
      'legal.faq': 'FAQ',
      'legal.impressum': 'Impressum',
      'legal.datenschutz': 'Datenschutz',
      'legal.agb': 'AGB',
      'legal.widerruf': 'Rücktrittsrecht',
      'legal.nutzungsrichtlinien': 'Nutzungsrichtlinien',
      'legal.sicherheit': 'Sicherheit',
      'legal.meldung': 'Inhalt melden',
      'legal.strafverfolgung': 'Strafverfolgung',
      'legal.section': 'Rechtliches',
      'legal.docs.aria': 'Rechtliche Dokumente',
      'legal.notice.de': 'Rechtstexte sind nur auf Deutsch verfügbar und in dieser Fassung verbindlich.'
    },
    en: {
      'lang.group': 'Language',
      'lang.de': 'German',
      'lang.en': 'English',
      'lang.label': 'Language',
      'lang.hint': 'Applies to the whole app. Legal texts remain binding in their German version.',
      'legal.faq': 'FAQ',
      'legal.impressum': 'Legal notice',
      'legal.datenschutz': 'Privacy',
      'legal.agb': 'Terms',
      'legal.widerruf': 'Right of withdrawal',
      'legal.nutzungsrichtlinien': 'Community guidelines',
      'legal.sicherheit': 'Safety',
      'legal.meldung': 'Report content',
      'legal.strafverfolgung': 'Law enforcement',
      'legal.section': 'Legal',
      'legal.docs.aria': 'Legal documents',
      'legal.notice.de': 'Legal texts are available in German only and are binding in that version.'
    }
  });

  lang = detect();
  document.documentElement.setAttribute('lang', htmlLangTag());

  // Der Regler und die Texte werden gebunden, sobald das Markup steht.
  function boot(){ apply(document); bindSwitches(document); }
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', boot);
  }else{
    boot();
  }

  return {
    t: t, has: has, apply: apply, register: register, set: set,
    current: current, onChange: onChange, bindSwitches: bindSwitches,
    LANGS: LANGS, DEFAULT: DEFAULT_LANG
  };
})();
