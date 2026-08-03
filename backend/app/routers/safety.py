from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Block, ModerationAction, PhotoStatus, Report, User
from ..moderation import APPEAL_HINT
from ..rate_limit import limiter
from ..schemas import (
    BlockedProfileOut,
    BlockRequest,
    ModerationNotice,
    MyReportOut,
    ReportAck,
    ReportRequest,
)
from ..security import get_current_user

router = APIRouter(prefix="/api", tags=["safety"])


@router.post("/reports", status_code=201, response_model=ReportAck)
@limiter.limit("20/minute")
def create_report(
    request: Request,
    payload: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.reported_user_id == current_user.id:
        raise HTTPException(400, "Du kannst dich nicht selbst melden.")

    reported_user = db.query(User).filter(User.id == payload.reported_user_id).first()
    if not reported_user:
        raise HTTPException(404, "Nutzer nicht gefunden.")

    report = Report(
        reporter_id=current_user.id,
        reported_id=payload.reported_user_id,
        reason=payload.reason,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Art. 16 Abs. 4 DSA: unverzügliche Empfangsbestätigung mit Aktenzeichen.
    return ReportAck(
        reference=report.reference,
        created_at=report.created_at,
        message=(
            f"Deine Meldung ist eingegangen (Aktenzeichen {report.reference}). "
            "Wir prüfen sie innerhalb von 72 Stunden — bei Gefahr für eine Person "
            "sofort. Das Ergebnis findest du danach unter „Meine Meldungen“ im "
            "Konto-Bereich."
        ),
    )


@router.get("/reports/mine", response_model=list[MyReportOut])
def list_my_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Art. 16 Abs. 5 DSA: Der Melder muss die Entscheidung über seine Meldung
    erfahren — hier holt die App sie ab."""
    rows = (
        db.query(Report)
        .filter(Report.reporter_id == current_user.id)
        .order_by(Report.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        MyReportOut(
            reference=report.reference,
            reason=report.reason,
            created_at=report.created_at,
            outcome=report.outcome,
            decision_note=report.decision_note,
            decided_at=report.dismissed_at,
        )
        for report in rows
    ]


@router.get("/moderation/notice", response_model=Optional[ModerationNotice])
def get_moderation_notice(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Art. 17 DSA: begründete Mitteilung zur laufenden Maßnahme gegen das
    eigene Konto. Liefert null, wenn keine Beschränkung aktiv ist. (Ein Ban
    kommt hier nicht an — den erfährt der Betroffene im Login-Fehler.)"""
    if not current_user.is_messaging_muted or not current_user.moderation_reason:
        return None
    return ModerationNotice(
        action=current_user.moderation_action or ModerationAction.mute.value,
        reason=current_user.moderation_reason,
        action_at=current_user.moderation_action_at or current_user.messaging_muted_until,
        muted_until=current_user.messaging_muted_until,
        appeal_hint=APPEAL_HINT,
    )


@router.post("/blocks", status_code=201)
@limiter.limit("20/minute")
def create_block(
    request: Request,
    payload: BlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.user_id == current_user.id:
        raise HTTPException(400, "Du kannst dich nicht selbst blockieren.")

    blocked_user = db.query(User).filter(User.id == payload.user_id).first()
    if not blocked_user:
        raise HTTPException(404, "Nutzer nicht gefunden.")

    existing = (
        db.query(Block)
        .filter(Block.blocker_id == current_user.id, Block.blocked_id == payload.user_id)
        .first()
    )
    if not existing:
        db.add(Block(blocker_id=current_user.id, blocked_id=payload.user_id))
        db.commit()
    return {"blocked": True}


@router.get("/blocks")
def list_blocks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(Block).filter(Block.blocker_id == current_user.id).all()
    return [row.blocked_id for row in rows]


@router.get("/blocks/profiles", response_model=list[BlockedProfileOut])
def list_blocked_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Blockierte Profile samt Name und Foto - Grundlage dafür, dass eine
    Blockierung in der Oberfläche auch wieder aufgehoben werden kann."""
    blocked_ids = [
        row.blocked_id
        for row in db.query(Block.blocked_id).filter(Block.blocker_id == current_user.id)
    ]
    if not blocked_ids:
        return []

    users = db.query(User).filter(User.id.in_(blocked_ids)).all()
    result = []
    for user in users:
        approved = [p for p in user.photos if p.status == PhotoStatus.approved]
        first = approved[0] if approved else None
        result.append(
            BlockedProfileOut(
                id=user.id,
                name=user.name,
                photo_url=(first.thumb_url or first.url) if first else None,
            )
        )
    return result


@router.delete("/blocks/{user_id}")
def remove_block(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    block = (
        db.query(Block)
        .filter(Block.blocker_id == current_user.id, Block.blocked_id == user_id)
        .first()
    )
    if not block:
        raise HTTPException(404, "Blockierung nicht gefunden.")
    db.delete(block)
    db.commit()
    return {"blocked": False}
