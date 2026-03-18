from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional


class EmailEntry(BaseModel):
    """Pydantic model for a submitted email entry."""
    email: EmailStr
    phone: Optional[str] = ""
    title: Optional[str] = ""
    message: Optional[str] = ""
    created_at: Optional[str] = None

    @field_validator("phone", "title", "message", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip() if isinstance(v, str) else v


class EmailEntryCreate(BaseModel):
    """Model used for incoming form data (before timestamp is added)."""
    email: EmailStr
    phone: Optional[str] = ""
    title: Optional[str] = ""
    message: Optional[str] = ""

    @field_validator("phone", "title", "message", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        return v.strip() if isinstance(v, str) else v
