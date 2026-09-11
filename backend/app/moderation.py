"""Gemeinsame Bausteine für Moderationsmitteilungen (Art. 17 DSA).

Jede Beschränkung - befristete Chat-Sperre wie Kontosperre - muss dem
Betroffenen begründet mitgeteilt werden, zusammen mit dem Hinweis, wie er
dagegen vorgehen kann. Die Texte liegen hier zentral, damit Login-Fehler,
Chat-Fehler und die Mitteilung in der App dieselbe Formulierung verwenden.
"""

from typing import Optional

from .models import ModerationAction, ModerationBasis, ModerationSource, User

# Alle Bausteine hier gibt es zweisprachig: Sie gehen per E-Mail an den
# Betroffenen (mailer.send_moderation_decision) und stehen im 403-Detail, das
# die Apps anzeigen - beides folgt der Profilsprache. Nicht uebersetzt wird
# der Freitext des Moderators (``moderation_reason``, ``moderation_facts``);
# den schreibt ein Mensch, und die englische Mail weist ihn als deutsch aus.
_APPEAL_HINT = {
    "de": (
        "Du kannst dieser Entscheidung formlos per E-Mail an flexr.social@proton.me "
        "widersprechen. Wir prüfen sie dann erneut und antworten begründet. "
        "Der Rechtsweg bleibt dir unbenommen."
    ),
    "en": (
        "You can object to this decision informally by email to "
        "flexr.social@proton.me. We then review it again and respond with reasons. "
        "Your right to take legal action remains unaffected."
    ),
}

# Fallback, solange eine Maßnahme aus der Zeit vor der Begründungspflicht
# stammt (Bestandsdaten ohne moderation_reason).
_FALLBACK_REASON = {
    "de": (
        "Verstoß gegen die Nutzungsrichtlinien. Die genaue Begründung erhältst du "
        "auf Anfrage unter flexr.social@proton.me."
    ),
    "en": (
        "Breach of the community guidelines. You can obtain the precise reasons on "
        "request at flexr.social@proton.me."
    ),
}


#: Wie die Herkunft der Maßnahme dem Betroffenen erklärt wird (Art. 17 Abs. 3
#: lit. b DSA - "ob die Entscheidung auf einer Meldung beruht").
SOURCE_TEXT = {
    ModerationSource.user_notice: {
        "de": "Anlass war eine Meldung über die Meldefunktion.",
        "en": "This was prompted by a report via the reporting function.",
    },
    ModerationSource.own_initiative: {
        "de": "Anlass war keine Meldung, sondern unsere eigene Moderation.",
        "en": "This was not prompted by a report but by our own moderation.",
    },
    ModerationSource.authority: {
        "de": "Anlass war eine behördliche Anordnung.",
        "en": "This was prompted by an order from an authority.",
    },
}

#: Art. 17 Abs. 3 lit. d/e: Rechtswidriger Inhalt oder Vertragsverstoß.
BASIS_TEXT = {
    ModerationBasis.illegal_content: {
        "de": "Grundlage ist geltendes Recht",
        "en": "The basis is applicable law",
    },
    ModerationBasis.terms: {
        "de": "Grundlage ist unsere Nutzungsrichtlinie",
        "en": "The basis is our community guidelines",
    },
}

AUTOMATED_TEXT = {
    True: {
        "de": (
            "An der Erkennung war ein automatisiertes Mittel beteiligt (unsere "
            "Filter für Links, Kontaktdaten und Scam-Begriffe). Die Entscheidung "
            "selbst hat ein Mensch getroffen."
        ),
        "en": (
            "An automated means was involved in the detection (our filters for "
            "links, contact details and scam terms). The decision itself was taken "
            "by a human."
        ),
    },
    False: {
        "de": "Bei der Erkennung war kein automatisiertes Mittel beteiligt.",
        "en": "No automated means was involved in the detection.",
    },
}

