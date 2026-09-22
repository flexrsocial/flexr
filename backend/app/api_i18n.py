"""Fehlermeldungen der API in der Sprache des Clients.

Die Routen formulieren ihre Fehler auf Deutsch - das ist die Ausgangssprache,
und so stehen sie auch im Code und in den Tests. Bis zum 22.09.2026 kamen sie
genau so auch bei englischen Nutzern an ("E-Mail oder Passwort falsch.").

Statt jede der rund hundert Aufrufstellen umzubauen, uebersetzt ein zentraler
Exception-Handler (siehe main.py) den fertigen Text, wenn der Client Englisch
verlangt. Die Clients schicken dafuer ``Accept-Language`` mit der in der App
gewaehlten Sprache.

Unbekannte Texte bleiben unveraendert - eine vergessene Uebersetzung liest
sich dann deutsch, sie bricht aber nichts. ``tests/test_api_i18n.py`` prueft,
dass jede Meldung aus einer ``HTTPException`` hier eine Uebersetzung hat.

Texte mit eingesetzten Werten stehen als Muster mit ``{name}`` darin; der
Platzhalter nimmt beliebigen Text auf und wird ins Englische uebernommen.
"""

import re

from fastapi import Request

# ---------------------------------------------------------------------------
# Deutsch -> Englisch
# ---------------------------------------------------------------------------

