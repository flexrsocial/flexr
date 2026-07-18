from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import GYM_CHOICES, Photo, PhotoStatus, User
from ..schemas import (
    AddPhotoRequest,
    LocationUpdateRequest,
    MyProfileOut,
    PresignPhotoRequest,
    PresignPhotoResponse,
    ProfileOut,
    UpdateProfileRequest,
)
from ..security import get_current_user
from ..storage import create_presigned_upload, public_url_for

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

    if "gym" in fields and fields["gym"] not in GYM_CHOICES:
        raise HTTPException(400, "Unbekanntes Gym.")

    for field, value in fields.items():
        if field == "bio" and value == "":
            value = None  # leere Bio = Bio entfernen
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/location", response_model=MyProfileOut)
def update_my_location(
    payload: LocationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Speichert die GPS-Position vom Gerät. Solange eine Position gespeichert
    ist, wird sie für die Umkreissuche verwendet (statt der PLZ-Koordinate)."""
    current_user.gps_lat = payload.lat
    current_user.gps_lon = payload.lon
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me/location", response_model=MyProfileOut)
def clear_my_location(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Entfernt die GPS-Position - die Umkreissuche fällt auf die PLZ zurück
    (wird vom Frontend aufgerufen, wenn Standortfreigabe fehlt/abgelehnt ist)."""
    current_user.gps_lat = None
    current_user.gps_lon = None
    db.commit()
    db.refresh(current_user)
    return current_user


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
    if existing_count >= 5:
        raise HTTPException(400, "Maximal 5 Fotos erlaubt.")

    result = create_presigned_upload(current_user.id, payload.content_type)
    return PresignPhotoResponse(**result)


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
    if existing_count >= 5:
        raise HTTPException(400, "Maximal 5 Fotos erlaubt.")

    photo = Photo(
        user_id=current_user.id,
        url=public_url_for(payload.object_key),
        thumb_url=public_url_for(payload.thumb_object_key) if payload.thumb_object_key else None,
        position=existing_count,
    )
    db.add(photo)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me/photos/{photo_id}", response_model=MyProfileOut)
def delete_photo(
    photo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    photo = (
        db.query(Photo)
        .filter(Photo.id == photo_id, Photo.user_id == current_user.id)
        .first()
    )
    if not photo:
        raise HTTPException(404, "Foto nicht gefunden.")
    db.delete(photo)
    db.commit()
    db.refresh(current_user)
    return current_user
