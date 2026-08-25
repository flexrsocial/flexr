from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .. import telegram
from ..database import get_db
from ..models import Block, Match, Message, ModerationAction, User
from ..moderation import restriction_detail
from ..rate_limit import limiter
from ..schemas import MessageOut, SendMessageRequest
from ..security import require_active_membership

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

    unread = [m for m in messages if m.sender_id == other_id and m.read_at is None]
    if unread:
        now = datetime.utcnow()
        for m in unread:
            m.read_at = now
        db.commit()

    return [_message_out(m, current_user.id) for m in messages]


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
    match.set_cleared_at(current_user.id, datetime.utcnow())
    db.commit()
    return None


@router.post("/{match_id}/messages", response_model=MessageOut, status_code=201)
@limiter.limit("30/minute")
def send_message(
    request: Request,
    match_id: str,
    payload: SendMessageRequest,
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
    # Der Absender bekommt sein Original zurück, plus den Zensur-Hinweis
    return _message_out(message, current_user.id)