_TEXTE: dict[str, str] = {
    # ---- Anmeldung / Konto
    "E-Mail oder Passwort falsch.": "Incorrect email or password.",
    "Konto wegen zu vieler Fehlversuche vorübergehend gesperrt. Bitte in ein paar Minuten erneut versuchen.":
        "Account temporarily locked after too many failed attempts. Please try again in a few minutes.",
    "Zu viele Fehlversuche. Bitte versuche es in {minuten} Minuten erneut.":
        "Too many failed attempts. Please try again in {minuten} minutes.",
    "Ungültige oder abgelaufene Anmeldung.": "Invalid or expired sign-in. Please log in again.",
    "Not authenticated": "Not signed in. Please log in.",
    "Dieses Konto wurde gelöscht.": "This account has been deleted.",
    "Dieses Konto wurde gelöscht. Bis zum {datum} kannst du es noch reaktivieren.":
        "This account has been deleted. You can still reactivate it until {datum}.",
    "Dieses Konto ist nicht gelöscht.": "This account is not deleted.",
    "E-Mail bereits registriert.": "This email address is already registered.",
    "Diese E-Mail-Adresse ist bereits registriert.": "This email address is already registered.",
    "Das ist bereits deine E-Mail-Adresse.": "That is already your email address.",
    "Wegwerf-E-Mail-Adressen sind nicht erlaubt.": "Disposable email addresses are not allowed.",
    "Registrierung von diesem Gerät nicht möglich.": "Registration is not possible from this device.",
    "Die Registrierung ist von diesem Gerät derzeit nicht möglich. Bitte versuche es später erneut oder wende dich an flexr.social@proton.me.":
        "Registration from this device is currently not possible. Please try again later or contact flexr.social@proton.me.",
    "Du musst mindestens 18 Jahre alt sein, um FLEXR nutzen zu können.":
        "You must be at least 18 years old to use FLEXR.",
    "Bitte ein gültiges Geburtsdatum angeben.": "Please enter a valid date of birth.",
    "Unbekanntes Gym. Bitte aus der Liste wählen oder vorschlagen.":
        "Unknown gym. Please choose one from the list or suggest it.",
    "Falsches Passwort.": "Incorrect password.",
    "Das aktuelle Passwort stimmt nicht.": "The current password is incorrect.",
    "Das neue Passwort ist dasselbe wie das bisherige.": "The new password is the same as the old one.",
    "Das Passwort darf höchstens 72 Bytes lang sein.": "The password may be at most 72 bytes long.",
    "Einwilligung zur Verarbeitung sensibler Daten ist erforderlich.":
        "Consent to the processing of sensitive data is required.",
    # ---- Links aus Mails (Bestaetigung, Passwort zuruecksetzen)
    "Dieser Bestätigungslink ist ungültig oder wurde bereits benutzt. Fordere in der App einen neuen an.":
        "This confirmation link is invalid or has already been used. Request a new one in the app.",
    "Dieser Bestätigungslink ist abgelaufen (er gilt {stunden} Stunden). Fordere in der App einen neuen an.":
        "This confirmation link has expired (it is valid for {stunden} hours). Request a new one in the app.",
    "Zu diesem Link gibt es kein Konto mehr.": "There is no longer an account for this link.",
    "Dieser Link gehört zu einer anderen E-Mail-Adresse. Fordere einen neuen an.":
        "This link belongs to a different email address. Request a new one.",
    "Deine E-Mail-Adresse ist bereits bestätigt.": "Your email address is already confirmed.",
    "Dieser Link ist ungültig oder wurde bereits benutzt. Fordere über „Passwort vergessen?“ einen neuen an.":
        "This link is invalid or has already been used. Request a new one via “Forgot password?”.",
    "Dieser Link ist abgelaufen (er gilt {minuten} Minuten). Fordere über „Passwort vergessen?“ einen neuen an.":
        "This link has expired (it is valid for {minuten} minutes). Request a new one via “Forgot password?”.",
    "Zu diesem Link gibt es kein nutzbares Konto mehr.": "There is no usable account for this link any more.",
    # ---- Profil / Fotos
    "PLZ und Ort müssen gemeinsam aktualisiert werden.": "Postal code and town must be updated together.",
    "Postleitzahl nicht gefunden. Bitte prüfen.": "Postal code not found. Please check it.",
    "Links sind in der Bio nicht erlaubt.": "Links are not allowed in your bio.",
    "Telefonnummern sind in der Bio nicht erlaubt.": "Phone numbers are not allowed in your bio.",
    "Dieser Inhalt ist in der Bio nicht erlaubt.": "This content is not allowed in your bio.",
    "Maximal {n} Fotos erlaubt.": "A maximum of {n} photos is allowed.",
    "Mindestens {n} Fotos sind erforderlich. Lade zuerst ein weiteres hoch.":
        "At least {n} photos are required. Upload another one first.",
    "Lade zuerst mindestens {n} Profilfotos hoch.": "Upload at least {n} profile photos first.",
    "Ungültiger object_key.": "Invalid object key.",
    "Ungültiger thumb_object_key.": "Invalid thumbnail key.",
    "Doppelte Foto-ID in der Reihenfolge.": "Duplicate photo ID in the order.",
    "Die Reihenfolge muss genau die eigenen Fotos enthalten.": "The order must contain exactly your own photos.",
    "Die hochgeladene Datei ist kein unterstütztes Bild oder zu groß.":
        "The uploaded file is not a supported image or is too large.",
    "Foto nicht gefunden.": "Photo not found.",
    "Das Gym kann nur alle drei Monate geändert werden (Schutz vor Umgehung des FLEXR-Premium-Suchumkreises) - nächste Änderung ab {datum} möglich.":
        "Your gym can only be changed every three months (so the FLEXR Premium search radius cannot be bypassed) - next change possible from {datum}.",
    "Dieses Gym wurde bereits geprüft und abgelehnt.": "This gym has already been reviewed and rejected.",
    "Gym nicht gefunden.": "Gym not found.",
    # ---- Swipes / Matches / Chat
    "Du kannst nicht mit dir selbst swipen.": "You cannot swipe on yourself.",
    "Nutzer nicht gefunden.": "User not found.",
    "Du hast die Einwilligung in die Verarbeitung von Geschlecht und gesuchtem Geschlecht widerrufen - ohne sie können wir niemanden vorschlagen und kein Match herstellen. Du kannst sie in den Einstellungen jederzeit wieder erteilen.":
        "You have withdrawn your consent to the processing of your gender and the gender you are looking for - without it we cannot suggest anyone or create a match. You can give it again at any time in the settings.",
    "Es gibt keinen Swipe zum Zurücknehmen.": "There is no swipe to undo.",
    "Daraus ist schon ein Match geworden - das lässt sich nur auflösen, nicht zurücknehmen.":
        "That has already become a match - it can only be dissolved, not undone.",
    "Den letzten Swipe zurücknehmen gibt es mit FLEXR Premium.": "Undoing your last swipe comes with FLEXR Premium.",
    "Du hast deine {n} Likes für heute aufgebraucht. In ein paar Stunden geht es weiter.":
        "You have used up your {n} likes for today. You can continue in a few hours.",
    "Du hast deine {n} Likes für heute aufgebraucht. Mit FLEXR Premium likest du ohne Grenze - sonst geht es in ein paar Stunden weiter.":
        "You have used up your {n} likes for today. With FLEXR Premium you can like without limits - otherwise you can continue in a few hours.",
    "Du hast {n} Unterhaltungen offen - mehr gehen gleichzeitig nicht. Löse ein Match auf, dann wird ein Platz frei.":
        "You have {n} conversations open - that is the maximum at once. Dissolve a match to free up a slot.",
    "Du hast {n} Unterhaltungen offen - mehr gehen ohne FLEXR Premium nicht gleichzeitig. Löse ein Match auf oder hol dir Premium für unbegrenzt viele Chats.":
        "You have {n} conversations open - that is the maximum at once without FLEXR Premium. Dissolve a match or get Premium for unlimited chats.",
    "Match nicht gefunden.": "Match not found.",
    "Chat nicht verfügbar.": "Chat not available.",
    "Nachricht nicht gefunden.": "Message not found.",
    # ---- Sicherheit
    "Du kannst dich nicht selbst melden.": "You cannot report yourself.",
    "Du kannst dich nicht selbst blockieren.": "You cannot block yourself.",
    "Blockierung nicht gefunden.": "Block not found.",
    "Meldung nicht gefunden.": "Report not found.",
    "Diese Meldung wurde bereits entschieden.": "This report has already been decided.",
    # ---- Verifizierung
    "Dein Konto ist noch nicht freigeschaltet. Schließe zuerst die Alters- und Identitätsprüfung ab.":
        "Your account has not been activated yet. Complete the age and identity check first.",
    "Bestätige zuerst deine E-Mail-Adresse.": "Confirm your email address first.",
    "Dein Profil ist bereits verifiziert.": "Your profile is already verified.",
    "Deine Verifizierung wurde abgeschlossen und kann nicht erneut gestartet werden. Melde dich bei Fragen unter flexr.social@proton.me.":
        "Your verification has been completed and cannot be started again. If you have questions, contact flexr.social@proton.me.",
    "Deine Verifizierung ist bereits in Prüfung.": "Your verification is already being reviewed.",
    "Keine laufende Verifizierung. Bitte zuerst starten.": "No verification in progress. Please start it first.",
    "Die Aufnahmen passen nicht zu den angeforderten Selfies.": "The pictures do not match the requested selfies.",
    "Für diesen Schritt läuft keine offene Verifizierung.": "There is no open verification for this step.",
    "Bitte zuerst die Selfie-Verifizierung wiederholen.": "Please repeat the selfie verification first.",
    "Die Aufnahme ist zu groß (max. {n} MB).": "The picture is too large (max. {n} MB).",
    "Für dieses Dokument brauchen wir auch eine Aufnahme der Rückseite.":
        "For this document we also need a picture of the back.",
    "Die Aufnahme konnte nicht gelesen werden. Bitte erneut hochladen.":
        "The picture could not be read. Please upload it again.",
    "Die Aufnahme ist kein gültiges Bild oder zu groß. Bitte als JPEG oder PNG erneut hochladen.":
        "The picture is not a valid image or is too large. Please upload it again as JPEG or PNG.",
    "Es liegt keine eingereichte Aufnahme vor.": "There is no submitted picture.",
    "Verifizierungsanfrage nicht gefunden.": "Verification request not found.",
    # ---- Premium / Abo
    "FLEXR ist derzeit für alle unbegrenzt nutzbar - FLEXR Premium ist noch nicht bestellbar.":
        "FLEXR is currently unlimited for everyone - FLEXR Premium cannot be ordered yet.",
    "FLEXR Premium kann in dieser App nicht abgeschlossen werden.": "FLEXR Premium cannot be purchased in this app.",
    "Für dieses Konto läuft bereits FLEXR Premium.": "This account already has FLEXR Premium.",
    "Noch kein Abo abgeschlossen.": "No subscription yet.",
    "Die Zahlung kann gerade nicht gestartet werden. Bitte versuch es in ein paar Minuten noch einmal - es wurde nichts abgebucht.":
        "The payment cannot be started right now. Please try again in a few minutes - nothing has been charged.",
    "Die Abo-Verwaltung ist gerade nicht erreichbar. Bitte versuch es in ein paar Minuten noch einmal.":
        "Subscription management is not available right now. Please try again in a few minutes.",
    "FLEXR Premium ist derzeit nicht bestellbar.": "FLEXR Premium cannot be ordered at the moment.",
    "Ohne diese Erklärung kann der kostenpflichtige Zugang nicht sofort beginnen.":
        "Without this statement the paid access cannot start immediately.",
    "Ohne diese Kenntnisnahme kann der Checkout nicht gestartet werden.":
        "Without this acknowledgement the checkout cannot be started.",
    "Nicht gefunden.": "Not found.",
    # ---- Ruecktritt / Meldeverfahren (oeffentliche Formulare)
    "Bitte den Rücktritt im zweiten Schritt bestätigen.": "Please confirm the withdrawal in the second step.",
    "Ohne die Erklärung, dass die Angaben nach bestem Wissen richtig und vollständig sind, können wir die Meldung nicht bearbeiten.":
        "Without the statement that the information is accurate and complete to the best of your knowledge, we cannot process the report.",
    "Für diese Kategorie brauchen wir Name und E-Mail-Adresse, damit wir dir den Eingang und die Entscheidung mitteilen können.":
        "For this category we need your name and email address so we can confirm receipt and tell you our decision.",
    # ---- Admin (nur deutsch bedient, der Vollstaendigkeit halber)
    "2FA ist bereits aktiviert.": "2FA is already enabled.",
    "Code stimmt nicht überein.": "Code does not match.",
    "Nur abgelehnte Einträge können gelöscht werden.": "Only rejected entries can be deleted.",
    "Name darf nicht leer sein.": "Name must not be empty.",
    "Ungültiger Status-Filter.": "Invalid status filter.",
    "Ein Gym mit diesem Namen und dieser PLZ existiert bereits.": "A gym with this name and postal code already exists.",
    "Sperrdauer muss größer als 0 sein.": "The suspension must be longer than 0.",
    # ---- Store-/Stripe-Schnittstellen (technisch, kein Nutzertext im engeren Sinn)
    "Ungültige Webhook-Signatur.": "Invalid webhook signature.",
    "Ungueltige Signatur.": "Invalid signature.",
    "Unlesbare Benachrichtigung.": "Unreadable notification.",
    "Ungueltiger Beleg.": "Invalid receipt.",
}

