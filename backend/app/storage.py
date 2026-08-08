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


# ---------- Ausweisdokumente (hochsensibel, nur temporär) ----------

# Eigener privater Prefix. Er liegt bewusst NICHT unter users/ - alles unter
# users/ ist über S3_PUBLIC_BASE_URL öffentlich abrufbar. Ausweisaufnahmen
# bekommen nie eine öffentliche URL, sondern nur kurzlebige Signed URLs für
# angemeldete Admins.
VERIFICATION_DOCUMENT_PREFIX = "verification-documents/"

# Obergrenze pro Aufnahme. Handykameras liefern komprimiert deutlich weniger;
# alles darüber ist entweder ein Fehler oder ein Missbrauchsversuch.
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024

# Gültigkeitsdauer der Signed URLs, mit denen der Admin die Aufnahmen ansieht.
# Kurz genug, dass ein kopierter Link praktisch wertlos ist.
DOCUMENT_VIEW_URL_TTL_SECONDS = 60

# Magic Bytes der zugelassenen Formate. Ein Client kann den Content-Type frei
# behaupten - geprüft wird deshalb der tatsächliche Dateianfang.
_MAGIC_BYTES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
}


def document_object_key(request_id: str, content_type: str) -> str:
    """Zufälliger Objektschlüssel für eine Ausweisaufnahme.

    Bewusst ohne Name, Geburtsdatum oder E-Mail im Pfad - der Schlüssel selbst
    darf nichts über die Person verraten. Die Zuordnung passiert über die ID
    des Verifizierungsvorgangs, die ebenfalls eine UUID ist.
    """
    ext = CONTENT_TYPE_EXTENSIONS[content_type]
    return f"{VERIFICATION_DOCUMENT_PREFIX}{request_id}/{uuid.uuid4()}.{ext}"


def create_presigned_document_upload(request_id: str, content_type: str) -> dict:
    """Presigned-PUT-URL für eine Ausweisaufnahme im privaten Prefix."""
    object_key = document_object_key(request_id, content_type)

    client = get_s3_client()
    upload_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket_name,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=180,
    )
    return {"upload_url": upload_url, "object_key": object_key}


def create_presigned_view_url(object_key: str, expires_in: int = DOCUMENT_VIEW_URL_TTL_SECONDS) -> str:
    """Kurzlebige Signed-GET-URL. Wird nur an authentifizierte Admins ausgegeben."""
    client = get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket_name, "Key": object_key},
        ExpiresIn=expires_in,
    )


def inspect_uploaded_image(object_key: str) -> dict:
    """Serverseitige Prüfung eines frisch hochgeladenen Bildes.

    Der Upload läuft am Backend vorbei direkt in den Storage - Größe und Format
    lassen sich deshalb erst danach kontrollieren. Geprüft wird die tatsächliche
    Objektgröße und der echte Dateianfang (Magic Bytes), nicht der vom Client
    behauptete Content-Type.

    Liefert ``{"ok": bool, "size": int, "detected": str|None}``.
    """
    client = get_s3_client()
    head = client.head_object(Bucket=settings.s3_bucket_name, Key=object_key)
    size = int(head.get("ContentLength", 0))
    if size <= 0 or size > MAX_DOCUMENT_BYTES:
        return {"ok": False, "size": size, "detected": None}

    body = client.get_object(
        Bucket=settings.s3_bucket_name, Key=object_key, Range="bytes=0-15"
    )["Body"].read()
    detected = _sniff_image_type(body)
    return {"ok": detected is not None, "size": size, "detected": detected}


def _sniff_image_type(head_bytes: bytes) -> str | None:
    for content_type, signatures in _MAGIC_BYTES.items():
        if any(head_bytes.startswith(sig) for sig in signatures):
            return content_type
    # WebP: "RIFF" + 4 Byte Länge + "WEBP"
    if head_bytes[:4] == b"RIFF" and head_bytes[8:12] == b"WEBP":
        return "image/webp"
    return None


def delete_objects_verified(object_keys: list[str]) -> list[str]:
    """Löscht Objekte und prüft, ob sie danach wirklich weg sind.

    Gibt die Schlüssel zurück, die weiterhin existieren bzw. deren Löschung
    nicht bestätigt werden konnte. Ein nicht leeres Ergebnis bedeutet: Der
    Vorgang darf NICHT als abgeschlossen gelten (siehe
    VerificationRequest.cleanup_pending).

    Es werden bewusst nur Objektschlüssel geloggt, nie Inhalte.
    """
    remaining: list[str] = []
    if not object_keys:
        return remaining
    if not settings.s3_bucket_name:
        # Ohne konfigurierten Bucket gibt es nichts zu löschen (Entwicklung/Test)
        return remaining

    client = get_s3_client()
    for key in object_keys:
        try:
            client.delete_object(Bucket=settings.s3_bucket_name, Key=key)
        except Exception:
            logger.warning("Löschen fehlgeschlagen: %s", key)
            remaining.append(key)
            continue
        try:
            client.head_object(Bucket=settings.s3_bucket_name, Key=key)
        except Exception:
            continue  # nicht mehr auffindbar = gelöscht
        logger.warning("Objekt nach dem Löschen weiterhin vorhanden: %s", key)
        remaining.append(key)
    return remaining


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