_MEASURE_TEXT = {
    ModerationAction.mute: {
        "de": "Beschränkung: Du kannst vorübergehend keine Nachrichten senden.",
        "en": "Restriction: you cannot send messages for the time being.",
    },
    None: {
        "de": "Beschränkung: Dein Konto ist gesperrt.",
        "en": "Restriction: your account is blocked.",
    },
}

_DURATION_TEXT = {
    "mute": {"de": "befristet bis {until} Uhr", "en": "limited until {until}"},
    "ban": {
        "de": "unbefristet, bis die Entscheidung aufgehoben wird",
        "en": "indefinite, until the decision is lifted",
    },
}


def _lang(value: str | None) -> str:
    from .message_texts import normalise

    return normalise(value)


#: Bleiben als Modulkonstanten erhalten - Tests und aeltere Aufrufer lesen sie
#: in der Ausgangssprache.
APPEAL_HINT = _APPEAL_HINT["de"]
FALLBACK_REASON = _FALLBACK_REASON["de"]


def appeal_hint(lang: str | None = "de") -> str:
    return _APPEAL_HINT[_lang(lang)]


def fallback_reason(lang: str | None = "de") -> str:
    return _FALLBACK_REASON[_lang(lang)]


def statement_of_reasons(
    user: User, action: ModerationAction, lang: str | None = None
) -> dict:
    """Begründung nach Art. 17 Abs. 3 DSA, in ihre Bestandteile zerlegt.

    Vorher bestand die Begründung aus einem einzigen Satz. Art. 17 Abs. 3
    verlangt mehr: die Maßnahme und ihren Umfang, die räumliche und zeitliche
    Reichweite, die zugrunde liegenden Tatsachen, die Angabe, ob eine Meldung
    Anlass war und ob automatisiert erkannt wurde, die konkrete Rechts- oder
    Vertragsgrundlage und den Rechtsbehelf.

    Fehlende Felder werden weggelassen statt erfunden - bei Bestandsmaßnahmen
    aus der Zeit davor bleibt es beim zusammenfassenden Satz.

    ``lang`` steuert nur die festen Bausteine. Der Freitext des Moderators
    (``moderation_reason``, ``moderation_facts``, ``moderation_basis_detail``)
    bleibt so stehen, wie er geschrieben wurde - ihn zu übersetzen hieße, eine
    Begründung zu erfinden. Ohne Angabe gilt die Profilsprache.
    """
    sprache = _lang(lang if lang is not None else user.language)
    aus: dict = {
        "action": action.value,
        "measure": _measure_text(user, action, sprache),
        "summary": user.moderation_reason or fallback_reason(sprache),
        "appeal_hint": appeal_hint(sprache),
    }
    if user.moderation_action_at:
        aus["decided_at"] = user.moderation_action_at.isoformat()
    if user.moderation_scope:
        aus["scope"] = user.moderation_scope
    if action is ModerationAction.mute and user.messaging_muted_until:
        aus["duration"] = _DURATION_TEXT["mute"][sprache].format(
            until=user.messaging_muted_until.strftime("%d.%m.%Y, %H:%M")
        )
    elif action is ModerationAction.ban:
        aus["duration"] = _DURATION_TEXT["ban"][sprache]
    if user.moderation_facts:
        aus["facts"] = user.moderation_facts
    if user.moderation_source:
        try:
            aus["source"] = SOURCE_TEXT[ModerationSource(user.moderation_source)][sprache]
        except ValueError:
            pass
    aus["automated_detection"] = AUTOMATED_TEXT[bool(user.moderation_automated)][sprache]
    if user.moderation_basis:
        try:
            grundlage = BASIS_TEXT[ModerationBasis(user.moderation_basis)][sprache]
        except ValueError:
            grundlage = None
        if grundlage:
            if user.moderation_basis_detail:
                grundlage = f"{grundlage}: {user.moderation_basis_detail}"
            aus["legal_basis"] = grundlage
    return aus