# Interne Codes, die die Clients vergleichen - bleiben unuebersetzt.
_CODES = {"totp_required", "totp_invalid"}


def _muster(deutsch: str) -> re.Pattern:
    teile = re.split(r"\{(\w+)\}", deutsch)
    regex = ""
    for i, teil in enumerate(teile):
        regex += re.escape(teil) if i % 2 == 0 else f"(?P<{teil}>.+?)"
    return re.compile("^" + regex + "$", re.S)


_EXAKT = {de: en for de, en in _TEXTE.items() if "{" not in de}
_MUSTER = [(_muster(de), en) for de, en in _TEXTE.items() if "{" in de]


def translate(text: str, lang: str) -> str:
    """Deutschen API-Text in ``lang`` liefern (unbekannt: unveraendert)."""
    if lang != "en" or not isinstance(text, str) or text in _CODES:
        return text
    if text in _EXAKT:
        return _EXAKT[text]
    for muster, englisch in _MUSTER:
        treffer = muster.match(text)
        if treffer:
            return englisch.format(**treffer.groupdict())
    return text


def has_translation(text: str) -> bool:
    return text in _CODES or text in _EXAKT or any(m.match(text) for m, _ in _MUSTER)


def request_language(request: Request) -> str:
    """Sprache aus ``Accept-Language``: Englisch nur, wenn der Client es
    ausdruecklich an erster Stelle nennt - sonst die Ausgangssprache."""
    header = request.headers.get("accept-language", "")
    erste = header.split(",")[0].strip().lower()
    return "en" if erste.startswith("en") else "de"


