import uuid

import boto3
from botocore.client import Config as BotoConfig

from .config import settings

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


def public_url_for(object_key: str) -> str:
    return f"{settings.s3_public_base_url.rstrip('/')}/{object_key}"
