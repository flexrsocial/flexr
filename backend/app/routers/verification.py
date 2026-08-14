"""Alters- und Identitätsprüfung aus Sicht des Nutzers.

Ein einziger Vorgang in zwei Schritten:

    1. Ein Live-Selfie, frontal in die Kamera (bestehender Schritt)
    2. Amtlicher Lichtbildausweis, temporär in einem privaten Storage-Bereich

Danach entscheidet ein Mensch (siehe routers/admin.py). Es gibt keine
automatisierte Gesichtserkennung und keinen externen Prüfdienst.

Kein Endpunkt in dieser Datei kann ``approved``, ``age_verified`` oder die
Freischaltung des Kontos setzen - das passiert ausschließlich über den
Admin-Router.
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import storage
from ..database import get_db
from ..mailer import email_configured
from ..models import User, VerificationRequest, VerificationStatus
from ..rate_limit import limiter
from ..schemas import (
    PresignPhotoRequest,
    PresignPhotoResponse,
    VerificationDocumentPresignRequest,
    VerificationDocumentSubmitRequest,
    VerificationStatusOut,
    VerificationSubmitRequest,
)
from ..security import get_current_user
from ..storage import create_presigned_verification_upload
from ..verification_service import (
    decision_is_binding,
    document_type_options,
    latest_request,
    needs_back_side,
    next_step_for,
    open_request,
    purge_uploads,
    reason_text,
)

logger = logging.getLogger("flexr.verification")

router = APIRouter(prefix="/api/verification", tags=["verification"])

# Der Vorgang verlangt genau ein Selfie, frontal in die Kamera. Früher zog der
# Server die Pose dafür zufällig aus einem Pool ("Schau nach links", "Lächle
# breit" ...) - als Liveness-Schutz gegen vorbereitete Fotos. Das ist am
# 9.8.2026 auf Wunsch gestrichen worden: die Echtheit entscheidet ohnehin ein
# Mensch beim Abgleich mit dem Ausweis.
#
# Die Antwort bleibt bewusst eine *Liste* von Anweisungen (heute mit genau
# einem Eintrag) - so bleiben die ausgelieferten App-Versionen kompatibel und
# ein Posen-Pool ließe sich ohne Client-Änderung wieder einführen.
SELFIE_PROMPTS = ["Schau direkt in die Kamera"]


def email_confirmation_enforced() -> bool:
    """Wird die E-Mail-Bestätigung verlangt?

    Nur, wenn der Server überhaupt Mail verschicken kann. Ohne SMTP-Zugangsdaten
    schreibt der Mailer die Nachricht bloß ins Log (siehe app/mailer.py) - ein
    Nutzer bekäme also nie einen Link und käme damit aus dem Wartezustand nicht
    mehr heraus. Eine Pflicht, die niemand erfüllen kann, ist keine Pflicht,
    sondern eine Sackgasse.

    Sobald SMTP konfiguriert ist, greift die Bestätigung von selbst - auch für
    Konten, die in der Zwischenzeit entstanden sind. Die kommen über
    "Neu senden" an ihren Link.
    """
    return email_configured()


def _status_out(user: User, req: VerificationRequest | None) -> VerificationStatusOut:
    """Baut die Statusantwort aus dem Server-Zustand - nie aus Client-Angaben."""
    if req is None:
        status = "none"
    else:
        status = req.status.value

    prompts = None
    if req is not None and req.status == VerificationStatus.in_progress:
        prompts = json.loads(req.prompts)

    step = next_step_for(req)
    return VerificationStatusOut(
        status=status,
        prompts=prompts,
        next_step=step,
        reason=reason_text(req.review_reason) if req is not None else None,
        verification_required=user.verification_required,
        account_activated=user.is_account_activated,
        # Für den Client heißt das Feld "steht die Bestätigung noch an?" - ohne
        # Mailversand steht sie nicht an, sonst zeigte die Oberfläche einen
        # Schritt an, den niemand abschließen kann.
        email_verified=user.email_verified or not email_confirmation_enforced(),
        document_types=document_type_options() if step == "document" else None,
    )


@router.get("/status", response_model=VerificationStatusOut)
def get_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _status_out(current_user, latest_request(db, current_user.id))


@router.post("/start", response_model=VerificationStatusOut)
@limiter.limit("10/minute")
def start_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Startet den Selfie-Schritt bzw. gibt einen laufenden Vorgang zurück."""
    # Die bestätigte Adresse steht vor allem anderen: Ein Mensch soll keine
    # Ausweisaufnahme begutachten, solange nicht feststeht, dass die Adresse dem
    # Nutzer gehört - und ein Tippfehler soll auffallen, bevor Aufnahmen
    # entstehen, die danach wieder gelöscht werden müssten.
    if not current_user.email_verified and email_confirmation_enforced():
        raise HTTPException(400, "Bestätige zuerst deine E-Mail-Adresse.")
    if not current_user.photos:
        raise HTTPException(400, "Lade zuerst mindestens ein Profilfoto hoch.")

    latest = latest_request(db, current_user.id)

    if latest is not None and latest.status in (
        VerificationStatus.approved, VerificationStatus.rejected
    ):
        if decision_is_binding(current_user, latest):
            # Bewusst keine Wiederholung auf Zuruf: sonst könnte eine abgelehnte
            # Prüfung (etwa wegen Alters- oder Personenabweichung) beliebig oft
            # neu versucht werden.
            if latest.status == VerificationStatus.approved:
                raise HTTPException(400, "Dein Profil ist bereits verifiziert.")
            raise HTTPException(
                400,
                "Deine Verifizierung wurde abgeschlossen und kann nicht erneut "
                "gestartet werden. Melde dich bei Fragen unter flexr.social@proton.me.",
            )
        # Die Prüfung wurde nach dieser Entscheidung neu angefordert
        # (Bestandskonto, siehe Admin-Aktion "Prüfung nachfordern") - dafür
        # beginnt ein frischer Vorgang.
        latest = None

    if latest is not None:
        if latest.status == VerificationStatus.submitted:
            raise HTTPException(400, "Deine Verifizierung ist bereits in Prüfung.")
        if latest.status in (VerificationStatus.in_progress, VerificationStatus.id_required):
            # Laufender Vorgang: unveränderten Stand zurückgeben (bei
            # in_progress also dieselbe Anweisung)
            return _status_out(current_user, latest)
        if latest.selfies:
            # Neu-Upload angefordert, aber nur für den Ausweis - Selfies gelten
            return _status_out(current_user, latest)
        # Neu-Upload inkl. Selfie: derselbe Vorgang beginnt von vorn
        latest.prompts = json.dumps(SELFIE_PROMPTS, ensure_ascii=False)
        latest.status = VerificationStatus.in_progress
        db.commit()
        return _status_out(current_user, latest)

    req = VerificationRequest(
        user_id=current_user.id,
        status=VerificationStatus.in_progress,
        prompts=json.dumps(SELFIE_PROMPTS, ensure_ascii=False),
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _status_out(current_user, req)


@router.post("/selfies/presign", response_model=PresignPhotoResponse)
@limiter.limit("20/minute")
def presign_selfie(
    request: Request,
    payload: PresignPhotoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    active = open_request(db, current_user.id)
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
    """Selfie-Schritt abschließen. Danach fehlt noch der Lichtbildausweis."""
    active = open_request(db, current_user.id)
    if active is None or active.status != VerificationStatus.in_progress:
        raise HTTPException(400, "Keine laufende Verifizierung. Bitte zuerst starten.")

    expected_prompts = json.loads(active.prompts)
    submitted_prompts = [s.prompt for s in payload.selfies]
    if submitted_prompts != expected_prompts:
        raise HTTPException(400, "Die Aufnahmen passen nicht zu den angeforderten Selfies.")

    prefix = f"users/{current_user.id}/verify/"
    for s in payload.selfies:
        if not s.object_key.startswith(prefix):
            raise HTTPException(400, "Ungültiger object_key.")

    active.selfies = json.dumps(
        [{"prompt": s.prompt, "object_key": s.object_key} for s in payload.selfies],
        ensure_ascii=False,
    )
    # Die Prüfung ist erst mit dem Ausweis vollständig - der Vorgang landet
    # deshalb noch nicht in der Admin-Warteschlange.
    active.status = VerificationStatus.id_required
    active.review_reason = None
    db.commit()
    return _status_out(current_user, active)


# ---------- Schritt 2: amtlicher Lichtbildausweis ----------


def _document_step_request(db: Session, user: User) -> VerificationRequest:
    """Der Vorgang, für den gerade ein Ausweis hochgeladen werden darf."""
    active = open_request(db, user.id)
    if active is None or active.status not in (
        VerificationStatus.id_required,
        VerificationStatus.reupload_required,
    ):
        raise HTTPException(
            400, "Für diesen Schritt läuft keine offene Verifizierung."
        )
    if active.status == VerificationStatus.reupload_required and not active.selfies:
        raise HTTPException(400, "Bitte zuerst die Selfie-Verifizierung wiederholen.")
    return active


@router.post("/document/presign", response_model=PresignPhotoResponse)
@limiter.limit("20/minute")
def presign_document(
    request: Request,
    payload: VerificationDocumentPresignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload-URL für eine Ausweisaufnahme.

    Das Ziel liegt in einem privaten Prefix ohne öffentliche URL. Die
    Größenangabe wird hier vorab geprüft und nach dem Upload noch einmal am
    tatsächlichen Objekt kontrolliert.
    """
    active = _document_step_request(db, current_user)
    if payload.byte_size > storage.MAX_DOCUMENT_BYTES:
        raise HTTPException(
            400,
            f"Die Aufnahme ist zu groß (max. {storage.MAX_DOCUMENT_BYTES // (1024 * 1024)} MB).",
        )
    result = storage.create_presigned_document_upload(active.id, payload.content_type)
    return PresignPhotoResponse(**result)


@router.post("/document/submit", response_model=VerificationStatusOut)
@limiter.limit("10/minute")
def submit_document(
    request: Request,
    payload: VerificationDocumentSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ausweisaufnahmen einreichen. Danach geht der Vorgang in die Prüfung."""
    active = _document_step_request(db, current_user)

    keys = [("front", payload.front_object_key)]
    if payload.back_object_key:
        keys.append(("back", payload.back_object_key))
    elif needs_back_side(payload.document_type):
        raise HTTPException(
            400, "Für dieses Dokument brauchen wir auch eine Aufnahme der Rückseite."
        )

    # Zuordnung: Der Schlüssel muss aus einer Presign-Anfrage genau dieses
    # Vorgangs stammen. Fremde Schlüssel sind damit ausgeschlossen, auch wenn
    # jemand eine gültige Objekt-ID erraten würde.
    expected_prefix = f"{storage.VERIFICATION_DOCUMENT_PREFIX}{active.id}/"
    for _side, key in keys:
        if not key.startswith(expected_prefix):
            raise HTTPException(400, "Ungültiger object_key.")

    # Serverseitige Datei-Prüfung am tatsächlich hochgeladenen Objekt: Größe und
    # echte Magic Bytes. Der vom Client behauptete Content-Type zählt nicht.
    for _side, key in keys:
        try:
            result = storage.inspect_uploaded_image(key)
        except Exception:
            # Ohne Objektinhalte im Log - der Schlüssel selbst ist eine Zufalls-ID.
            logger.warning("Ausweisaufnahme nicht prüfbar (Vorgang %s)", active.id)
            raise HTTPException(400, "Die Aufnahme konnte nicht gelesen werden. Bitte erneut hochladen.")
        if not result["ok"]:
            storage.delete_objects_verified([key])
            raise HTTPException(
                400,
                "Die Aufnahme ist kein gültiges Bild oder zu groß. "
                "Bitte als JPEG oder PNG erneut hochladen.",
            )

    # Ein früherer Upload desselben Vorgangs (Neu-Upload nach Aufforderung)
    # wird ersetzt - die alten Dateien müssen weg.
    previous = active.documents
    if previous:
        old_keys = [entry["object_key"] for entry in json.loads(previous)]
        new_keys = {key for _side, key in keys}
        storage.delete_objects_verified([k for k in old_keys if k not in new_keys])

    active.document_type = payload.document_type
    active.documents = json.dumps(
        [{"side": side, "object_key": key} for side, key in keys], ensure_ascii=False
    )
    active.status = VerificationStatus.submitted
    active.submitted_at = datetime.utcnow()
    active.review_reason = None
    db.commit()
    return _status_out(current_user, active)


@router.delete("/document", response_model=VerificationStatusOut)
@limiter.limit("10/minute")
def discard_documents(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Eingereichte Ausweisaufnahmen zurückziehen, solange noch niemand geprüft hat.

    Datenschutzfreundlicher Ausstieg: Wer es sich anders überlegt, bekommt die
    Aufnahmen sofort gelöscht statt sie bis zur Prüfung liegen zu lassen.
    """
    active = open_request(db, current_user.id)
    if active is None or active.status != VerificationStatus.submitted:
        raise HTTPException(400, "Es liegt keine eingereichte Aufnahme vor.")

    purge_uploads(active, selfies=False, documents=True)
    active.document_type = None
    active.status = VerificationStatus.id_required
    db.commit()
    return _status_out(current_user, active)