def translate_detail(detail, lang: str):
    """Ein HTTPException-Detail uebersetzen: Text, oder Objekt mit ``message``."""
    if lang != "en":
        return detail
    if isinstance(detail, str):
        return translate(detail, lang)
    if isinstance(detail, dict) and isinstance(detail.get("message"), str):
        return {**detail, "message": translate(detail["message"], lang)}
    return detail


# ---------------------------------------------------------------------------
# Validierungsfehler (422)
# ---------------------------------------------------------------------------
#
# Die Clients zeigen bei 422 die "msg" jedes Eintrags an. Pydantic formuliert
# die auf Englisch ("String should have at least 1 character") und stellt
# eigenen Pruefungen "Value error, " voran - beides sah bisher jeder Nutzer.

_PYDANTIC_DE = {
    "missing": "Pflichtfeld fehlt",
    "string_too_short": "Eingabe zu kurz",
    "string_too_long": "Eingabe zu lang",
    "too_short": "Zu wenige Einträge",
    "too_long": "Zu viele Einträge",
    "string_pattern_mismatch": "Ungültiges Format",
    "value_error": "Ungültiger Wert",
    "literal_error": "Ungültige Auswahl",
    "less_than_equal": "Wert zu groß",
    "greater_than_equal": "Wert zu klein",
    "less_than": "Wert zu groß",
    "greater_than": "Wert zu klein",
    "int_parsing": "Bitte eine Zahl angeben",
    "bool_parsing": "Ungültiger Wert",
    "date_from_datetime_parsing": "Ungültiges Datum",
    "date_parsing": "Ungültiges Datum",
    "json_invalid": "Ungültige Anfrage",
}

