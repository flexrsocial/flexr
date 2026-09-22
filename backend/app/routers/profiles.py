import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import consents, mailer, premium, telegram
from ..database import get_db
from ..geo import city_for_plz
from ..models import (
    GYM_CHOICES,
    MAX_PHOTOS,
    MIN_PHOTOS,
    ConsentType,
    Photo,
    PhotoStatus,
    User,
)
from ..rate_limit import limiter
from ..retention import ACCOUNT_GRACE_PERIOD_DAYS
from ..schemas import (
    AddPhotoRequest,
    ConsentGrantRequest,
    ConsentOut,
    ConsentRevokeRequest,
    DeleteAccountRequest,
    EmailChangeRequest,
    OkResponse,
    PasswordChangeRequest,
    TokenResponse,
    MyProfileOut,
    NotificationSettingsUpdate,
    PresignPhotoRequest,
    PresignPhotoResponse,
    ProfileOut,
    ReorderPhotosRequest,
    UpdateProfileRequest,
)
from ..security import get_current_user
from ..storage import (
    create_presigned_upload,
    inspect_uploaded_photo,
    public_url_for,
    set_photo_headers,
)
from ..timeutil import utcnow

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

        # Karenz gegen haeufigen Gym-Wechsel (siehe models.GYM_CHANGE_COOLDOWN_DAYS):
        # der Suchumkreis wird ab der Gym-Adresse berechnet, ohne Sperre liesse
        # sich der kostenpflichtige groessere FLEXR-Premium-Radius umgehen,
        # indem der Mittelpunkt per Gym-Wechsel einfach mitwandert. Ein Patch
        # mit demselben Gym ist kein Wechsel und loest die Karenz nicht aus.
        if fields["gym"] != current_user.gym:
            locked_until = current_user.gym_change_locked_until
            if locked_until is not None:
                raise HTTPException(
                    400,
                    "Das Gym kann nur alle drei Monate geändert werden (Schutz "
                    "vor Umgehung des FLEXR-Premium-Suchumkreises) - nächste "
                    f"Änderung ab {locked_until.strftime('%d.%m.%Y')} möglich.",
                )
            fields["gym_changed_at"] = utcnow()

    if "bio" in fields:
        from ..safety_checks import check_public_text

        bio_problem = check_public_text(fields["bio"])
        if bio_problem:
            raise HTTPException(400, bio_problem)

    # Der volle Umkreis (bis 250 km) gehoert zu FLEXR Premium. Gekappt statt
    # abgelehnt - siehe premium.clamp_radius(): Wer Premium kuendigt, haette
    # sonst ein Profil, das sich nie wieder speichern laesst.
    if fields.get("search_radius_km") is not None:
        fields["search_radius_km"] = premium.clamp_radius(
            current_user, fields["search_radius_km"]
        )

    # "language" laeuft ueber denselben generischen Weg wie die Profilfelder.
    # Sie ist kein Profilfeld im engeren Sinn, sondern die Sprache, in der der
    # Server diesem Nutzer schreibt (siehe models.User.language) - der
    # Sprachregler in der Oberflaeche schickt sie mit, sobald jemand umschaltet.
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

    current_user.deleted_at = utcnow()
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
        current_user.language,
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
    if existing_count >= MAX_PHOTOS:
        raise HTTPException(400, f"Maximal {MAX_PHOTOS} Fotos erlaubt.")

    result = create_presigned_upload(current_user.id, payload.content_type)
    return PresignPhotoResponse(**result)


