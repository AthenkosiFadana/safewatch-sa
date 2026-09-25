"""Amazon S3 evidence/image storage helper.

Incident photos are uploaded by the frontend to a presigned S3 URL and the
resulting https URL is stored on the incident record.
"""

import logging

from app.config import Config

logger = logging.getLogger("safewatch.storage")

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_MB = 5


def create_presigned_upload(filename: str, content_type: str, expires: int = 300):
    """Return a presigned PUT URL so the browser uploads straight to S3."""
    if not Config.S3_BUCKET:
        return None
    if content_type not in ALLOWED_TYPES:
        raise ValueError("Only JPEG, PNG or WebP images are accepted")
    import boto3

    s3 = boto3.client("s3", region_name=Config.AWS_REGION)
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": Config.S3_BUCKET, "Key": f"incidents/{filename}", "ContentType": content_type},
        ExpiresIn=expires,
    )


def public_url(filename: str) -> str:
    if not Config.S3_BUCKET:
        return ""
    return f"https://{Config.S3_BUCKET}.s3.amazonaws.com/incidents/{filename}"
