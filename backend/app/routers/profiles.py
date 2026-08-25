import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import consents, mailer, telegram
from ..database import get_db
from ..geo import city_for_plz
from ..models import GYM_CHOICES, ConsentType, Photo, PhotoStatus, User
from ..retention import ACCOUNT_GRACE_PERIOD_DAYS
from ..schemas import (
    AddPhotoRequest,
    ConsentGrantRequest,
    ConsentOut,
    ConsentRevokeRequest,
    DeleteAccountRequest,
    MyProfileOut,
    PresignPhotoRequest,
    PresignPhotoResponse,
    ProfileOut,
    UpdateProfileRequest,
)
from ..security import get_current_user
from ..storage import (
    create_presigned_upload,
    inspect_uploaded_photo,
    public_url_for,
    set_photo_cache_control,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


def to_public_profile(user: User) -> ProfileOut:
    """Profil-Ansicht für andere Nutzer (Swipe-Deck, Matches) - zeigt nur
    von der Moderation freigegebene Fotos, im Unterschied zur eigenen Profilansicht
    (/me), die alle Fotos inkl. Status zeigt."""
    profile = ProfileOut.model_validate(user)
    profile.photos = [p for p in profile.photos if p.status == PhotoStatus.approved.value]
    return profile


@router.get("/me", response_model=MyProfileOut)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=MyProfileOut)
def update_my_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fields = payload.model_dump(exclude_unset=True)

    # PLZ und Ort gehören zusammen - der Ort kommt aus dem PLZ-Lookup im Frontend.
    if ("plz" in fields) != ("city" in fields):
        raise HTTPException(400, "PLZ und Ort müssen gemeinsam aktualisiert werden.")

    # Wie bei der Registrierung gilt der amtliche Ortsname zur PLZ.
    if "plz" in fields:
        fields["city"] = city_for_plz(fields["plz"]) or fields["city"]

    if "gym" in fields:
        from .gyms import gym_exists_for_profile

        if not gym_exists_for_profile(db, fields["gym"]):
            raise HTTPException(400, "Unbekanntes Gym. Bitte aus der Liste wählen oder vorschlagen.")

    if "bio" in fields:
        from ..safety_checks import check_public_text

        bio_problem = check_public_text(fields["bio"])
        if bio_problem:
            raise HTTPException(400, bio_problem)

    for field, value in fields.items():
        if field == "bio" and value == "":
            value = None  # leere Bio = Bio entfernen
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/consents", response_model=list[ConsentOut])
def list_my_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Welche Einwilligungen wann und zu welcher Fassung erteilt wurden.

    Teil der Auskunft nach Art. 15 DSGVO und Voraussetzung dafür, dass ein
    Widerruf überhaupt gezielt möglich ist.
    """
    return [
        ConsentOut(
            consent_type=entry.consent_type,
            version=entry.version,
            granted_at=entry.granted_at,
            revoked_at=entry.revoked_at,
            active=entry.is_active,
        )
        for entry in consents.history(db, current_user.id)
    ]


@router.post("/me/consents/revoke")
def revoke_my_consent(
    payload: ConsentRevokeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Widerruf einer Einwilligung mit Wirkung für die Zukunft (Art. 7 Abs. 3).

    Der Widerruf darf nicht schwerer sein als die Erteilung - angehakt wurde
    mit einem Klick, also geht auch das hier mit einem Klick, statt über eine
    Mail an den Support.

    Was der Widerruf der Art.-9-Einwilligung bedeutet, wird ehrlich
    zurückgemeldet: Geschlecht und gesuchtes Geschlecht sind die Grundlage des
    Matchings. Ohne sie kann FLEXR niemanden mehr vorschlagen - das Konto
    bleibt bestehen, das Deck aber leer. Wer das nicht will, löscht statt zu
    widerrufen. Die Entscheidung bleibt beim Nutzer; verweigert wird der
    Widerruf nicht.
    """
    consent_type = ConsentType(payload.consent_type)
    revoked = consents.revoke(db, current_user.id, consent_type)

    folge = {
        ConsentType.sensitive_data: (
            "Ohne diese Einwilligung dürfen wir Geschlecht und gesuchtes "
            "Geschlecht nicht mehr zum Matching verwenden. Dein Konto bleibt "
            "bestehen, es werden dir aber keine Profile mehr vorgeschlagen und "
            "du erscheinst in keinem Deck. Willst du ganz weg, lösche dein "
            "Konto — dann werden die Angaben mitgelöscht."
        ),
        ConsentType.verification_media: (
            "Noch nicht geprüfte Aufnahmen werden gelöscht. Eine bereits "
            "abgeschlossene Prüfung bleibt als Ergebnis bestehen — die Bilder "
            "dazu sind ohnehin längst gelöscht."
        ),
    }[consent_type]

    return {
        "revoked": revoked,
        "consent_type": payload.consent_type,
        "consequence": folge,
    }


