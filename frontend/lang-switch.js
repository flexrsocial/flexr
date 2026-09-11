/* FLEXR — Wegfuehrung zwischen der deutschen und der englischen Fassung.

   Laeuft auf der Landingpage (/ und /en/) und auf den Rechtstexten
   (/agb.html und /en/agb.html und so weiter). Welche zwei Adressen zu der
   gerade offenen Seite gehoeren, liest das Skript aus dem Regler im Markup -
   es kennt keine feste Liste.
   ============================================================================
   Deutsch und Englisch sind zwei eigene Adressen: `/` und `/en/`. Beide liefern
   ihren Text fertig im HTML aus. Das ist der Unterschied zur Web-App unter
   /app/, die ihre Sprache zur Laufzeit umschaltet — die App steht auf noindex,
   die Landingpage nicht. Wuerde diese Seite den Text im Browser austauschen,
   saehe Google je nach Zeitzone seines Renderers englischen Fliesstext unter
   deutscher Auszeichnung.

   Dieses Skript macht deshalb nur zwei Dinge:

   1. Wer die Sprache schon einmal ausdruecklich gewaehlt hat (derselbe
      localStorage-Schluessel wie in der App), landet beim naechsten Aufruf
      direkt auf der passenden Adresse.
   2. Wer noch nie gewaehlt hat und erkennbar nicht aus dem DACH-Raum kommt,
      bekommt eine Hinweiszeile mit dem Verweis auf die andere Fassung —
      **keine** automatische Weiterleitung.

   Punkt 2 ist bewusst nur ein Hinweis: Ein Suchmaschinen-Crawler hat nie eine
   gespeicherte Wahl, wuerde also von einer automatischen Weiterleitung immer
   erfasst. Er bekaeme dann nie die deutsche Fassung von `/` zu sehen — genau
   das, was die getrennten Adressen verhindern sollen.
   ========================================================================== */
(function(){
  'use strict';

  var STORE_KEY = 'flexr_lang';           // derselbe Schluessel wie in /i18n.js

  var root = document.documentElement;

  /* Die beiden Adressen dieser Seite stehen im Regler selbst - jedes <a> dort
     traegt sein hreflang. Frueher war {de:'/', en:'/en/'} fest verdrahtet;
     seit es auch die Rechtstexte zweisprachig gibt (/agb.html und
     /en/agb.html), waere das die falsche Karte: Ein gespeichertes "de" haette
     von /en/agb.html auf die Startseite umgeleitet statt auf /agb.html.
     Der Rueckfall auf die Startseiten gilt nur, wenn eine Seite gar keinen
     Regler hat. */
  function urls(){
    var map = {de: '/', en: '/en/'};
    document.querySelectorAll('.lang-switch a[hreflang]').forEach(function(a){
      var code = String(a.getAttribute('hreflang') || '').slice(0, 2).toLowerCase();
      if(code === 'de' || code === 'en') map[code] = a.getAttribute('href');
    });
    return map;
  }
  var URLS = urls();
  /* Welche Sprache diese Adresse ausliefert, steht am <html lang> — "de-AT"
     oder "en". Kein eigenes Attribut noetig. */
  var pageLang = (root.getAttribute('lang') || 'de').slice(0, 2).toLowerCase();
  var otherLang = pageLang === 'de' ? 'en' : 'de';

  function stored(){
    try{
      var v = localStorage.getItem(STORE_KEY);
      return (v === 'de' || v === 'en') ? v : null;
    }catch(e){ return null; }   // localStorage gesperrt (privater Modus)
  }

  function remember(lang){
    try{ localStorage.setItem(STORE_KEY, lang); }catch(e){}
  }

  /* Ohne gespeicherte Wahl: Standort und Systemsprache, dieselbe Reihenfolge
     wie in /i18n.js (DACH-Raum -> Deutsch, sonst Browsersprache, sonst
     Englisch). Bewusst hier wiederholt statt /i18n.js zu laden: dieses Skript
     laeuft mit `defer` und braucht die Uebersetzungsmaschinerie nicht. */
  var DACH_ZONES = [
    'Europe/Vienna', 'Europe/Berlin', 'Europe/Zurich',
    'Europe/Busingen', 'Europe/Vaduz'
  ];

  function detect(){
    try{
      var tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if(tz && DACH_ZONES.indexOf(tz) >= 0) return 'de';
    }catch(e){}
    var tags = (navigator.languages && navigator.languages.length)
      ? navigator.languages
      : [navigator.language || ''];
    for(var i = 0; i < tags.length; i++){
      var tag = String(tags[i] || '').toLowerCase();
      if(!tag) continue;
      return tag.indexOf('de') === 0 ? 'de' : 'en';
    }
    return 'de';
  }

  /* Ein Klick auf den Regler ist eine ausdrueckliche Wahl - merken, damit der
     naechste Aufruf ohne Umweg auf der richtigen Adresse landet. */
  function bindSwitch(){
    var links = document.querySelectorAll('.lang-switch a[hreflang]');
    for(var i = 0; i < links.length; i++){
      (function(a){
        a.addEventListener('click', function(){
          remember(a.getAttribute('hreflang'));
        });
      })(links[i]);
    }
  }

  /* Hinweiszeile oben, in der jeweils anderen Sprache beschriftet. */
  var NOTICE = {
    en: {text: 'This page is also available in English.', action: 'Read in English'},
    de: {text: 'Diese Seite gibt es auch auf Deutsch.', action: 'Auf Deutsch lesen'}
  };

  function showNotice(){
    var copy = NOTICE[otherLang];
    var bar = document.createElement('div');
    bar.className = 'lang-notice';
    bar.setAttribute('lang', otherLang);
    // Der Hinweis ist nicht der Inhalt dieser Seite - er soll weder im
    // Suchergebnis-Auszug landen noch die Sprachbestimmung der Seite stoeren.
    bar.setAttribute('data-nosnippet', '');

    var text = document.createElement('span');
    text.textContent = copy.text;

    var link = document.createElement('a');
    link.href = URLS[otherLang];
    link.setAttribute('hreflang', otherLang);
    link.textContent = copy.action + ' →';
    link.addEventListener('click', function(){ remember(otherLang); });

    var close = document.createElement('button');
    close.type = 'button';
    close.className = 'lang-notice-close';
    close.setAttribute('aria-label', otherLang === 'en' ? 'Dismiss' : 'Schließen');
    close.textContent = '✕';
    close.addEventListener('click', function(){
      bar.remove();
      // Wegklicken heisst: diese Sprache ist recht so.
      remember(pageLang);
    });

    bar.appendChild(text);
    bar.appendChild(link);
    bar.appendChild(close);
    // Hinter den Sprungverweis, nicht davor: sonst fuehrt der erste Tastendruck
    // in die Hinweiszeile statt zu "Zum Inhalt springen".
    var skip = document.querySelector('.skip-link');
    if(skip && skip.nextSibling){
      document.body.insertBefore(bar, skip.nextSibling);
    }else{
      document.body.insertBefore(bar, document.body.firstChild);
    }
  }

  bindSwitch();

  var choice = stored();
  if(choice){
    // Ausdrueckliche Wahl gilt: liegt sie quer zu dieser Adresse, umleiten.
    // `replace` statt `assign`, damit der Zurueck-Knopf nicht in eine
    // Weiterleitungsschleife laeuft.
    if(choice !== pageLang) location.replace(URLS[choice]);
    return;
  }

  if(detect() !== pageLang) showNotice();
})();
