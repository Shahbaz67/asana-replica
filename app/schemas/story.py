from typing import Optional
from pydantic import BaseModel, Field


class StoryBase(BaseModel):
    """Base story schema."""
    text: Optional[str] = None
    html_text: Optional[str] = None


class StoryCreate(StoryBase):
    """Schema for creating a story (comment)."""
    text: str = Field(..., min_length=1)
    is_pinned: bool = False
    sticker_name: Optional[str] = None


class StoryUpdate(BaseModel):
    """Schema for updating a story."""
    text: Optional[str] = None
    html_text: Optional[str] = None
    is_pinned: Optional[bool] = None


class StoryResponse(BaseModel):
    """Story response schema."""
    gid: str
    resource_type: str = "story"
    resource_subtype: str = "comment"
    text: Optional[str] = None
    html_text: Optional[str] = None
    is_pinned: bool = False
    is_edited: bool = False
    liked: bool = False
    num_likes: int = 0
    type: str = "comment"
    source: str = "api"
    created_at: Optional[str] = None
    created_by: Optional[dict] = None
    target: Optional[dict] = None
    sticker_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class StoryCompact(BaseModel):
    """Compact story representation."""
    gid: str
    resource_type: str = "story"
    resource_subtype: str = "comment"
    text: Optional[str] = None
    
    class Config:
        from_attributes = True

