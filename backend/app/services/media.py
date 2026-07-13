"""Media upload signed-URL stub (MinIO presign when boto available)."""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)


class MediaService:
    """Return a deterministic upload URL. Real MinIO presign if boto3 is importable."""

    def create_upload_url(
        self,
        *,
        filename: str,
        content_type: str = "application/octet-stream",
        owner_id: uuid.UUID | None = None,
    ) -> dict:
        safe_name = (filename or "upload.bin").replace("/", "_").replace("\\", "_")
        key = f"uploads/{owner_id or 'anon'}/{uuid.uuid4().hex[:12]}_{safe_name}"
        digest = hashlib.sha256(f"{key}:{content_type}".encode()).hexdigest()[:16]

        presigned = self._try_minio_presign(key, content_type)
        if presigned:
            return {
                "upload_url": presigned,
                "asset_url": f"{settings.s3_endpoint.rstrip('/')}/{settings.s3_bucket}/{key}",
                "key": key,
                "expires_in": 3600,
                "content_type": content_type,
            }

        stub = f"https://example.invalid/orchestra/{key}?sig={digest}"
        return {
            "upload_url": stub,
            "asset_url": stub,
            "key": key,
            "expires_in": 3600,
            "content_type": content_type,
            "stub": True,
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }

    def _try_minio_presign(self, key: str, content_type: str) -> str | None:
        try:
            import boto3
            from botocore.client import Config
        except ImportError:
            return None

        try:
            client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                config=Config(signature_version="s3v4"),
                region_name="us-east-1",
            )
            return client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.s3_bucket,
                    "Key": key,
                    "ContentType": content_type,
                },
                ExpiresIn=3600,
            )
        except Exception as exc:  # noqa: BLE001
            logger.info("MinIO presign unavailable, using stub: %s", exc)
            return None
