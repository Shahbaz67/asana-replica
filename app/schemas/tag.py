from typing import Optional
from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Base tag schema."""
    name: str = Field(..., min_length=1, max_length=255)
    color: Optional[str] = None
    notes: Optional[str] = None


class TagCreate(TagBase):
    """Schema for creating a tag."""
    workspace: str = Field(..., description="Workspace GID")


class TagUpdate(BaseModel):
    """Schema for updating a tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = None
    notes: Optional[str] = None


class TagResponse(BaseModel):
    """Tag response schema."""
    gid: str
    resource_type: str = "tag"
    name: str
    color: Optional[str] = None
    notes: Optional[str] = None
    workspace: Optional[dict] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class TagCompact(BaseModel):
    """Compact tag representation."""
    gid: str
    resource_type: str = "tag"
    name: str
    
    class Config:
        from_attributes = True

