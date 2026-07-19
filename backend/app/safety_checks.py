"""Automatische Sicherheitsprüfungen für Inhalte (nach Tinder-Vorbild).

Drei Bausteine:
- Wegwerf-E-Mail-Blocklist bei der Registrierung
- Bio-/Profiltext-Prüfung (öffentliche Texte): blockiert URLs, Telefonnummern
  und bekannte Scam-Begriffe hart (400)
- Nachrichten-Scanner: markiert auffällige Chat-Nachrichten fürs Admin-Review,
  stellt sie aber zu (kein Auto-Block wegen False Positives)
"""

import re
from typing import Optional

# Gängige Wegwerf-E-Mail-Domains (bewusst kompakt gehalten)
DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com", "10minutemail.com", "10minutemail.de", "tempmail.com",
    "temp-mail.org", "guerrillamail.com", "guerrillamail.de", "sharklasers.com",
    "yopmail.com", "trashmail.com", "trashmail.de", "wegwerfemail.de",
    "wegwerf-email.de", "einrollen.de", "byom.de", "dispostable.com",
    "getnada.com", "maildrop.cc", "mintemail.com", "throwawaymail.com",
    "mail-temporaire.fr", "spamgourmet.com", "mytemp.email", "fakemail.net",
}

_URL_RE = re.compile(
    r"(https?://|www\.|\b[\w-]+\.(?:com|net|org|io|me|de|at|ch|info|xyz|club|online)(?:/|\b))",
    re.IGNORECASE,
)
# Telefonnummern in öffentlichen Profiltexten (mind. 9 zusammenhängende Ziffern
# mit üblichen Trennzeichen)
_PHONE_RE = re.compile(r"\+?\d[\d\s\-/().]{7,}\d")

_SCAM_TERMS = [
    "western union", "moneygram", "bitcoin", "btc kaufen", "crypto invest",
    "krypto invest", "onlyfans", "of-account", "sugar daddy", "sugardaddy",
    "sugar baby", "cashapp", "paysafecard", "geld verdienen", "schnelles geld",
    "investier", "trading-gruppe", "broker",
]


def is_disposable_email(email: str) -> bool:
    domain = email.rsplit("@", 1)[-1].lower()
    return domain in DISPOSABLE_EMAIL_DOMAINS


def check_public_text(text: Optional[str]) -> Optional[str]:
    """Prüft öffentliche Profiltexte (Bio). Liefert eine Begründung, wenn der
    Text nicht erlaubt ist, sonst None."""
    if not text:
        return None
    lowered = text.lower()
    if _URL_RE.search(text):
        return "Links sind in der Bio nicht erlaubt."
    if _PHONE_RE.search(text):
        return "Telefonnummern sind in der Bio nicht erlaubt."
    for term in _SCAM_TERMS:
        if term in lowered:
            return "Dieser Inhalt ist in der Bio nicht erlaubt."
    return None


def scan_message(text: str) -> Optional[str]:
    """Prüft Chat-Nachrichten. Liefert einen Flag-Grund für auffällige Inhalte
    (Scam-Begriffe, Links), sonst None. Telefonnummern sind im Chat bewusst
    erlaubt - Kontaktaustausch ist dort normal."""
    lowered = text.lower()
    for term in _SCAM_TERMS:
        if term in lowered:
            return f"Scam-Verdacht: '{term}'"
    if _URL_RE.search(text):
        return "Enthält Link"
    return None
