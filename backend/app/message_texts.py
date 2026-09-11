"""Woerterbuch der Texte, die der Server verschickt (Deutsch / Englisch).

Betrifft E-Mails (app/mailer.py) und Push-Benachrichtigungen
(app/notifications.py) - beides entsteht zum Teil ohne Client: im Tagesjob, im
Stripe-Webhook, im Admin-Bereich. Die Sprache kommt deshalb aus
``User.language`` und nicht aus einem Request-Header.

Warum ein eigenes Modul und keine zweite Fassung von ``mailer.py``:

Die Mails bestehen aus zwei Teilen - einem Geruest (HTML-Karte, Absaetze,
Tabellenzeilen, Klartext-Umbrueche) und den Saetzen darin. Nur die Saetze
haengen an der Sprache. Zwei vollstaendige Mailer nebeneinander haetten das
Geruest verdoppelt, und die beiden Fassungen waeren beim naechsten Umbau
auseinandergelaufen - genau der Grund, aus dem die englische Landingpage
erzeugt und nicht von Hand gepflegt wird (siehe frontend/build-en.py).

Deutsch ist die Ausgangssprache. Fehlt ein englischer Eintrag, faellt ``t()``
auf den deutschen zurueck statt auf den nackten Schluessel - eine vergessene
Uebersetzung sieht dann nach deutschem Text aus und nicht nach einem Fehler.
Dieselbe Regel wie in frontend/i18n.js.

Platzhalter stehen in geschweiften Klammern und werden ueber ``str.format``
gefuellt. Wer hier einen Text mit einer echten geschweiften Klammer eintraegt,
muss sie verdoppeln.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

SPRACHEN = ("de", "en")
STANDARD = "de"

VIENNA = ZoneInfo("Europe/Vienna")


def normalise(lang: str | None) -> str:
    """Alles, was kein bekanntes Kuerzel ist, wird zur Ausgangssprache.

    Nimmt auch "de-AT" oder "EN" entgegen - die Clients schicken je nach
    Plattform mal das eine, mal das andere.
    """
    if not lang:
        return STANDARD
    kurz = str(lang)[:2].lower()
    return kurz if kurz in SPRACHEN else STANDARD


# ---------------------------------------------------------------------------
# Formatierungen, die sich mit der Sprache aendern
# ---------------------------------------------------------------------------


def format_datetime(timestamp: int | None, lang: str = STANDARD) -> str:
    """Unix-Zeitstempel aus Stripe-Payloads als Datum mit Uhrzeit."""
    lang = normalise(lang)
    if not timestamp:
        return t("date.unknown", lang)
    value = datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone(VIENNA)
    if lang == "en":
        # Ohne fuehrende Null und mit ausgeschriebenem Monat - "09/11/2026"
        # waere fuer britische und amerikanische Leser verschieden.
        return f"{value.day} {value.strftime('%B %Y')} at {value.strftime('%H:%M')}"
    return value.strftime("%d.%m.%Y um %H:%M Uhr")


def format_date(value: datetime, lang: str = STANDARD) -> str:
    """Naiver UTC-Zeitstempel aus der Datenbank als reines Datum."""
    lokal = value.replace(tzinfo=timezone.utc).astimezone(VIENNA)
    if normalise(lang) == "en":
        return f"{lokal.day} {lokal.strftime('%B %Y')}"
    return lokal.strftime("%d.%m.%Y")


def format_money(amount_cents: int | None, currency: str | None, lang: str = STANDARD) -> str:
    """Betrag mit Waehrungskuerzel - Komma im Deutschen, Punkt im Englischen."""
    amount = (amount_cents or 0) / 100
    code = (currency or "EUR").upper()
    if normalise(lang) == "en":
        return f"{amount:.2f} {code}"
    return f"{amount:.2f} {code}".replace(".", ",")


# ---------------------------------------------------------------------------
# Die Texte
# ---------------------------------------------------------------------------

TEXTE: dict[str, dict[str, str]] = {
    # ---- Geruest, in jeder Mail ----
    "html.lang": {"de": "de", "en": "en"},
    "greeting": {"de": "Hallo {name},", "en": "Hi {name},"},
    "greeting.plain": {"de": "Hallo,", "en": "Hello,"},
    "signoff": {"de": "Dein FLEXR-Team", "en": "Your FLEXR team"},
    "questions.reply": {
        "de": "Fragen? Antworte einfach auf diese Mail.",
        "en": "Questions? Just reply to this email.",
    },
    "footer.questions": {
        "de": "Fragen? Antworte einfach auf diese Mail oder schreib an",
        "en": "Questions? Just reply to this email or write to",
    },
    "date.unknown": {"de": "noch nicht bekannt", "en": "not known yet"},
    "value.none": {"de": "— keine Angabe —", "en": "— not stated —"},

    # ---- Bestaetigungsmail nach der Registrierung ----
    "verify.subject": {
        "de": "Bestätige deine E-Mail-Adresse für FLEXR",
        "en": "Confirm your email address for FLEXR",
    },
    "verify.eyebrow": {"de": "Erste Wiederholung", "en": "First rep"},
    "verify.heading": {
        "de": "Willkommen bei FLEXR, {name}!",
        "en": "Welcome to FLEXR, {name}!",
    },
    "verify.afterCheck": {
        "de": (
            "erst danach ist dein Konto freigeschaltet. Die Nutzung von FLEXR ist "
            "und bleibt kostenlos - die Prüfzeit kostet dich nichts."
        ),
        "en": (
            "only then is your account activated. Using FLEXR is and stays free - "
            "the time the check takes costs you nothing."
        ),
    },
    "verify.text.intro": {
        "de": (
            "dein FLEXR-Profil ist angelegt. Bevor es weitergeht, bestätige bitte\n"
            "einmalig deine E-Mail-Adresse:"
        ),
        "en": (
            "your FLEXR profile is set up. Before you go on, please confirm your\n"
            "email address once:"
        ),
    },
    "verify.text.ttl": {
        "de": (
            "Der Link gilt {hours} Stunden. Danach steht die einmalige Alters- "
            "und Identitätsprüfung an - {after}"
        ),
        "en": (
            "The link is valid for {hours} hours. After that comes the one-off age "
            "and identity check - {after}"
        ),
    },
    "verify.html.intro": {
        "de": (
            "Dein Profil ist angelegt. Bevor es weitergeht, bestätige bitte einmalig "
            "deine E-Mail-Adresse. Der Link gilt {hours} Stunden."
        ),
        "en": (
            "Your profile is set up. Before you go on, please confirm your email "
            "address once. The link is valid for {hours} hours."
        ),
    },
    "verify.cta": {"de": "E-Mail bestätigen", "en": "Confirm email"},
    "verify.fallback": {
        "de": "Klappt der Knopf nicht? Kopier diese Adresse in deinen Browser:",
        "en": "Button not working? Copy this address into your browser:",
    },
    "verify.html.check": {
        "de": "Danach steht die einmalige <b>Alters- und Identitätsprüfung</b> an - {after}",
        "en": "After that comes the one-off <b>age and identity check</b> - {after}",
    },
    "verify.needed": {"de": "Das brauchst du dafür:", "en": "Here is what you need for it:"},
    "verify.step1": {
        "de": "Ein Live-Selfie, frontal in die Kamera (direkt in der App aufgenommen)",
        "en": "A live selfie, facing the camera (taken directly in the app)",
    },
    "verify.step2": {
        "de": "Eine Aufnahme deines amtlichen Lichtbildausweises",
        "en": "An image of your official photo ID",
    },
    "verify.manual": {
        "de": (
            "Die Prüfung erfolgt manuell durch einen Menschen - es kommt keine "
            "automatische Gesichtserkennung zum Einsatz. Die Aufnahmen werden nach "
            "Abschluss der Prüfung gelöscht."
        ),
        "en": (
            "The check is done manually by a person - no automated facial recognition "
            "is used. The images are deleted once the check is complete."
        ),
    },
    "verify.notYou": {
        "de": (
            "Du hast dich nicht bei FLEXR angemeldet? Dann ignoriere diese Mail "
            "einfach. Ohne Bestätigung passiert mit der Adresse nichts."
        ),
        "en": (
            "Didn’t sign up to FLEXR? Then simply ignore this email - without "
            "confirmation nothing happens with the address."
        ),
    },
    "verify.signoff": {"de": "Bis gleich im Gym,", "en": "See you at the gym,"},
    # Nach dem Komma der Zeile darueber - deshalb klein, anders als der
    # alleinstehende "signoff" in allen uebrigen Mails.
    "verify.signoffTeam": {"de": "dein FLEXR-Team", "en": "your FLEXR team"},

    # ---- Vertragsbestaetigung (FLEXR Premium) ----
    "subscription.subject": {
        "de": "Bestätigung deines FLEXR-Abos",
        "en": "Confirmation of your FLEXR subscription",
    },
    "subscription.eyebrow": {"de": "Abo bestätigt", "en": "Subscription confirmed"},
    "subscription.intro": {
        "de": "danke für dein Abo. Diese Mail bestätigt den Vertragsabschluss.",
        "en": "thank you for subscribing. This email confirms the conclusion of the contract.",
    },
    "subscription.kv.service": {"de": "Leistung", "en": "Service"},
    "subscription.kv.serviceValue": {
        "de": "FLEXR-Mitgliedschaft (flexr.social)",
        "en": "FLEXR membership (flexr.social)",
    },
    "subscription.kv.price": {"de": "Preis", "en": "Price"},
    "subscription.kv.priceValue": {
        "de": "{price} € pro Monat, Endpreis",
        "en": "{price} € per month, final price",
    },
    "subscription.kv.billing": {"de": "Abrechnung", "en": "Billing"},
    "subscription.kv.billingValue": {
        "de": "monatlich, automatische Verlängerung",
        "en": "monthly, renews automatically",
    },
    "subscription.kv.term": {"de": "Laufzeit", "en": "Term"},
    "subscription.kv.termValue": {
        "de": "keine Mindestlaufzeit, monatlich kündbar",
        "en": "no minimum term, cancellable monthly",
    },
    "subscription.kv.cancel": {"de": "Kündigen", "en": "Cancelling"},
    "subscription.kv.cancelValue": {
        "de": 'jederzeit im Konto unter "Abo verwalten / kündigen"',
        "en": 'any time in your account under “Manage / cancel subscription”',
    },
    "subscription.immediateStart": {
        "de": (
            "Du hast vor dem Abschluss ausdrücklich verlangt, dass wir mit der "
            "kostenpflichtigen Leistung schon vor Ablauf der 14-tägigen "
            "Rücktrittsfrist beginnen. Dein gesetzliches Rücktrittsrecht bleibt "
            "davon unberührt - bei einem Rücktritt kann lediglich ein anteiliger "
            "Wertersatz für die bereits erbrachte Leistung anfallen. Alles dazu, "
            "inklusive der Online-Funktion, steht unter {url}."
        ),
        "en": (
            "Before concluding the contract you expressly requested that we begin "
            "the paid service before the 14-day withdrawal period has expired. Your "
            "statutory right of withdrawal remains unaffected - on withdrawal only a "
            "pro-rata amount for the service already provided may become payable. "
            "Everything about it, including the online function, is at {url}."
        ),
    },

    # ---- Abo-Lebenszyklus ----
    "trial.subject": {
        "de": "Dein FLEXR-Gratismonat endet bald",
        "en": "Your free FLEXR month ends soon",
    },
    "trial.eyebrow": {"de": "Gratismonat endet bald", "en": "Free month ending soon"},
    "trial.intro": {
        "de": (
            "dein FLEXR-Gratismonat endet am {date}. Danach wird dein bereits "
            "abgeschlossenes Abo erstmals mit {price} EUR pro Monat abgerechnet."
        ),
        "en": (
            "your free FLEXR month ends on {date}. After that, the subscription you "
            "have already taken out will be billed for the first time at {price} EUR "
            "per month."
        ),
    },
    "trial.optOut": {
        "de": (
            'Wenn du das nicht möchtest, kannst du das Abo vorher in FLEXR unter '
            '"Abo verwalten / kündigen" beenden. Bis zum Ende des Gratismonats '
            "bleibt dein Zugang erhalten."
        ),
        "en": (
            "If you don’t want that, you can end the subscription beforehand in FLEXR "
            "under “Manage / cancel subscription”. Your access stays until the free "
            "month is over."
        ),
    },
    "renewal.subject": {
        "de": "Deine nächste FLEXR-Aboverlängerung",
        "en": "Your next FLEXR subscription renewal",
    },
    "renewal.eyebrow": {"de": "Abo verlängert sich", "en": "Subscription renewing"},
    "renewal.intro": {
        "de": (
            "dein FLEXR-Abo verlängert sich am {date} um einen weiteren Monat. "
            "Der angekündigte Betrag ist {amount}."
        ),
        "en": (
            "your FLEXR subscription renews on {date} for another month. The amount "
            "announced is {amount}."
        ),
    },
    "renewal.manage": {
        "de": (
            'Du kannst dein Abo vorher jederzeit in FLEXR unter "Abo verwalten / '
            'kündigen" verwalten. Bei einer Kündigung bleibt der Zugang bis zum Ende '
            "des bereits bezahlten Zeitraums bestehen."
        ),
        "en": (
            "You can manage your subscription at any time beforehand in FLEXR under "
            "“Manage / cancel subscription”. If you cancel, access remains until the "
            "end of the period you have already paid for."
        ),
    },
    "paid.subject": {
        "de": "Zahlung für FLEXR erfolgreich",
        "en": "Payment for FLEXR successful",
    },
    "paid.eyebrow": {"de": "Zahlung erfolgreich", "en": "Payment successful"},
    "paid.intro": {
        "de": "deine Zahlung über {amount} für FLEXR war erfolgreich. Dein Abo ist weiterhin aktiv.",
        "en": "your payment of {amount} for FLEXR was successful. Your subscription remains active.",
    },
    "paid.invoice": {"de": "Rechnung/Beleg", "en": "Invoice/receipt"},
    "paid.manage": {
        "de": (
            'Du kannst dein Abo und deine Zahlungsdaten jederzeit in FLEXR unter '
            '"Abo verwalten / kündigen" verwalten.'
        ),
        "en": (
            "You can manage your subscription and payment details at any time in "
            "FLEXR under “Manage / cancel subscription”."
        ),
    },
    "failed.subject": {
        "de": "Zahlung für FLEXR fehlgeschlagen",
        "en": "Payment for FLEXR failed",
    },
    "failed.eyebrow": {"de": "Zahlung fehlgeschlagen", "en": "Payment failed"},
    "failed.intro": {
        "de": "die Zahlung über {amount} für dein FLEXR-Abo ist fehlgeschlagen. {next}",
        "en": "the payment of {amount} for your FLEXR subscription failed. {next}",
    },
    "failed.nextAttempt": {
        "de": "Der nächste Zahlungsversuch ist für {date} vorgesehen.",
        "en": "The next payment attempt is scheduled for {date}.",
    },
    "failed.noNextAttempt": {
        "de": "Stripe hat noch keinen weiteren Zahlungsversuch angekündigt.",
        "en": "Stripe has not announced a further payment attempt yet.",
    },
    "failed.check": {
        "de": (
            'Bitte prüfe deine Zahlungsdaten in FLEXR unter "Abo verwalten / '
            'kündigen". Dein Zugang bleibt während der erneuten Zahlungsversuche '
            "vorerst aktiv."
        ),
        "en": (
            "Please check your payment details in FLEXR under “Manage / cancel "
            "subscription”. Your access stays active for now while the payment is "
            "retried."
        ),
    },
    "failed.openInvoice": {"de": "Offene Rechnung", "en": "Outstanding invoice"},
    "cancelled.subject": {
        "de": "Bestätigung deiner FLEXR-Kündigung",
        "en": "Confirmation of your FLEXR cancellation",
    },
    "cancelled.eyebrow": {"de": "Kündigung vorgemerkt", "en": "Cancellation scheduled"},
    "cancelled.intro": {
        "de": (
            "deine Kündigung ist vorgemerkt. Es erfolgen keine weiteren monatlichen "
            "Verlängerungen. Dein FLEXR-Zugang bleibt bis {date} bestehen."
        ),
        "en": (
            "your cancellation is scheduled. There will be no further monthly "
            "renewals. Your FLEXR access remains until {date}."
        ),
    },
    "cancelled.undo": {
        "de": "Du kannst die Kündigung bis dahin im Stripe-Kundenportal rückgängig machen.",
        "en": "Until then you can undo the cancellation in the Stripe customer portal.",
    },
    "ended.subject": {
        "de": "Dein FLEXR-Abo ist beendet",
        "en": "Your FLEXR subscription has ended",
    },
    "ended.eyebrow": {"de": "Abo beendet", "en": "Subscription ended"},
    "ended.intro": {
        "de": (
            "dein FLEXR-Abo ist beendet. Es erfolgen keine weiteren Abbuchungen. "
            "Falls dein kostenloser Nutzungszeitraum ebenfalls abgelaufen ist, ist "
            "der Mitgliederzugang ab jetzt pausiert. Dein Konto bleibt bestehen "
            "und kann mit einem neuen Abo wieder aktiviert werden."
        ),
        "en": (
            "your FLEXR subscription has ended. No further payments will be taken. "
            "If your free usage period has also expired, member access is paused from "
            "now on. Your account remains and can be reactivated with a new "
            "subscription."
        ),
    },

    # ---- Aktivitaets-Benachrichtigungen (abbestellbar) ----
    "notify.optOut": {
        "de": (
            'Du kannst diese Benachrichtigung jederzeit in FLEXR unter '
            '"Benachrichtigungen" im Profil abschalten.'
        ),
        "en": (
            "You can turn this notification off at any time in FLEXR under "
            "“Notifications” in your profile."
        ),
    },
    "match.subject": {"de": "Neues Match mit {other}", "en": "New match with {other}"},
    "match.eyebrow": {"de": "Neues Match", "en": "New match"},
    "match.intro": {
        "de": (
            "{other} hat dich auch geliked - ihr habt ein Match. Ab jetzt könnt ihr "
            "euch in FLEXR schreiben."
        ),
        "en": (
            "{other} liked you back - you have a match. From now on you can message "
            "each other in FLEXR."
        ),
    },
    "queue.subject": {
        "de": "{count} neue Profile in deinem Umkreis",
        "en": "{count} new profiles within your radius",
    },
    "queue.eyebrow": {"de": "Neue Profile", "en": "New profiles"},
    "queue.intro": {
        "de": (
            "in deinem Suchradius warten gerade {count} neue Profile darauf, von dir "
            "bewertet zu werden."
        ),
        "en": (
            "There are {count} new profiles within your search radius waiting for you "
            "to rate them."
        ),
    },
    "likes.subject.one": {
        "de": "Ein Like wartet auf dich bei FLEXR",
        "en": "A like is waiting for you on FLEXR",
    },
    "likes.subject.many": {
        "de": "{count} Likes warten auf dich bei FLEXR",
        "en": "{count} likes are waiting for you on FLEXR",
    },
    "likes.eyebrow": {"de": "Neue Likes", "en": "New likes"},
    "likes.intro.one": {
        "de": (
            "{count} Mitglied hat dein Profil geliked - ihr habt aber noch kein "
            "Match. Öffne FLEXR und swipe zurück, dann seht ihr, ob's auch bei dir "
            "passt."
        ),
        "en": (
            "{count} member liked your profile - but you don’t have a match yet. Open "
            "FLEXR and swipe back to see whether it’s a fit for you too."
        ),
    },
    "likes.intro.many": {
        "de": (
            "{count} Mitglieder haben dein Profil geliked - ihr habt aber noch kein "
            "Match. Öffne FLEXR und swipe zurück, dann seht ihr, ob's auch bei dir "
            "passt."
        ),
        "en": (
            "{count} members liked your profile - but you don’t have a match yet. Open "
            "FLEXR and swipe back to see whether it’s a fit for you too."
        ),
    },
    "inactive.subject": {
        "de": "Lange nicht gesehen bei FLEXR",
        "en": "Long time no see on FLEXR",
    },
    "inactive.eyebrow": {"de": "Lange nicht gesehen", "en": "Long time no see"},
    "inactive.intro": {
        "de": (
            "du warst {days} Tage nicht mehr in FLEXR. In der Zwischenzeit können "
            "neue Profile in deinem Umkreis dazugekommen sein."
        ),
        "en": (
            "you haven’t been on FLEXR for {days} days. New profiles may have turned "
            "up within your radius in the meantime."
        ),
    },

    # ---- Push-Benachrichtigungen ----
    # Dieselben vier Anlaesse wie die abbestellbaren Mails oben, nur kuerzer:
    # Titel und eine Zeile. Sie entstehen an derselben Stelle
    # (notifications.py) und muessen deshalb derselben Sprache folgen - sonst
    # bekaeme ein englischer Nutzer die Mail auf Englisch und den Hinweis auf
    # dem Sperrbildschirm auf Deutsch.
    "push.match.title": {"de": "Neues Match", "en": "New match"},
    "push.match.body": {
        "de": "{other} hat dich auch geliked.",
        "en": "{other} liked you back.",
    },
    "push.queue.title": {"de": "{count} neue Profile", "en": "{count} new profiles"},
    "push.queue.body": {
        "de": "In deinem Umkreis warten neue Profile auf dich.",
        "en": "New profiles are waiting for you within your radius.",
    },
    "push.inactive.title": {"de": "Lange nicht gesehen", "en": "Long time no see"},
    "push.inactive.body": {
        "de": "Du warst {days} Tage nicht mehr in FLEXR.",
        "en": "You haven’t been on FLEXR for {days} days.",
    },
    "push.likes.title": {"de": "Neue Likes", "en": "New likes"},
    "push.likes.body.one": {
        "de": "Ein Mitglied hat dich geliked.",
        "en": "A member liked you.",
    },
    "push.likes.body.many": {
        "de": "{count} Mitglieder haben dich geliked.",
        "en": "{count} members liked you.",
    },

    # ---- Bestaetigung der Selbstloeschung ----
    "deletion.subject": {
        "de": "Bestätigung: Dein FLEXR-Konto wurde gelöscht",
        "en": "Confirmation: your FLEXR account has been deleted",
    },
    "deletion.eyebrow": {"de": "Konto gelöscht", "en": "Account deleted"},
    "deletion.intro": {
        "de": (
            "dein FLEXR-Konto wurde soeben deaktiviert. Diese Mail bestätigt deinen "
            "Löschauftrag."
        ),
        "en": (
            "Your FLEXR account has just been deactivated. This email confirms your "
            "deletion request."
        ),
    },
    "deletion.whatItMeans": {"de": "Was das bedeutet:", "en": "What that means:"},
    "deletion.point1": {
        "de": (
            "Dein Profil ist ab sofort für andere Mitglieder unsichtbar, ein Login "
            "ist vorerst nicht mehr möglich."
        ),
        "en": (
            "Your profile is invisible to other members with immediate effect, and "
            "signing in is no longer possible for now."
        ),
    },
    "deletion.point2": {
        "de": (
            "Deine Konto- und Profildaten bleiben noch bis zum {date} gespeichert "
            "({days} Tage Karenzzeit) und werden danach unwiderruflich gelöscht."
        ),
        "en": (
            "Your account and profile data stay stored until {date} ({days} days’ "
            "grace period) and are irrevocably deleted after that."
        ),
    },
    "deletion.point3": {
        "de": (
            "Dein Verifizierungs-Selfie und deine Ausweisaufnahme wurden bereits "
            "jetzt gelöscht, ohne auf die Karenzzeit zu warten."
        ),
        "en": (
            "Your verification selfie and your ID capture have already been deleted "
            "now, without waiting for the grace period."
        ),
    },
    "deletion.reactivate": {
        "de": (
            "Meinung geändert? Bis zum {date} kannst du dein Konto reaktivieren: "
            "Melde dich einfach mit deiner E-Mail-Adresse und deinem bisherigen "
            "Passwort erneut an - der Login bietet dir die Reaktivierung dann von "
            "selbst an. Nach Ablauf der Frist ist das nicht mehr möglich, und die "
            "Daten sind endgültig weg."
        ),
        "en": (
            "Changed your mind? Until {date} you can reactivate your account: simply "
            "sign in again with your email address and your existing password - the "
            "login then offers you reactivation by itself. Once the period has "
            "expired that is no longer possible, and the data is gone for good."
        ),
    },
    "deletion.notYou": {
        "de": (
            "Warst du das nicht? Dann kennt jemand dein Passwort - antworte umgehend "
            "auf diese Mail oder schreib an {support}, wir kümmern uns darum."
        ),
        "en": (
            "Wasn’t you? Then somebody knows your password - reply to this email "
            "immediately or write to {support} and we will look into it."
        ),
    },
    "deletion.privacy": {
        "de": "Einzelheiten zur Löschung stehen in unserer Datenschutzerklärung.",
        "en": "Details about deletion are in our privacy policy.",
    },

    # ---- Verifizierungsentscheidung ----
    "decision.openApp": {
        "de": (
            "Öffne FLEXR, um deinen aktuellen Status und die nächsten Schritte zu "
            "sehen. Fragen? Antworte einfach auf diese Mail oder schreib an"
        ),
        "en": (
            "Open FLEXR to see your current status and the next steps. Questions? "
            "Just reply to this email or write to"
        ),
    },
    "decision.openApp.text": {
        "de": (
            "Öffne FLEXR, um deinen aktuellen Status und die nächsten Schritte zu "
            "sehen.\nBei Fragen antworte auf diese Mail."
        ),
        "en": (
            "Open FLEXR to see your current status and the next steps.\nIf you have "
            "questions, just reply to this email."
        ),
    },
    "verified.subject": {
        "de": "Dein FLEXR-Konto ist freigeschaltet",
        "en": "Your FLEXR account is activated",
    },
    "verified.eyebrow": {"de": "Freigeschaltet", "en": "Activated"},
    "verified.detail": {
        "de": (
            "Deine Alters- und Identitätsprüfung wurde bestätigt. Dein Konto ist "
            "jetzt freigeschaltet."
        ),
        "en": (
            "Your age and identity check has been confirmed. Your account is now "
            "activated."
        ),
    },
    "reupload.subject": {
        "de": "FLEXR braucht eine neue Verifizierungsaufnahme",
        "en": "FLEXR needs a new verification image",
    },
    "reupload.eyebrow": {"de": "Nachbesserung nötig", "en": "Correction needed"},
    "reupload.detail": {
        "de": "Bitte lade {what} erneut hoch. Grund: {reason}",
        "en": "Please upload {what} again. Reason: {reason}",
    },
    "reupload.both": {"de": "Selfie und Ausweisaufnahme", "en": "the selfie and the ID capture"},
    "reupload.idOnly": {"de": "Ausweisaufnahme", "en": "the ID capture"},
    "reupload.fallbackReason": {
        "de": "Aufnahme nicht verwertbar.",
        "en": "Image not usable.",
    },
    "rejected.subject": {
        "de": "Deine FLEXR-Verifizierung wurde abgelehnt",
        "en": "Your FLEXR verification was rejected",
    },
    "rejected.eyebrow": {"de": "Verifizierung abgelehnt", "en": "Verification rejected"},
    "rejected.detail": {
        "de": "Die Prüfung konnte nicht bestätigt werden. Grund: {reason}",
        "en": "The check could not be confirmed. Reason: {reason}",
    },
    "rejected.fallbackReason": {
        "de": "Prüfung nicht erfolgreich.",
        "en": "Check not successful.",
    },

    # ---- Aufforderung zur Verifizierung ----
    "required.subject": {
        "de": "Alters- und Identitätsprüfung für dein FLEXR-Konto",
        "en": "Age and identity check for your FLEXR account",
    },
    "required.eyebrow": {"de": "Prüfung erforderlich", "en": "Check required"},
    "required.intro": {
        "de": (
            "für dein FLEXR-Konto ist eine Alters- und Identitätsprüfung "
            "erforderlich. Dein Konto ist bis zum Abschluss vorübergehend pausiert."
        ),
        "en": (
            "an age and identity check is required for your FLEXR account. Your "
            "account is paused temporarily until it is complete."
        ),
    },
    "required.steps": {
        "de": (
            "Öffne FLEXR und folge dort den Schritten für Live-Selfie und amtlichen "
            "Lichtbildausweis. Die Prüfung erfolgt manuell; es findet keine "
            "automatische Gesichtserkennung statt. Die Prüfaufnahmen werden "
            "anschließend gelöscht."
        ),
        "en": (
            "Open FLEXR and follow the steps there for the live selfie and the "
            "official photo ID. The check is done manually; no automated facial "
            "recognition takes place. The images used for the check are deleted "
            "afterwards."
        ),
    },
    "required.questions": {
        "de": "Bei Fragen antworte auf diese Mail.",
        "en": "If you have questions, just reply to this email.",
    },

    # ---- Moderationsmitteilung (Art. 17 DSA) ----
    "moderation.subject": {
        "de": "Wichtige Mitteilung zu deinem FLEXR-Konto",
        "en": "Important notice about your FLEXR account",
    },
    "moderation.eyebrow": {"de": "Kontomitteilung", "en": "Account notice"},
    "moderation.reasonLabel": {"de": "Begründung", "en": "Reason"},
    "moderation.detailsLabel": {"de": "Einzelheiten:", "en": "Details:"},
    "moderation.appeal": {
        "de": (
            "Du kannst der Entscheidung formlos per Antwort auf diese Mail "
            "widersprechen. Wir prüfen sie dann erneut und antworten begründet. "
            "Der Rechtsweg bleibt unbenommen."
        ),
        "en": (
            "You can object to the decision informally by replying to this email. We "
            "then review it again and respond with reasons. Your right to take legal "
            "action remains unaffected."
        ),
    },
    # Die Begruendung selbst schreibt ein Mensch im Admin-Bereich - auf Deutsch.
    # Uebersetzen laesst sie sich nicht, also wird sie in der englischen Mail als
    # das ausgewiesen, was sie ist.
    "moderation.originalNote": {
        "de": "",
        "en": (
            "The reason and any details below were recorded by our moderation in "
            "German."
        ),
    },

    # ---- Abgelehntes Foto ----
    "photo.subject": {
        "de": "Ein FLEXR-Profilfoto wurde abgelehnt",
        "en": "A FLEXR profile photo was rejected",
    },
    "photo.eyebrow": {"de": "Foto abgelehnt", "en": "Photo rejected"},
    "photo.intro": {
        "de": (
            "ein Profilfoto wurde nicht freigegeben und aus deinem sichtbaren Profil "
            "entfernt."
        ),
        "en": (
            "A profile photo was not approved and has been removed from your visible "
            "profile."
        ),
    },
    "photo.reasonLabel": {"de": "Begründung", "en": "Reason"},
    "photo.retry": {
        "de": (
            "Du kannst ein neues Foto hochladen. Wenn du die Entscheidung für falsch "
            "hältst, antworte bitte auf diese Mail."
        ),
        "en": (
            "You can upload a new photo. If you think the decision is wrong, please "
            "reply to this email."
        ),
    },

    # ---- Entscheidung ueber eine Meldung ----
    "report.subject": {
        "de": "Entscheidung zu deiner FLEXR-Meldung {reference}",
        "en": "Decision on your FLEXR report {reference}",
    },
    "report.eyebrow": {"de": "Meldung entschieden", "en": "Report decided"},
    "report.intro": {
        "de": "wir haben deine Meldung {reference} geprüft.",
        "en": "we have reviewed your report {reference}.",
    },
    "report.outcomeLabel": {"de": "Ergebnis", "en": "Outcome"},
    "report.reasonLabel": {"de": "Begründung", "en": "Reason"},
    "report.appeal": {
        "de": (
            "Du kannst der Entscheidung formlos per Antwort auf diese Mail "
            "widersprechen. Der Rechtsweg bleibt unbenommen."
        ),
        "en": (
            "You can object to the decision informally by replying to this email. "
            "Your right to take legal action remains unaffected."
        ),
    },

    # ---- Ruecktrittsbestaetigung (§ 13a Abs. 4 FAGG) ----
    "withdrawal.subject": {
        "de": "Bestätigung deines Rücktritts ({reference}) — FLEXR",
        "en": "Confirmation of your withdrawal ({reference}) — FLEXR",
    },
    "withdrawal.eyebrow": {"de": "Rücktritt bestätigt", "en": "Withdrawal confirmed"},
    "withdrawal.intro": {
        "de": (
            "deine Rücktrittserklärung ist bei uns eingegangen. Diese Mail ist die "
            "Bestätigung nach § 13a Abs. 4 FAGG — bewahre sie auf."
        ),
        "en": (
            "we have received your withdrawal statement. This email is the "
            "confirmation under Section 13a(4) FAGG — please keep it."
        ),
    },
    "withdrawal.kv.reference": {"de": "Aktenzeichen", "en": "Reference number"},
    "withdrawal.kv.receivedAt": {"de": "Eingegangen am", "en": "Received on"},
    "withdrawal.kv.timezone": {
        "de": "{received} (Uhrzeit in MEZ/MESZ)",
        "en": "{received} (time in CET/CEST)",
    },
    "withdrawal.kv.contract": {"de": "Vertrag/Konto", "en": "Contract/account"},
    "withdrawal.wording": {
        "de": "Wortlaut deiner Erklärung:",
        "en": "Wording of your statement, as recorded:",
    },
    "withdrawal.stopped": {
        "de": (
            "Was jetzt passiert: Ein zugeordnetes laufendes Abo ist bereits an der "
            "weiteren Verlängerung gehindert - es wird nicht erneut abgebucht. Wir "
            "prüfen die Erklärung und wickeln einen bereits bezahlten Zeitraum "
            "anteilig ab; bereits geleistete Zahlungen erstatten wir über dasselbe "
            "Zahlungsmittel, mit dem du bezahlt hast."
        ),
        "en": (
            "What happens now: a running subscription assigned to you has already "
            "been stopped from renewing - it will not be charged again. We review the "
            "statement and settle a period already paid for on a pro-rata basis; we "
            "refund payments already made using the same means of payment you paid "
            "with."
        ),
    },
    "withdrawal.pending": {
        "de": (
            "Was jetzt passiert: Wir prüfen die Erklärung, ordnen sie deinem Vertrag "
            "zu und verhindern eine weitere Verlängerung. Bereits geleistete "
            "Zahlungen erstatten wir über dasselbe Zahlungsmittel, mit dem du "
            "bezahlt hast."
        ),
        "en": (
            "What happens now: we review the statement, assign it to your contract "
            "and prevent any further renewal. We refund payments already made using "
            "the same means of payment you paid with."
        ),
    },

    # ---- Empfangsbestaetigung einer DSA-Meldung (Art. 16 Abs. 4) ----
    "notice.subject": {
        "de": "Deine Meldung an FLEXR ({reference})",
        "en": "Your report to FLEXR ({reference})",
    },
    "notice.eyebrow": {"de": "Meldung eingegangen", "en": "Report received"},
    "notice.intro": {
        "de": "deine Meldung ist bei uns eingegangen.",
        "en": "we have received your report.",
    },
    "notice.kv.reference": {"de": "Aktenzeichen", "en": "Reference number"},
    "notice.kv.receivedAt": {"de": "Eingegangen am", "en": "Received on"},
    "notice.kv.category": {"de": "Kategorie", "en": "Category"},
    "notice.review": {
        "de": (
            "Ein Mensch sieht sich die Meldung an — in der Regel binnen 72 Stunden, "
            "bei Gefahr für eine Person sofort. Du bekommst danach eine begründete "
            "Entscheidung an diese Adresse."
        ),
        "en": (
            "A human reviews the report — as a rule within 72 hours, immediately "
            "where a person is at risk. You then receive a reasoned decision at this "
            "address."
        ),
    },
    "notice.legalBasis": {
        "de": (
            "Diese Bestätigung erfolgt nach Art. 16 Abs. 4 der Verordnung (EU) "
            "2022/2065 (Gesetz über digitale Dienste). Wenn du der Entscheidung "
            "später widersprechen willst, genügt eine formlose Antwort auf diese "
            "Mail unter Angabe des Aktenzeichens."
        ),
        "en": (
            "This acknowledgement is given under Art. 16(4) of Regulation (EU) "
            "2022/2065 (Digital Services Act). If you want to object to the decision "
            "later, an informal reply to this email quoting the reference number is "
            "enough."
        ),
    },

    # ---- Antworttexte der API ----
    # Die beiden oeffentlichen Formulare zeigen diese Saetze im
    # Bestaetigungskasten an. Sie gehoeren hierher und nicht ins Frontend: Der
    # Server kennt als Einziger, ob die Bestaetigungsmail tatsaechlich
    # rausgegangen ist - und genau davon haengt ab, was der Erklaerende jetzt
    # tun muss.
    "api.notice.received": {
        "de": "Deine Meldung ist eingegangen (Aktenzeichen {reference}). {deadline} {delivery}",
        "en": "Your report has been received (reference number {reference}). {deadline} {delivery}",
    },
    "api.notice.urgent": {
        "de": "Meldungen dieser Kategorie behandeln wir vorrangig — spätestens binnen 24 Stunden.",
        "en": "We handle reports in this category as a priority — at the latest within 24 hours.",
    },
    "api.notice.normal": {
        "de": "Ein Mensch prüft die Meldung, in der Regel binnen 72 Stunden.",
        "en": "A human reviews the report, as a rule within 72 hours.",
    },
    "api.notice.delivery": {
        "de": "Die Empfangsbestätigung und später die begründete Entscheidung gehen an {email}.",
        "en": "The acknowledgement of receipt and, later, the reasoned decision go to {email}.",
    },
    "api.notice.noMail": {
        "de": (
            "Wir können dir gerade keine Bestätigungsmail schicken. Deine Meldung "
            "ist trotzdem erfasst — notiere dir bitte das Aktenzeichen {reference}. "
            "Die Entscheidung geht an {email}, sobald der Mailversand wieder läuft."
        ),
        "en": (
            "We cannot send you a confirmation email right now. Your report has been "
            "recorded all the same — please note down the reference number "
            "{reference}. The decision goes to {email} as soon as mail delivery is "
            "working again."
        ),
    },
    "api.notice.anonymous": {
        "de": (
            "Du hast keine Kontaktadresse angegeben — das ist bei dieser Kategorie "
            "zulässig (Art. 16 Abs. 3 DSA). Wir können dir dann aber keine "
            "Entscheidung zusenden. Notiere dir das Aktenzeichen."
        ),
        "en": (
            "You did not give a contact address — that is permitted for this "
            "category (Art. 16(3) DSA). We cannot send you a decision in that case. "
            "Please note down the reference number."
        ),
    },
    "api.withdrawal.received": {
        "de": "Dein Rücktritt ist erklärt (Aktenzeichen {reference}). {hint}",
        "en": "Your withdrawal has been declared (reference number {reference}). {hint}",
    },
    "api.withdrawal.confirmed": {
        "de": (
            "Die Bestätigung geht an {email}. Bewahre sie auf — sie ist dein "
            "Nachweis nach § 13a Abs. 4 FAGG."
        ),
        "en": (
            "The confirmation goes to {email}. Keep it — it is your evidence under "
            "Section 13a(4) FAGG."
        ),
    },
    "api.withdrawal.noMail": {
        "de": (
            "Wir können dir gerade keine Bestätigungsmail schicken. Deine Erklärung "
            "ist trotzdem wirksam — sie gilt mit dem Eingang, nicht mit der "
            "Bestätigung. Bitte sichere dir den unten angezeigten Wortlaut samt "
            "Aktenzeichen (Bildschirmfoto genügt) und schreib uns zur Sicherheit "
            "an flexr.social@proton.me."
        ),
        "en": (
            "We cannot send you a confirmation email right now. Your statement is "
            "effective all the same — it takes effect on receipt, not on "
            "confirmation. Please save the wording shown below together with the "
            "reference number (a screenshot is enough) and write to us at "
            "flexr.social@proton.me to be on the safe side."
        ),
    },
}


def t(key: str, lang: str = STANDARD, **vars: object) -> str:
    """Text nachschlagen und Platzhalter fuellen.

    Fehlt der englische Eintrag, kommt der deutsche - siehe Modulkopf.
    """
    eintrag = TEXTE.get(key)
    if eintrag is None:
        raise KeyError(f"Unbekannter Mailtext: {key}")
    text = eintrag.get(normalise(lang))
    if text is None:
        text = eintrag[STANDARD]
    return text.format(**vars) if vars else text
