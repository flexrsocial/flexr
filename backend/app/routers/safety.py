from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Block, ModerationAction, Report, User
from ..moderation import APPEAL_HINT
from ..rate_limit import limiter
from ..schemas import (
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
            "sofort. Notiere dir das Aktenzeichen, falls du dich später darauf "
            "berufen willst."
        ),
    )


@router.get("/reports/mine", response_model=list[MyReportOut])
def list_my_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Die eigenen Meldungen mit ihrem Stand (Art. 16 Abs. 5 DSA).

    Bis 15.08.2026 versprach frontend/sicherheit.html: "du siehst das Ergebnis
    unter 'Meine Meldungen' im Konto-Bereich". Diese Ansicht gab es nicht - der
    Melder bekam ein Aktenzeichen und danach nie wieder etwas zu hören, obwohl
    der Admin die Entscheidung längst in ``Report.decision_note`` geschrieben
    hatte. Hier wird sie ihm zugänglich gemacht.
    """
    rows = (
        db.query(Report)
        .filter(Report.reporter_id == current_user.id)
        .order_by(Report.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        MyReportOut(
            reference=row.reference,
            created_at=row.created_at,
            reason=row.reason,
            status="decided" if row.outcome else "open",
            outcome=row.outcome,
            decision_note=row.decision_note,
            decided_at=row.dismissed_at if row.outcome else None,
        )
        for row in rows
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
