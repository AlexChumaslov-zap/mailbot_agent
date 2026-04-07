from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional, List


class EmailEntry(BaseModel):
    """Pydantic model for a submitted email entry."""
    email: EmailStr
    title: Optional[str] = ""
    message: Optional[str] = ""
    created_at: Optional[str] = None

    @field_validator("title", "message", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip() if isinstance(v, str) else v


class EmailEntryCreate(BaseModel):
    """Model used for incoming form data (before timestamp is added)."""
    email: EmailStr
    title: Optional[str] = ""
    message: Optional[str] = ""

    @field_validator("title", "message", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip() if isinstance(v, str) else v


# --- RFI Email models ---

class AttachmentCreate(BaseModel):
    """Incoming attachment data (before storage)."""
    filename: str
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    s3_key: Optional[str] = None


class Attachment(AttachmentCreate):
    """Stored attachment with database fields."""
    id: int
    rfi_email_id: int
    uploaded_at: str


class RfiEmailCreate(BaseModel):
    """Incoming RFI email data (before storage)."""
    message_id: Optional[str] = None
    sender: str
    subject: str
    body: Optional[str] = None
    email_date: str
    attachments: List[AttachmentCreate] = []


class RfiEmail(BaseModel):
    """Stored RFI email with database fields."""
    id: int
    message_id: Optional[str] = None
    sender: str
    subject: str
    body: Optional[str] = None
    email_date: str
    received_at: str
    is_read: bool = False
    attachments: List[Attachment] = []
