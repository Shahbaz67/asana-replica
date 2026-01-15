from typing import Optional
from pydantic import BaseModel, Field


class TeamBase(BaseModel):
    """Base team schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    html_description: Optional[str] = None


class TeamCreate(TeamBase):
    """Schema for creating a team."""
    organization: str = Field(..., description="Workspace/Organization GID")
    visibility: str = Field(default="members", pattern="^(public|members|secret)$")


class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    html_description: Optional[str] = None
    visibility: Optional[str] = Field(None, pattern="^(public|members|secret)$")


class TeamResponse(BaseModel):
    """Team response schema."""
    gid: str
    resource_type: str = "team"
    name: str
    description: Optional[str] = None
    html_description: Optional[str] = None
    visibility: str = "members"
    organization: Optional[dict] = None
    
    class Config:
        from_attributes = True


class TeamCompact(BaseModel):
    """Compact team representation."""
    gid: str
    resource_type: str = "team"
    name: str
    
    class Config:
        from_attributes = True


class AddUserToTeamRequest(BaseModel):
    """Request to add a user to a team."""
    user: str = Field(..., description="User GID to add")


class TeamMembershipResponse(BaseModel):
    """Team membership response."""
    gid: str
    resource_type: str = "team_membership"
    user: dict
    team: dict
    is_admin: bool = False
    is_guest: bool = False
    is_limited_access: bool = False
    
    class Config:
        from_attributes = True