_PYDANTIC_EN = {
    "missing": "Required field missing",
    "string_too_short": "Input too short",
    "string_too_long": "Input too long",
    "string_pattern_mismatch": "Invalid format",
    "value_error": "Invalid value",
    "literal_error": "Invalid choice",
    "json_invalid": "Invalid request",
}

_FELDNAMEN = {
    "de": {"email": "E-Mail", "new_email": "E-Mail", "password": "Passwort",
           "new_password": "Passwort", "name": "Name", "plz": "Postleitzahl",
           "bio": "Bio", "content": "Nachricht", "birthdate": "Geburtsdatum"},
    "en": {"email": "Email", "new_email": "Email", "password": "Password",
           "new_password": "Password", "name": "Name", "plz": "Postal code",
           "bio": "Bio", "content": "Message", "birthdate": "Date of birth"},
}


def _validation_msg(fehler: dict, lang: str) -> str:
    typ = fehler.get("type", "")
    msg = str(fehler.get("msg", ""))
    if typ == "value_error" and msg.startswith("Value error, "):
        # Eigene Pruefung - der Text ist schon ein fertiger Satz.
        return translate(msg[len("Value error, "):], lang)
    if typ == "value_error" and "email address" in msg:
        return "Invalid email address." if lang == "en" else "Ungültige E-Mail-Adresse."
    tabelle = _PYDANTIC_EN if lang == "en" else _PYDANTIC_DE
    grund = tabelle.get(typ)
    if grund is None:
        return msg if lang == "en" else "Ungültige Eingabe"
    loc = fehler.get("loc") or ()
    feld = str(loc[-1]) if loc else ""
    name = _FELDNAMEN[lang].get(feld)
    return f"{name}: {grund}" if name else grund


def translate_validation_errors(errors: list, lang: str) -> list:
    """Dieselbe Liste, aber mit lesbaren "msg"-Texten in ``lang``. Alle anderen
    Felder (type, loc, ...) bleiben stehen - Clients, die darauf schauen,
    merken keinen Unterschied."""
    ergebnis = []
    for fehler in errors:
        eintrag = {k: v for k, v in fehler.items() if k not in ("ctx", "url")}
        if "ctx" in fehler:
            # ctx kann Exceptions enthalten, die nicht JSON-serialisierbar sind.
            eintrag["ctx"] = {k: str(v) for k, v in fehler["ctx"].items()}
        eintrag["msg"] = _validation_msg(fehler, lang)
        ergebnis.append(eintrag)
    return ergebnis
