"""Gemeinsame Bausteine für Moderationsmitteilungen (Art. 17 DSA).

Jede Beschränkung - befristete Chat-Sperre wie Kontosperre - muss dem
Betroffenen begründet mitgeteilt werden, zusammen mit dem Hinweis, wie er
dagegen vorgehen kann. Die Texte liegen hier zentral, damit Login-Fehler,
Chat-Fehler und die Mitteilung in der App dieselbe Formulierung verwenden.
"""

from typing import Optional

from .models import ModerationAction, ModerationBasis, ModerationSource, User

APPEAL_HINT = (
    "Du kannst dieser Entscheidung formlos per E-Mail an flexr.social@proton.me "
    "widersprechen. Wir prüfen sie dann erneut und antworten begründet. "
    "Der Rechtsweg bleibt dir unbenommen."
)

# Fallback, solange eine Maßnahme aus der Zeit vor der Begründungspflicht
# stammt (Bestandsdaten ohne moderation_reason).
FALLBACK_REASON = (
    "Verstoß gegen die Nutzungsrichtlinien. Die genaue Begründung erhältst du "
    "auf Anfrage unter flexr.social@proton.me."
)


#: Wie die Herkunft der Maßnahme dem Betroffenen erklärt wird (Art. 17 Abs. 3
#: lit. b DSA - "ob die Entscheidung auf einer Meldung beruht").
SOURCE_TEXT = {
    ModerationSource.user_notice: "Anlass war eine Meldung über die Meldefunktion.",
    ModerationSource.own_initiative: (
        "Anlass war keine Meldung, sondern unsere eigene Moderation."
    ),
    ModerationSource.authority: "Anlass war eine behördliche Anordnung.",
}

#: Art. 17 Abs. 3 lit. d/e: Rechtswidriger Inhalt oder Vertragsverstoß.
BASIS_TEXT = {
    ModerationBasis.illegal_content: "Grundlage ist geltendes Recht",
    ModerationBasis.terms: "Grundlage ist unsere Nutzungsrichtlinie",
}

AUTOMATED_TEXT = {
    True: (
        "An der Erkennung war ein automatisiertes Mittel beteiligt (unsere "
        "Filter für Links, Kontaktdaten und Scam-Begriffe). Die Entscheidung "
        "selbst hat ein Mensch getroffen."
    ),
    False: "Bei der Erkennung war kein automatisiertes Mittel beteiligt.",
}


def statement_of_reasons(user: User, action: ModerationAction) -> dict:
    """Begründung nach Art. 17 Abs. 3 DSA, in ihre Bestandteile zerlegt.

    Vorher bestand die Begründung aus einem einzigen Satz. Art. 17 Abs. 3
    verlangt mehr: die Maßnahme und ihren Umfang, die räumliche und zeitliche
    Reichweite, die zugrunde liegenden Tatsachen, die Angabe, ob eine Meldung
    Anlass war und ob automatisiert erkannt wurde, die konkrete Rechts- oder
    Vertragsgrundlage und den Rechtsbehelf.

    Fehlende Felder werden weggelassen statt erfunden - bei Bestandsmaßnahmen
    aus der Zeit davor bleibt es beim zusammenfassenden Satz.
    """
    aus: dict = {
        "action": action.value,
        "measure": _measure_text(user, action),
        "summary": user.moderation_reason or FALLBACK_REASON,
        "appeal_hint": APPEAL_HINT,
    }
    if user.moderation_action_at:
        aus["decided_at"] = user.moderation_action_at.isoformat()
    if user.moderation_scope:
        aus["scope"] = user.moderation_scope
    if action is ModerationAction.mute and user.messaging_muted_until:
        aus["duration"] = (
            f"befristet bis {user.messaging_muted_until.strftime('%d.%m.%Y, %H:%M')} Uhr"
        )
    elif action is ModerationAction.ban:
        aus["duration"] = "unbefristet, bis die Entscheidung aufgehoben wird"
    if user.moderation_facts:
        aus["facts"] = user.moderation_facts
    if user.moderation_source:
        try:
            aus["source"] = SOURCE_TEXT[ModerationSource(user.moderation_source)]
        except ValueError:
            pass
    aus["automated_detection"] = AUTOMATED_TEXT[bool(user.moderation_automated)]
    if user.moderation_basis:
        try:
            grundlage = BASIS_TEXT[ModerationBasis(user.moderation_basis)]
        except ValueError:
            grundlage = None
        if grundlage:
            if user.moderation_basis_detail:
                grundlage = f"{grundlage}: {user.moderation_basis_detail}"
            aus["legal_basis"] = grundlage
    return aus


def _measure_text(user: User, action: ModerationAction) -> str:
    if action is ModerationAction.mute:
        return "Beschränkung: Du kannst vorübergehend keine Nachrichten senden."
    return "Beschränkung: Dein Konto ist gesperrt."


def restriction_detail(user: User, action: ModerationAction) -> dict:
    """Fehler-Detail für HTTP 403, das die App als begründete Mitteilung
    anzeigen kann.

    Die alten Schlüssel bleiben unverändert - die ausgelieferten Android- und
    iOS-Fassungen lesen sie. ``statement`` kommt als zusätzliches Feld dazu;
    ältere Clients ignorieren es, neue können die vollständige Begründung nach
    Art. 17 DSA anzeigen.
    """
    detail = {
        "reason": "messaging_muted" if action is ModerationAction.mute else "account_banned",
        "moderation_action": action.value,
        "moderation_reason": user.moderation_reason or FALLBACK_REASON,
        "appeal_hint": APPEAL_HINT,
        "message": _message_for(user, action),
        "statement": statement_of_reasons(user, action),
    }
    if action is ModerationAction.mute and user.messaging_muted_until:
        detail["muted_until"] = user.messaging_muted_until.isoformat()
    if user.moderation_action_at:
        detail["moderation_action_at"] = user.moderation_action_at.isoformat()
    return detail


def _message_for(user: User, action: ModerationAction) -> str:
    if action is ModerationAction.mute:
        return (
            "Deine Chat-Sperre ist noch aktiv - du kannst derzeit keine "
            "Nachrichten senden."
        )
    return "Dein Konto wurde gesperrt."


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
