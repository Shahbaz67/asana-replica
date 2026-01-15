from typing import Optional, List
from pydantic import BaseModel, Field


class PortfolioBase(BaseModel):
    """Base portfolio schema."""
    name: str = Field(..., min_length=1, max_length=255)
    color: Optional[str] = None
    public: bool = False


class PortfolioCreate(PortfolioBase):
    """Schema for creating a portfolio."""
    workspace: str = Field(..., description="Workspace GID")
    members: Optional[List[str]] = None


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = None
    public: Optional[bool] = None


class PortfolioResponse(BaseModel):
    """Portfolio response schema."""
    gid: str
    resource_type: str = "portfolio"
    name: str
    color: Optional[str] = None
    public: bool = False
    workspace: Optional[dict] = None
    owner: Optional[dict] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class PortfolioCompact(BaseModel):
    """Compact portfolio representation."""
    gid: str
    resource_type: str = "portfolio"
    name: str
    
    class Config:
        from_attributes = True


class AddItemRequest(BaseModel):
    """Request to add an item to a portfolio."""
    item: str = Field(..., description="Project GID")
    insert_before: Optional[str] = None
    insert_after: Optional[str] = None


class RemoveItemRequest(BaseModel):
    """Request to remove an item from a portfolio."""
    item: str = Field(..., description="Project GID")


class AddMembersRequest(BaseModel):
    """Request to add members to a portfolio."""
    members: str = Field(..., description="Comma-separated user GIDs")


class RemoveMembersRequest(BaseModel):
    """Request to remove members from a portfolio."""
    members: str = Field(..., description="Comma-separated user GIDs")


class PortfolioMembershipResponse(BaseModel):
    """Portfolio membership response schema."""
    gid: str
    resource_type: str = "portfolio_membership"
    portfolio: dict
    user: dict
    access_level: str = "editor"
    
    class Config:
        from_attributes = True


