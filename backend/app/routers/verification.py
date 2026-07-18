import json
import random

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, VerificationRequest, VerificationStatus
from ..rate_limit import limiter
from ..schemas import (
    PresignPhotoRequest,
    PresignPhotoResponse,
    VerificationStatusOut,
    VerificationSubmitRequest,
)
from ..security import get_current_user
from ..storage import create_presigned_verification_upload

router = APIRouter(prefix="/api/verification", tags=["verification"])

# Posen-Pool: Der Server wählt zufällig 3 aus - dadurch kann niemand vorbereitete
# Fotos verwenden (Liveness-Prinzip: nur eine echte Person vor der Kamera kann
# die verlangten Posen spontan liefern).
POSE_PROMPTS = [
    "Schau nach links",
    "Schau nach rechts",
    "Schau nach oben",
    "Lächle breit in die Kamera",
    "Halte einen Daumen hoch neben dein Gesicht",
    "Zeig ein Peace-Zeichen neben deinem Gesicht",
    "Leg eine Hand flach auf deinen Kopf",
    "Zeig mit dem Finger auf die Kamera",
]


def _active_request(db: Session, user_id: str) -> VerificationRequest | None:
    return (
        db.query(VerificationRequest)
        .filter(
            VerificationRequest.user_id == user_id,
            VerificationRequest.status.in_(
                [VerificationStatus.in_progress, VerificationStatus.submitted]
            ),
        )
        .order_by(VerificationRequest.created_at.desc())
        .first()
    )


@router.get("/status", response_model=VerificationStatusOut)
def get_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.is_verified:
        return VerificationStatusOut(status="approved")

    latest = (
        db.query(VerificationRequest)
        .filter(VerificationRequest.user_id == current_user.id)
        .order_by(VerificationRequest.created_at.desc())
        .first()
    )
    if latest is None:
        return VerificationStatusOut(status="none")
    if latest.status == VerificationStatus.in_progress:
        return VerificationStatusOut(status="in_progress", prompts=json.loads(latest.prompts))
    return VerificationStatusOut(status=latest.status.value)


@router.post("/start", response_model=VerificationStatusOut)
@limiter.limit("10/minute")
def start_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.is_verified:
        raise HTTPException(400, "Dein Profil ist bereits verifiziert.")
    if not current_user.photos:
        raise HTTPException(400, "Lade zuerst mindestens ein Profilfoto hoch.")

    active = _active_request(db, current_user.id)
    if active is not None:
        if active.status == VerificationStatus.submitted:
            raise HTTPException(400, "Deine Verifizierung ist bereits in Prüfung.")
        # Laufende Anfrage: dieselben Posen erneut ausgeben
        return VerificationStatusOut(status="in_progress", prompts=json.loads(active.prompts))

    prompts = random.sample(POSE_PROMPTS, 3)
    req = VerificationRequest(
        user_id=current_user.id,
        status=VerificationStatus.in_progress,
        prompts=json.dumps(prompts, ensure_ascii=False),
    )
    db.add(req)
    db.commit()
    return VerificationStatusOut(status="in_progress", prompts=prompts)


@router.post("/selfies/presign", response_model=PresignPhotoResponse)
@limiter.limit("20/minute")
def presign_selfie(
    request: Request,
    payload: PresignPhotoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    active = _active_request(db, current_user.id)
    if active is None or active.status != VerificationStatus.in_progress:
        raise HTTPException(400, "Keine laufende Verifizierung. Bitte zuerst starten.")
    result = create_presigned_verification_upload(current_user.id, payload.content_type)
    return PresignPhotoResponse(**result)


@router.post("/submit", response_model=VerificationStatusOut)
@limiter.limit("10/minute")
def submit_verification(
    request: Request,
    payload: VerificationSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    active = _active_request(db, current_user.id)
    if active is None or active.status != VerificationStatus.in_progress:
        raise HTTPException(400, "Keine laufende Verifizierung. Bitte zuerst starten.")

    expected_prompts = json.loads(active.prompts)
    submitted_prompts = [s.prompt for s in payload.selfies]
    if submitted_prompts != expected_prompts:
        raise HTTPException(400, "Die Selfies passen nicht zu den angeforderten Posen.")

    prefix = f"users/{current_user.id}/verify/"
    for s in payload.selfies:
        if not s.object_key.startswith(prefix):
            raise HTTPException(400, "Ungültiger object_key.")

    active.selfies = json.dumps(
        [{"prompt": s.prompt, "object_key": s.object_key} for s in payload.selfies],
        ensure_ascii=False,
    )
    active.status = VerificationStatus.submitted
    db.commit()
    return VerificationStatusOut(status="submitted")
