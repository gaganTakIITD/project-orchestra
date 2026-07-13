"""Signed upload URL stub."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.models.identity import User
from app.services.auth import get_current_client
from app.services.media import MediaService

router = APIRouter(prefix="/media", tags=["media"])


class UploadUrlIn(BaseModel):
    filename: str = Field(min_length=1)
    content_type: str = "application/octet-stream"


class UploadUrlOut(BaseModel):
    upload_url: str
    asset_url: str
    key: str
    expires_in: int = 3600
    content_type: str = "application/octet-stream"
    stub: bool | None = None


@router.post("/upload-url", response_model=UploadUrlOut)
async def create_upload_url(
    body: UploadUrlIn,
    user: User = Depends(get_current_client),
) -> UploadUrlOut:
    result = MediaService().create_upload_url(
        filename=body.filename,
        content_type=body.content_type,
        owner_id=user.id,
    )
    return UploadUrlOut(**{k: v for k, v in result.items() if k in UploadUrlOut.model_fields})
