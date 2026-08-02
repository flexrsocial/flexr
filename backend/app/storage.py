import logging
import uuid

import boto3
from botocore.client import Config as BotoConfig

from .config import settings

logger = logging.getLogger(__name__)

CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
        config=BotoConfig(signature_version="s3v4"),
    )


def create_presigned_upload(user_id: str, content_type: str) -> dict:
    """Erzeugt eine Presigned-PUT-URL, gegen die der Client direkt hochladen kann.
    object_key ist mit der user_id ge-prefixed, damit register_photo() den Key
    später eindeutig dem Nutzer zuordnen und verifizieren kann."""
    ext = CONTENT_TYPE_EXTENSIONS[content_type]
    object_key = f"users/{user_id}/{uuid.uuid4()}.{ext}"

    client = get_s3_client()
    upload_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket_name,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=300,
    )
    return {"upload_url": upload_url, "object_key": object_key}


def create_presigned_verification_upload(user_id: str, content_type: str) -> dict:
    """Presigned-PUT-URL für Verifizierungs-Selfies - eigener verify/-Unterpfad,
    damit die Keys klar von Profilfotos getrennt sind."""
    ext = CONTENT_TYPE_EXTENSIONS[content_type]
    object_key = f"users/{user_id}/verify/{uuid.uuid4()}.{ext}"

    client = get_s3_client()
    upload_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket_name,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=300,
    )
    return {"upload_url": upload_url, "object_key": object_key}


PHOTO_CACHE_CONTROL = "public, max-age=31536000, immutable"


def set_photo_cache_control(object_key: str) -> None:
    """Setzt Cache-Control auf ein bereits hochgeladenes Objekt.

    Der Upload läuft als Presigned PUT direkt vom Client zum Storage; ein
    Cache-Control-Header müsste dafür mitsigniert *und* von jedem Client exakt
    so mitgeschickt werden, sonst schlägt die Signatur fehl. Deshalb wird der
    Header hier nachträglich per Copy-auf-sich-selbst gesetzt - der
    Upload-Vertrag bleibt für Web und App unverändert.

    Ohne den Header liefert R2 gar kein Cache-Control. Clients fallen dann auf
    heuristisches Caching zurück, das sich am Alter des Objekts bemisst - bei
    einem gerade hochgeladenen Foto also praktisch null. Jede Anzeige wird zum
    Netz-Roundtrip, und bei wackligem Empfang bleibt das Bild schlicht leer.
    Die Objektschlüssel sind UUIDs und werden nie überschrieben, „immutable"
    ist deshalb korrekt.

    Fehler werden geschluckt: ein fehlender Cache-Header darf einen sonst
    erfolgreichen Upload nicht scheitern lassen.
    """
    try:
        client = get_s3_client()
        client.copy_object(
            Bucket=settings.s3_bucket_name,
            Key=object_key,
            CopySource={"Bucket": settings.s3_bucket_name, "Key": object_key},
            CacheControl=PHOTO_CACHE_CONTROL,
            MetadataDirective="REPLACE",
        )
    except Exception:  # noqa: BLE001 - bewusst breit, siehe Docstring
        logger.warning("Cache-Control konnte nicht gesetzt werden: %s", object_key, exc_info=True)


def delete_object(object_key: str) -> None:
    """Löscht ein Objekt aus dem Storage (Selfies nach Abschluss der Prüfung)."""
    client = get_s3_client()
    client.delete_object(Bucket=settings.s3_bucket_name, Key=object_key)


def public_url_for(object_key: str) -> str:
    return f"{settings.s3_public_base_url.rstrip('/')}/{object_key}"
