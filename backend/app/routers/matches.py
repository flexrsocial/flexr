from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, aliased, selectinload

from ..database import get_db
from ..models import Block, Match, Message, Swipe, User
from ..schemas import MatchOut
from ..security import require_active_membership
from .profiles import to_public_profile
from ..timeutil import utcnow

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("", response_model=list[MatchOut])
def get_matches(
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Match)
        .filter(or_(Match.user_a_id == current_user.id, Match.user_b_id == current_user.id))
        .all()
    )
    if not rows:
        return []

    other_ids = [
        row.user_b_id if row.user_a_id == current_user.id else row.user_a_id for row in rows
    ]
    # Blockierungen wirken in beide Richtungen: ein Match verschwindet aus der
    # Liste, sobald eine Seite die andere blockiert hat.
    blocked_ids = {
        b.blocked_id for b in db.query(Block).filter(Block.blocker_id == current_user.id)
    } | {
        b.blocker_id for b in db.query(Block).filter(Block.blocked_id == current_user.id)
    }

    users_by_id = {
        u.id: u
        for u in db.query(User)
        .options(selectinload(User.photos))
        .filter(
            User.id.in_(other_ids),
            User.deleted_at.is_(None),
            User.is_banned.is_(False),
        )
        .all()
    }

    visible_rows = [
        row
        for row in rows
        if (row.user_b_id if row.user_a_id == current_user.id else row.user_a_id) not in blocked_ids
        and (row.user_b_id if row.user_a_id == current_user.id else row.user_a_id) in users_by_id
    ]

    # Drei Werte pro Match (last_message, unread_count, in_chats), aber je
    # Match ein eigener Ausschnitt-Zeitpunkt ("Chatverlauf leeren" bzw. "Chat
    # löschen" - beide je Nutzerseite in der Match-Zeile gespeichert, siehe
    # Match.cleared_at_for/chat_deleted_at_for). Statt das dreimal pro Match
    # einzeln abzufragen (3×N Round-Trips, auf dem "Matches"-Bildschirm bei
    # jedem App-Start), werden die Zeitpunkte hier vorab gelesen und die
    # Bedingungen für alle Matches zu je einer einzigen Abfrage
    # zusammengefasst (via OR verknüpft - inhaltlich identisch zu den
    # vorherigen Einzelabfragen, nur als eine Abfrage statt N).
    cleared_at_by_match = {row.id: row.cleared_at_for(current_user.id) for row in visible_rows}
    chat_deleted_by_match = {row.id: row.chat_deleted_at_for(current_user.id) for row in visible_rows}

    def _cutoff_condition(match_id: str, cutoff):
        cond = Message.match_id == match_id
        return cond if cutoff is None else and_(cond, Message.created_at > cutoff)

    last_message_by_match: dict[str, Message] = {}
    unread_count_by_match: dict[str, int] = {}
    in_chats_ids: set[str] = set()

    if visible_rows:
        rn = (
            func.row_number()
            .over(partition_by=Message.match_id, order_by=Message.created_at.desc())
            .label("rn")
        )
        ranked = (
            db.query(Message, rn)
            .filter(or_(*(_cutoff_condition(mid, cutoff) for mid, cutoff in cleared_at_by_match.items())))
            .subquery()
        )
        ranked_message = aliased(Message, ranked)
        last_message_by_match = {
            m.match_id: m
            for m in db.query(ranked_message).filter(ranked.c.rn == 1).all()
        }

        unread_count_by_match = dict(
            db.query(Message.match_id, func.count(Message.id))
            .filter(
                or_(
                    and_(
                        _cutoff_condition(mid, cleared_at_by_match[mid]),
                        Message.sender_id != current_user.id,
                        Message.read_at.is_(None),
                    )
                    for mid in cleared_at_by_match
                )
            )
            .group_by(Message.match_id)
            .all()
        )

        # "Chats"-Zugehörigkeit unabhängig von last_message/cleared_at: nach
        # "Chatverlauf leeren" bleibt der Chat sichtbar (nur eben ohne
        # last_message), nach "Chat löschen" verschwindet er, bis danach eine
        # neue Nachricht eintrifft (chat_deleted_at gilt nur bis dahin).
        in_chats_ids = {
            match_id
            for (match_id,) in db.query(Message.match_id.distinct())
            .filter(or_(*(_cutoff_condition(mid, cutoff) for mid, cutoff in chat_deleted_by_match.items())))
            .all()
        }

    result = []
    for row in visible_rows:
        other_id = row.user_b_id if row.user_a_id == current_user.id else row.user_a_id
        result.append(
            (
                row.created_at,
                MatchOut(
                    match_id=row.id,
                    profile=to_public_profile(users_by_id[other_id]),
                    last_message=last_message_by_match.get(row.id),
                    unread_count=unread_count_by_match.get(row.id, 0),
                    is_online=users_by_id[other_id].is_online,
                    in_chats=row.id in in_chats_ids,
                ),
            )
        )

    result.sort(
        key=lambda pair: pair[1].last_message.created_at if pair[1].last_message else pair[0],
        reverse=True,
    )
    return [match_out for _, match_out in result]


@router.delete("/{match_id}")
def unmatch(
    match_id: str,
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    """Match auflösen: Match und Chatverlauf werden gelöscht. Der eigene Swipe
    wird ebenfalls entfernt, damit die Person noch einmal ganz normal im Deck
    erscheint und bewusst weggewischt werden kann. Eine Sperre wie beim
    Blockieren ist das ausdrücklich nicht."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match or current_user.id not in (match.user_a_id, match.user_b_id):
        raise HTTPException(404, "Match nicht gefunden.")

    other_id = match.user_b_id if match.user_a_id == current_user.id else match.user_a_id

    db.query(Message).filter(Message.match_id == match_id).delete()
    db.query(Swipe).filter(
        Swipe.from_user_id == current_user.id, Swipe.to_user_id == other_id
    ).delete()
    db.delete(match)
    db.commit()
    return {"unmatched": True}


@router.delete("/{match_id}/chat")
def delete_chat(
    match_id: str,
    current_user: User = Depends(require_active_membership),
    db: Session = Depends(get_db),
):
    """"Chat löschen": anders als ``unmatch`` bleiben Match, Swipe und die
    Nachrichten selbst bestehen - nur für die löschende Seite verschwindet die
    Unterhaltung aus der Chats-Übersicht (siehe ``in_chats`` in
    ``get_matches``), bis erneut eine Nachricht geschrieben wird. Für die
    andere Seite ändert sich nichts."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match or current_user.id not in (match.user_a_id, match.user_b_id):
        raise HTTPException(404, "Match nicht gefunden.")

    jetzt = utcnow()
    match.set_chat_deleted_at(current_user.id, jetzt)
    # Wie bei "Chatverlauf leeren": die alten Nachrichten sollen nicht wieder
    # auftauchen, sobald der Chat durch eine neue Nachricht zurückkehrt.
    match.set_cleared_at(current_user.id, jetzt)
    db.commit()
    return {"chat_deleted": True}
