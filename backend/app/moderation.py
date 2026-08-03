"""Gemeinsame Bausteine für Moderationsmitteilungen (Art. 17 DSA).

Jede Beschränkung - befristete Chat-Sperre wie Kontosperre - muss dem
Betroffenen begründet mitgeteilt werden, zusammen mit dem Hinweis, wie er
dagegen vorgehen kann. Die Texte liegen hier zentral, damit Login-Fehler,
Chat-Fehler und die Mitteilung in der App dieselbe Formulierung verwenden.
"""

from typing import Optional

from .models import ModerationAction, User

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


def restriction_detail(user: User, action: ModerationAction) -> dict:
    """Fehler-Detail für HTTP 403, das die App als begründete Mitteilung
    anzeigen kann."""
    detail = {
        "reason": "messaging_muted" if action is ModerationAction.mute else "account_banned",
        "moderation_action": action.value,
        "moderation_reason": user.moderation_reason or FALLBACK_REASON,
        "appeal_hint": APPEAL_HINT,
        "message": _message_for(user, action),
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
) -> None:
    """Setzt Maßnahme samt Begründung. Ohne Begründung keine Beschränkung."""
    user.moderation_action = action.value
    user.moderation_reason = reason
    from datetime import datetime

    user.moderation_action_at = datetime.utcnow()
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
