from typing import Optional
from pydantic import BaseModel, Field


class AttachmentCreate(BaseModel):
    """Schema for creating an attachment (external URL)."""
    parent: str = Field(..., description="Parent task GID")
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., description="URL to the attachment")
    resource_subtype: str = Field(default="external", pattern="^(asana|external|dropbox|gdrive|onedrive|box|vimeo)$")


class AttachmentResponse(BaseModel):
    """Attachment response schema."""
    gid: str
    resource_type: str = "attachment"
    resource_subtype: str = "asana"
    name: str
    host: str = "asana"
    download_url: Optional[str] = None
    view_url: Optional[str] = None
    permanent_url: Optional[str] = None
    size: Optional[int] = None
    created_at: Optional[str] = None
    parent: Optional[dict] = None
    connected_to_app: bool = False
    
    class Config:
        from_attributes = True


class AttachmentCompact(BaseModel):
    """Compact attachment representation."""
    gid: str
    resource_type: str = "attachment"
    name: str
    
    class Config:
        from_attributes = True