def _measure_text(user: User, action: ModerationAction, lang: str = "de") -> str:
    schluessel = ModerationAction.mute if action is ModerationAction.mute else None
    return _MEASURE_TEXT[schluessel][lang]


def restriction_detail(user: User, action: ModerationAction) -> dict:
    """Fehler-Detail für HTTP 403, das die App als begründete Mitteilung
    anzeigen kann.

    Die alten Schlüssel bleiben unverändert - die ausgelieferten Android- und
    iOS-Fassungen lesen sie. ``statement`` kommt als zusätzliches Feld dazu;
    ältere Clients ignorieren es, neue können die vollständige Begründung nach
    Art. 17 DSA anzeigen.
    """
    sprache = _lang(user.language)
    detail = {
        "reason": "messaging_muted" if action is ModerationAction.mute else "account_banned",
        "moderation_action": action.value,
        "moderation_reason": user.moderation_reason or fallback_reason(sprache),
        "appeal_hint": appeal_hint(sprache),
        "message": _message_for(user, action, sprache),
        "statement": statement_of_reasons(user, action, sprache),
    }
    if action is ModerationAction.mute and user.messaging_muted_until:
        detail["muted_until"] = user.messaging_muted_until.isoformat()
    if user.moderation_action_at:
        detail["moderation_action_at"] = user.moderation_action_at.isoformat()
    return detail


_MESSAGE_TEXT = {
    "mute": {
        "de": (
            "Deine Chat-Sperre ist noch aktiv - du kannst derzeit keine "
            "Nachrichten senden."
        ),
        "en": (
            "Your chat suspension is still active - you cannot send messages at "
            "the moment."
        ),
    },
    "ban": {
        "de": "Dein Konto wurde gesperrt.",
        "en": "Your account has been blocked.",
    },
}


def _message_for(user: User, action: ModerationAction, lang: str = "de") -> str:
    schluessel = "mute" if action is ModerationAction.mute else "ban"
    return _MESSAGE_TEXT[schluessel][lang]


def apply_restriction(
    user: User,
    action: ModerationAction,
    reason: str,
    muted_until: Optional["object"] = None,
    *,
    scope: Optional[str] = None,
    facts: Optional[str] = None,
    source: Optional[ModerationSource] = None,
    automated: bool = False,
    basis: Optional[ModerationBasis] = None,
    basis_detail: Optional[str] = None,
) -> None:
    """Setzt Maßnahme samt Begründung. Ohne Begründung keine Beschränkung.

    Die zusätzlichen Angaben sind optional, damit bestehende Aufrufe
    unverändert funktionieren - vollständig im Sinne des Art. 17 Abs. 3 DSA ist
    die Begründung aber erst mit ihnen. Wo sie fehlen, lässt
    ``statement_of_reasons`` den jeweiligen Punkt weg, statt etwas zu behaupten.
    """
    user.moderation_action = action.value
    user.moderation_reason = reason
    from datetime import datetime

    user.moderation_action_at = datetime.utcnow()
    user.moderation_scope = scope or (
        "Senden von Nachrichten" if action is ModerationAction.mute else "gesamtes Konto"
    )
    user.moderation_facts = facts
    user.moderation_source = source.value if source else None
    user.moderation_automated = automated
    user.moderation_basis = basis.value if basis else None
    user.moderation_basis_detail = basis_detail
    if action is ModerationAction.mute:
        user.messaging_muted_until = muted_until
    else:
        user.is_banned = True


def clear_restriction(user: User, action: ModerationAction) -> None:
    """Hebt eine Maßnahme auf und räumt die Begründung mit weg."""
    if action is ModerationAction.mute:
        user.messaging_muted_until = None
    else:
        user.is_banned = False
    if user.moderation_action == action.value:
        user.moderation_action = None
        user.moderation_reason = None
        user.moderation_action_at = None
        user.moderation_scope = None
        user.moderation_facts = None
        user.moderation_source = None
        user.moderation_automated = False
        user.moderation_basis = None
        user.moderation_basis_detail = None