def _foto_befund(object_key: str) -> dict:
    """Groesse und echter Dateianfang des hochgeladenen Objekts.

    Bewusst durchlaessig, wenn die Pruefung selbst scheitert: Ein Zeitfehler
    oder eine Stoerung beim Objekt-Storage darf keinen sonst gueltigen Upload
    abweisen. Genau daran haengt seit dem 15.08.2026 die Kernfunktion der App -
    ein Fehler in dieser Zeile waere ein zweiter Totalausfall des Foto-Uploads.
    Abgewiesen wird deshalb nur, was nachweislich zu gross oder kein Bild ist;
    alles Unklare wird geloggt und durchgelassen.

    Liefert den ganzen Befund statt nur ``ok``, weil der Aufrufer den erkannten
    Typ gleich weiterverwendet (siehe ``set_photo_headers``) - er stammt aus den
    Magic Bytes und ist damit belastbarer als die Behauptung des Clients beim
    Presign. Ohne diese Rueckgabe muesste das Objekt ein zweites Mal gelesen
    werden, nur um dasselbe Ergebnis zu bekommen.
    """
    try:
        befund = inspect_uploaded_photo(object_key)
    except Exception:  # noqa: BLE001 - siehe Docstring
        logger.warning("Foto konnte nicht geprueft werden: %s", object_key, exc_info=True)
        return {"ok": True, "size": 0, "detected": None}
    if not befund["ok"]:
        logger.info(
            "Foto abgewiesen: %s (%s Byte, erkannt: %s)",
            object_key, befund["size"], befund["detected"])
    return befund


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
    if existing_count >= MAX_PHOTOS:
        raise HTTPException(400, f"Maximal {MAX_PHOTOS} Fotos erlaubt.")

    # Erst jetzt laesst sich pruefen, was tatsaechlich im Storage liegt: Der
    # Presigned PUT laeuft am Backend vorbei, der Content-Type ist nur eine
    # Behauptung des Clients. Ohne diesen Schritt kaeme unter "image/jpeg"
    # beliebiger Inhalt in beliebiger Groesse durch.
    erkannter_typ: dict[str, str | None] = {}
    for key in filter(None, (payload.object_key, payload.thumb_object_key)):
        befund = _foto_befund(key)
        if not befund["ok"]:
            raise HTTPException(
                400, "Die hochgeladene Datei ist kein unterstütztes Bild oder zu groß.")
        erkannter_typ[key] = befund["detected"]

    # Cache-Control und Content-Type nachtraeglich setzen - siehe
    # set_photo_headers(). Der erkannte Typ kommt aus der Pruefung oben und
    # kostet hier keinen zweiten Abruf.
    set_photo_headers(payload.object_key, erkannter_typ.get(payload.object_key))
    if payload.thumb_object_key:
        set_photo_headers(
            payload.thumb_object_key, erkannter_typ.get(payload.thumb_object_key)
        )

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


