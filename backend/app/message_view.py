"""Betrachterabhängige Ausgabe einer Chat-Nachricht.

Eigenes Modul, damit sowohl der Chat (routers/messages.py) als auch die
Match-Liste (routers/matches.py, Feld last_message) dieselbe Logik nutzen,
ohne dass sich die beiden Router gegenseitig importieren müssen.
"""

from .models import Message
from .schemas import MessageOut


def message_out(m: Message, viewer_id: str) -> MessageOut:
    """Baut die Nachrichten-Ausgabe je nach Betrachter: der Absender (und Admin)
    sieht sein Original, der Empfänger die zensierte Fassung."""
    if m.sender_id == viewer_id:
        shown = m.content
    else:
        shown = m.display_content if m.display_content is not None else m.content
    return MessageOut(
        id=m.id,
        match_id=m.match_id,
        sender_id=m.sender_id,
        content=shown,
        created_at=m.created_at,
        read_at=m.read_at,
        was_censored=m.was_censored,
    )
