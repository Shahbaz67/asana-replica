from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class PhotoUrls(BaseModel):
    """User photo URLs at various sizes."""
    image_21x21: Optional[str] = None
    image_27x27: Optional[str] = None
    image_36x36: Optional[str] = None
    image_60x60: Optional[str] = None
    image_128x128: Optional[str] = None


class UserBase(BaseModel):
    """Base user schema."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user."""


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    photo: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema."""
    gid: str
    resource_type: str = "user"
    name: str
    email: Optional[str] = None
    photo: Optional[PhotoUrls] = None
    
    class Config:
        from_attributes = True


class UserCompact(BaseModel):
    """Compact user representation."""
    gid: str
    resource_type: str = "user"
    name: str
    
    class Config:
        from_attributes = True