@router.put("/me/photos/order", response_model=MyProfileOut)
def reorder_photos(
    payload: ReorderPhotosRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reihenfolge der eigenen Fotos neu setzen (Drag & Drop im Profil).

    Position 0 ist das Hauptfoto - es trägt Swipe-Karte, Avatar und Chat-Kopf
    (siehe die order_by-Begründung an User.photos). Verlangt wird deshalb die
    vollständige Liste, nicht ein "verschiebe X vor Y": eine Teilangabe ließe
    offen, welche Position die nicht genannten Fotos bekommen, und das
    Hauptfoto würde je nach DB-Reihenfolge springen.
    """
    photos = db.query(Photo).filter(Photo.user_id == current_user.id).all()
    by_id = {photo.id: photo for photo in photos}

    if len(payload.photo_ids) != len(set(payload.photo_ids)):
        raise HTTPException(400, "Doppelte Foto-ID in der Reihenfolge.")
    # Vollzählig und ausschließlich eigene Fotos: sonst könnte eine
    # untergeschobene fremde ID die Zuordnung verschieben, und eine
    # unvollständige Liste würde Fotos ohne definierte Position zurücklassen.
    if set(payload.photo_ids) != set(by_id):
        raise HTTPException(400, "Die Reihenfolge muss genau die eigenen Fotos enthalten.")

    for index, photo_id in enumerate(payload.photo_ids):
        by_id[photo_id].position = index
    db.commit()
    db.refresh(current_user)
    return current_user


@router.patch("/me/notifications", response_model=MyProfileOut)
def update_notification_settings(
    payload: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Schalter unter "Benachrichtigungen" - je Anlass getrennt für E-Mail und App."""
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is not None:
            setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
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

    # Die Mindestanzahl gilt nicht nur beim Anlegen des Kontos: Ohne diese
    # Pruefung liesse sie sich unterlaufen, indem direkt nach der Registrierung
    # zwei der drei Fotos wieder verschwinden. Wer ein Foto austauschen will,
    # laedt zuerst das neue hoch (bis MAX_PHOTOS) und loescht dann das alte.
    # Ein abgelehntes Foto zaehlt nicht mit: Seine Datei ist bereits geloescht,
    # im Profil zeigt es niemand an. Es muss sich deshalb jederzeit entfernen
    # lassen - sonst saesse ein Nutzer mit drei Fotos, von denen eines
    # abgelehnt wurde, auf einem kaputten Bild fest.
    gueltige = (
        db.query(Photo)
        .filter(Photo.user_id == current_user.id, Photo.status != PhotoStatus.rejected)
        .count()
    )
    if photo.status != PhotoStatus.rejected and gueltige - 1 < MIN_PHOTOS:
        raise HTTPException(
            400,
            f"Mindestens {MIN_PHOTOS} Fotos sind erforderlich. "
            "Lade zuerst ein weiteres hoch.",
        )

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


# ---------- Zugangsdaten ----------


@router.post("/me/password", response_model=TokenResponse)
@limiter.limit("10/hour")
def change_password(
    request: Request,
    payload: PasswordChangeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Passwort aendern. Beendet alle anderen Sitzungen - der Aufrufer bekommt
    einen frischen Token zurueck und bleibt angemeldet."""
    from .. import password_reset
    from ..security import create_access_token, verify_password

    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(400, "Das aktuelle Passwort stimmt nicht.")
    if verify_password(payload.new_password, current_user.password_hash):
        raise HTTPException(400, "Das neue Passwort ist dasselbe wie das bisherige.")
    password_reset.set_new_password(db, current_user, payload.new_password)
    db.commit()
    background_tasks.add_task(
        mailer.send_password_changed, current_user.email, current_user.name, current_user.language
    )
    return TokenResponse(access_token=create_access_token(current_user.id))


@router.post("/me/email", response_model=MyProfileOut)
@limiter.limit("5/hour")
def change_email(
    request: Request,
    payload: EmailChangeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """E-Mail-Adresse aendern.

    Die neue Adresse ist erst bestaetigt, wenn der Link darin angeklickt ist;
    die alte bekommt einen Hinweis. Beides zusammen verhindert, dass ein
    Tippfehler oder eine Uebernahme unbemerkt bleibt.
    """
    from ..email_verification import TOKEN_TTL_HOURS, build_link, issue
    from ..safety_checks import is_disposable_email
    from ..security import verify_password

    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(400, "Falsches Passwort.")
    neu = payload.new_email
    if neu == current_user.email.lower():
        raise HTTPException(400, "Das ist bereits deine E-Mail-Adresse.")
    if is_disposable_email(neu):
        raise HTTPException(400, "Wegwerf-E-Mail-Adressen sind nicht erlaubt.")
    if db.query(User.id).filter(func.lower(User.email) == neu).first():
        raise HTTPException(409, "Diese E-Mail-Adresse ist bereits registriert.")

    alt = current_user.email
    current_user.email = neu
    current_user.email_verified_at = None
    db.commit()
    token = issue(db, current_user)
    background_tasks.add_task(
        mailer.send_verification_email,
        neu, current_user.name, build_link(token), TOKEN_TTL_HOURS, current_user.language,
    )
    background_tasks.add_task(
        mailer.send_email_changed, alt, current_user.name, neu, current_user.language
    )
    db.refresh(current_user)
    return current_user
