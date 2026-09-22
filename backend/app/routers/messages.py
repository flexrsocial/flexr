import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .. import premium, push, telegram
from ..database import get_db
from ..models import Block, Match, Message, ModerationAction, User
from ..moderation import restriction_detail
from ..rate_limit import limiter
from ..schemas import MessageOut, SendMessageRequest
from ..security import require_active_membership
from ..timeutil import utcnow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/matches", tags=["messages"])


def _get_match_and_other_id(match_id: str, current_user: User, db: Session) -> tuple[Match, str]:
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match or current_user.id not in (match.user_a_id, match.user_b_id):
        raise HTTPException(404, "Match nicht gefunden.")

    other_id = match.user_b_id if match.user_a_id == current_user.id else match.user_a_id

    blocked = (
        db.query(Block)
        .filter(
            or_(
                and_(Block.blocker_id == current_user.id, Block.blocked_id == other_id),
                and_(Block.blocker_id == other_id, Block.blocked_id == current_user.id),
            )
        )
        .first()
    )
    if blocked:
        raise HTTPException(403, "Chat nicht verfügbar.")

    return match, other_id


def _message_out(m: Message, viewer_id: str) -> MessageOut:
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


# Wie lang der Text in der Benachrichtigung höchstens wird. Auf einem
# gesperrten Bildschirm ist alles darüber ohnehin abgeschnitten, und FCM
# begrenzt die Nutzlast - lieber hier sauber kürzen als dort hart abschneiden.
NOTIFICATION_PREVIEW_CHARS = 120


def _benachrichtigungstext(m: Message, empfaenger_id: str) -> str:
    """Der Text, der in der Push-Benachrichtigung steht.

    Bewusst die **zensierte** Fassung: Sie landet auf einem gesperrten
    Bildschirm, und was der Empfänger in der App nicht zu sehen bekäme (Links,
    Kontaktdaten - siehe safety_checks.redact_message), hat dort erst recht
    nichts verloren.
    """
    text = _message_out(m, empfaenger_id).content
    if len(text) <= NOTIFICATION_PREVIEW_CHARS:
        return text
    return text[: NOTIFICATION_PREVIEW_CHARS - 1].rstrip() + "…"


