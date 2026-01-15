from typing import Optional, List
from pydantic import BaseModel, Field


class WorkspaceBase(BaseModel):
    """Base workspace schema."""
    name: str = Field(..., min_length=1, max_length=255)


class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a workspace."""
    is_organization: bool = False
    email_domains: Optional[List[str]] = None


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class WorkspaceResponse(BaseModel):
    """Workspace response schema."""
    gid: str
    resource_type: str = "workspace"
    name: str
    is_organization: bool = False
    email_domains: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class WorkspaceCompact(BaseModel):
    """Compact workspace representation."""
    gid: str
    resource_type: str = "workspace"
    name: str
    
    class Config:
        from_attributes = True


class AddUserRequest(BaseModel):
    """Request to add a user to a workspace."""
    user: str = Field(..., description="User GID to add")


class RemoveUserRequest(BaseModel):
    """Request to remove a user from a workspace."""
    user: str = Field(..., description="User GID to remove")


class WorkspaceMembershipResponse(BaseModel):
    """Workspace membership response."""
    gid: str
    resource_type: str = "workspace_membership"
    user: dict
    workspace: dict
    is_admin: bool = False
    is_active: bool = True
    is_guest: bool = False
    
    class Config:
        from_attributes = True

