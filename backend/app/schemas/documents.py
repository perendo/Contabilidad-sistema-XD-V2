from pydantic import BaseModel, ConfigDict

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/xml",
    "text/xml",
}


class AttachmentOut(BaseModel):
    id: int
    entry_id: int
    filename: str
    content_type: str
    size: int

    model_config = ConfigDict(from_attributes=True)