@router.get("/{match_id}/messages", response_model=list[MessageOut])
def list_messages(
    match_id: str,
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    match, other_id = _get_match_and_other_id(match_id, current_user, db)

    query = db.query(Message).filter(Message.match_id == match_id)
    # Eigener "Chatverlauf leeren"-Zeitpunkt blendet ältere Nachrichten aus
    cleared_at = match.cleared_at_for(current_user.id)
    if cleared_at is not None:
        query = query.filter(Message.created_at > cleared_at)
    messages = query.order_by(Message.created_at.asc()).all()

    now = utcnow()
    unread_ids = {m.id for m in messages if m.sender_id == other_id and m.read_at is None}

    # Die Antwort wird vor dem Commit gebaut (und read_at für die eben als
    # gelesen markierten hier direkt am Ausgabeobjekt gesetzt, nicht am
    # ORM-Objekt): expire_on_commit räumt nach einem commit() sonst den
    # Attribut-Cache aller Objekte in der Session leer, und jeder folgende
    # Attributzugriff (hier: für jede einzelne Nachricht) löst eine eigene
    # Nachlade-Abfrage aus.
    result = []
    for m in messages:
        out = _message_out(m, current_user.id)
        if m.id in unread_ids:
            out.read_at = now
        result.append(out)

    if unread_ids:
        # Ein UPDATE für alle betroffenen Zeilen statt eines pro Nachricht
        # (SQLAlchemys Unit-of-Work würde bei N einzeln geänderten ORM-
        # Objekten N einzelne UPDATE-Statements ausführen).
        db.query(Message).filter(Message.id.in_(unread_ids)).update(
            {Message.read_at: now}, synchronize_session=False
        )
        db.commit()

    return result


@router.delete("/{match_id}/messages", status_code=204)
def clear_messages(
    match_id: str,
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    """Chatverlauf leeren - nur für die leerende Seite: der bisherige Verlauf
    wird für diesen Nutzer ausgeblendet, für die andere Seite bleibt er
    erhalten. Nachrichten werden nicht gelöscht, nur ein 'geleert-ab'-Zeitpunkt
    gesetzt."""
    match, _ = _get_match_and_other_id(match_id, current_user, db)
    match.set_cleared_at(current_user.id, utcnow())
    db.commit()
    return None


@router.post("/{match_id}/messages", response_model=MessageOut, status_code=201)
@limiter.limit("30/minute")
def send_message(
    request: Request,
    match_id: str,
    payload: SendMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    _, other_id = _get_match_and_other_id(match_id, current_user, db)

    # Empfänger darf kein gesperrtes oder gelöschtes Konto sein - solche Konten
    # verschwinden aus der Match-Liste, ein direkter Sendeversuch (z. B. mit
    # veralteter match_id) läuft sonst ins Leere.
    other = db.query(User).filter(User.id == other_id).first()
    if other is None or other.is_banned or other.deleted_at is not None:
        raise HTTPException(404, "Chat nicht verfügbar.")

    # Befristete Chat-Sperre ("Abmahnung"): Senden ist bis zum Ablauf gesperrt.
    # Das Detail trägt Begründung und Widerspruchshinweis (Art. 17 DSA).
    if current_user.is_messaging_muted:
        raise HTTPException(
            403,
            restriction_detail(current_user, ModerationAction.mute),
        )

    # Wie viele Unterhaltungen ein Standardkonto gleichzeitig fuehren darf.
    # Greift nur beim **ersten** eigenen Satz in diesem Chat - siehe
    # premium.ensure_chat_allowed(). Bewusst nach der Moderationspruefung: Eine
    # laufende Chatsperre ist der gewichtigere Grund und soll auch dann als
    # solcher gemeldet werden, wenn zusaetzlich das Kontingent voll ist.
    premium.ensure_chat_allowed(db, current_user, match_id, request)

    # Automatische Sicherheitsprüfung: auffällige Nachrichten werden zugestellt,
    # aber fürs Admin-Review markiert. Zusätzlich werden Links/Kontaktdaten für
    # den Empfänger zensiert (Scam-/Phishing-Schutz).
    from ..safety_checks import redact_message, scan_message

    flag_reason = scan_message(payload.content)
    display_content, was_censored = redact_message(payload.content)

    message = Message(
        match_id=match_id,
        sender_id=current_user.id,
        content=payload.content,
        display_content=display_content,
        was_censored=was_censored,
        is_flagged=flag_reason is not None,
        flag_reason=flag_reason,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    if message.is_flagged:
        telegram.notify_admin_task(
            f"🆕 Nachricht markiert im FLEXR-Admin-Dashboard: Grund {flag_reason}"
        )

    # Echte Push-Zustellung an den Empfänger.
    #
    # Der entscheidende Teil an der Behebung des gemeldeten Fehlers: Bis hierher
    # erfuhr der Empfänger von einer Nachricht erst, wenn seine App von sich aus
    # nachfragte - frühestens nach 15 Minuten, im Doze-Modus nach ein bis zwei
    # Stunden, nach einem erzwungenen Beenden gar nicht mehr. Jetzt schickt der
    # Server, und das Gerät wacht dafür auf.
    #
    # Als BackgroundTask statt eines direkten Aufrufs: push.send() macht
    # Netzwerkaufrufe an FCM/APNs (bis zu mehrere Sekunden, siehe app/push.py)
    # - ohne das hier wuerde jede Chatnachricht auf diese Zustellung warten,
    # bevor der Absender ueberhaupt sein 201 sieht. send_async() oeffnet dafuer
    # eine eigene, kurzlebige Session (siehe deren Docstring): die Request-
    # Session ist zu diesem Zeitpunkt schon geschlossen.
    #
    # ``push.send_async()`` wirft nie und ist ohne Zugangsdaten ein No-op: Eine
    # Nachricht muss auch dann ankommen, wenn Push nicht eingerichtet ist oder
    # Google gerade nicht erreichbar - der Hintergrundabgleich der Apps liefert
    # sie dann wie bisher nach. Festgehalten in
    # test_nachricht_kommt_auch_ohne_push_an.
    #
    # Der zensierte Text, nicht das Original: Was in der Benachrichtigung steht,
    # steht auf einem gesperrten Bildschirm - dort hat ungefiltertes Zeug nichts
    # verloren, das der Empfänger in der App gar nicht zu sehen bekäme. Wird
    # hier, nicht im Hintergrund-Task, aus der noch lebenden Session gelesen.
    background_tasks.add_task(
        push.send_async,
        other.id,
        current_user.name,
        _benachrichtigungstext(message, other.id),
        "chats",
    )

    # Der Absender bekommt sein Original zurück, plus den Zensur-Hinweis
    return _message_out(message, current_user.id)