@router.post("/me/consents/grant")
def grant_my_consent(
    payload: ConsentGrantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Einen zuvor erklärten Widerruf rückgängig machen (erneute Einwilligung).

    Nicht von der DSGVO verlangt, aber ohne das bliebe ein Konto nach dem
    Widerruf von sensitive_data dauerhaft mit leerem Deck zurück, ohne
    reparierbar zu sein außer über die Kontolöschung. Ein Klick zum Widerruf,
    ein Klick zurück - dieselbe Symmetrie wie beim Widerruf selbst.
    """
    consent_type = ConsentType(payload.consent_type)
    entry = consents.grant(db, current_user, consent_type)

    folge = {
        ConsentType.sensitive_data: (
            "Deine Einwilligung ist wieder aktiv. Du erscheinst ab sofort "
            "wieder im Deck und dir werden wieder Profile vorgeschlagen."
        ),
        ConsentType.verification_media: (
            "Deine Einwilligung ist wieder aktiv. Bereits gelöschte Aufnahmen "
            "sind damit nicht wiederhergestellt - für eine neue Prüfung "
            "reichst du sie im Verifizierungsschritt erneut ein."
        ),
    }[consent_type]

    return {
        "granted": True,
        "consent_type": payload.consent_type,
        "version": entry.version,
        "consequence": folge,
    }


@router.delete("/me")
def delete_my_account(
    payload: DeleteAccountRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Selbstlöschung mit Passwort-Bestätigung: Konto wird sofort deaktiviert
    (Login gesperrt, für andere unsichtbar) und nach 30 Tagen Karenzzeit
    endgültig gelöscht (siehe Datenschutzerklärung)."""
    from ..security import verify_password

    from ..cleanup import purge_verification_uploads_for_user

    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(400, "Falsches Passwort.")

    # Ausweisaufnahmen und Verifizierungs-Selfies sofort löschen - sie sollen
    # die 30-tägige Karenzzeit nicht überdauern.
    purge_verification_uploads_for_user(db, current_user)

    current_user.deleted_at = datetime.utcnow()
    db.commit()

    # Bestätigung samt Reaktivierungshinweis - nach der Antwort, nicht davor
    # (siehe app/mailer.py zur Begründung dieses Musters).
    purge_at = current_user.deleted_at + timedelta(days=ACCOUNT_GRACE_PERIOD_DAYS)
    background_tasks.add_task(
        mailer.send_account_deletion_confirmation,
        current_user.email,
        current_user.name,
        purge_at,
        ACCOUNT_GRACE_PERIOD_DAYS,
    )

    return {"deleted": True, "purge_after_days": ACCOUNT_GRACE_PERIOD_DAYS}


@router.post("/me/photos/presign", response_model=PresignPhotoResponse)
def presign_photo_upload(
    payload: PresignPhotoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Erzeugt eine Presigned-Upload-URL (S3/R2). Der Client lädt die Bilddatei
    direkt dorthin hoch und registriert danach den zurückgegebenen object_key
    über POST /me/photos - es fließen keine Bilddaten durchs Backend."""
    existing_count = db.query(Photo).filter(Photo.user_id == current_user.id).count()
    if existing_count >= 6:
        raise HTTPException(400, "Maximal 6 Fotos erlaubt.")

    result = create_presigned_upload(current_user.id, payload.content_type)
    return PresignPhotoResponse(**result)


def _foto_ist_brauchbar(object_key: str) -> bool:
    """Groesse und echter Dateianfang des hochgeladenen Objekts.

    Bewusst durchlaessig, wenn die Pruefung selbst scheitert: Ein Zeitfehler
    oder eine Stoerung beim Objekt-Storage darf keinen sonst gueltigen Upload
    abweisen. Genau daran haengt seit dem 15.08.2026 die Kernfunktion der App -
    ein Fehler in dieser Zeile waere ein zweiter Totalausfall des Foto-Uploads.
    Abgewiesen wird deshalb nur, was nachweislich zu gross oder kein Bild ist;
    alles Unklare wird geloggt und durchgelassen.
    """
    try:
        befund = inspect_uploaded_photo(object_key)
    except Exception:  # noqa: BLE001 - siehe Docstring
        logger.warning("Foto konnte nicht geprueft werden: %s", object_key, exc_info=True)
        return True
    if not befund["ok"]:
        logger.info(
            "Foto abgewiesen: %s (%s Byte, erkannt: %s)",
            object_key, befund["size"], befund["detected"])
    return befund["ok"]


@router.post("/me/photos", response_model=MyProfileOut)
def add_photo(
    payload: AddPhotoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.object_key.startswith(f"users/{current_user.id}/"):
        raise HTTPException(400, "Ungültiger object_key.")
    if payload.thumb_object_key and not payload.thumb_object_key.startswith(f"users/{current_user.id}/"):
        raise HTTPException(400, "Ungültiger thumb_object_key.")

    existing_count = db.query(Photo).filter(Photo.user_id == current_user.id).count()
    if existing_count >= 6:
        raise HTTPException(400, "Maximal 6 Fotos erlaubt.")

    # Erst jetzt laesst sich pruefen, was tatsaechlich im Storage liegt: Der
    # Presigned PUT laeuft am Backend vorbei, der Content-Type ist nur eine
    # Behauptung des Clients. Ohne diesen Schritt kaeme unter "image/jpeg"
    # beliebiger Inhalt in beliebiger Groesse durch.
    for key in filter(None, (payload.object_key, payload.thumb_object_key)):
        if not _foto_ist_brauchbar(key):
            raise HTTPException(
                400, "Die hochgeladene Datei ist kein unterstütztes Bild oder zu groß.")

    # Cache-Control nachtraeglich setzen - siehe set_photo_cache_control().
    set_photo_cache_control(payload.object_key)
    if payload.thumb_object_key:
        set_photo_cache_control(payload.thumb_object_key)

    # Nächste freie Position aus dem Maximum ableiten, nicht aus der Anzahl:
    # nach dem Löschen eines Fotos aus der Mitte wäre die Anzahl kleiner als die
    # höchste vergebene Position, und zwei Fotos bekämen dieselbe Nummer.
    max_position = (
        db.query(func.max(Photo.position)).filter(Photo.user_id == current_user.id).scalar()
    )
    photo = Photo(
        user_id=current_user.id,
        url=public_url_for(payload.object_key),
        thumb_url=public_url_for(payload.thumb_object_key) if payload.thumb_object_key else None,
        position=0 if max_position is None else max_position + 1,
    )
    db.add(photo)
    db.commit()
    db.refresh(current_user)
    telegram.notify_admin_task(
        f"🆕 Neues Foto zur Prüfung im FLEXR-Admin-Dashboard: {current_user.name}"
    )
    return current_user


@router.delete("/me/photos/{photo_id}", response_model=MyProfileOut)
def delete_photo(
    photo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..cleanup import delete_storage_objects, storage_keys_for_photo

    photo = (
        db.query(Photo)
        .filter(Photo.id == photo_id, Photo.user_id == current_user.id)
        .first()
    )
    if not photo:
        raise HTTPException(404, "Foto nicht gefunden.")
    # Die Bilddatei mitnehmen: Fotos liegen unter einer öffentlichen URL, die
    # ohne diesen Schritt weiter ausliefert - das Foto wäre nur aus dem Profil
    # verschwunden, nicht aus dem Netz.
    delete_storage_objects(storage_keys_for_photo(photo))
    db.delete(photo)
    db.flush()

    # Lücken schließen, damit die Positionen wieder 0..n-1 durchlaufen - sonst
    # driften sie mit jedem Löschen weiter von der Anzeigereihenfolge weg.
    remaining = (
        db.query(Photo)
        .filter(Photo.user_id == current_user.id)
        .order_by(Photo.position, Photo.id)
        .all()
    )
    for index, remaining_photo in enumerate(remaining):
        remaining_photo.position = index

    db.commit()
    db.refresh(current_user)
    return current_user
