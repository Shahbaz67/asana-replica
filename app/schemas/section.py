from typing import Optional
from pydantic import BaseModel, Field


class SectionBase(BaseModel):
    """Base section schema."""
    name: str = Field(..., min_length=1, max_length=255)


class SectionCreate(SectionBase):
    """Schema for creating a section."""
    project: str = Field(..., description="Project GID")
    insert_before: Optional[str] = Field(None, description="Section GID to insert before")
    insert_after: Optional[str] = Field(None, description="Section GID to insert after")


class SectionUpdate(BaseModel):
    """Schema for updating a section."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class SectionResponse(BaseModel):
    """Section response schema."""
    gid: str
    resource_type: str = "section"
    name: str
    project: Optional[dict] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class SectionCompact(BaseModel):
    """Compact section representation."""
    gid: str
    resource_type: str = "section"
    name: str
    
    class Config:
        from_attributes = True


class InsertSectionRequest(BaseModel):
    """Request to insert a section at a specific position."""
    project: str = Field(..., description="Project GID")
    before_section: Optional[str] = None
    after_section: Optional[str] = None


class AddTaskRequest(BaseModel):
    """Request to add a task to a section."""
    task: str = Field(..., description="Task GID")
    insert_before: Optional[str] = Field(None, description="Task GID to insert before")
    insert_after: Optional[str] = Field(None, description="Task GID to insert after")


