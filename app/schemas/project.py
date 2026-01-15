from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None
    html_notes: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    workspace: str = Field(..., description="Workspace GID")
    team: Optional[str] = Field(None, description="Team GID")
    public: bool = False
    color: Optional[str] = None
    default_view: str = Field(default="list", pattern="^(list|board|calendar|timeline)$")
    due_on: Optional[date] = None
    start_on: Optional[date] = None
    owner: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    notes: Optional[str] = None
    html_notes: Optional[str] = None
    archived: Optional[bool] = None
    public: Optional[bool] = None
    color: Optional[str] = None
    default_view: Optional[str] = Field(None, pattern="^(list|board|calendar|timeline)$")
    due_on: Optional[date] = None
    due_at: Optional[datetime] = None
    start_on: Optional[date] = None
    completed: Optional[bool] = None
    owner: Optional[str] = None


class ProjectResponse(BaseModel):
    """Project response schema."""
    gid: str
    resource_type: str = "project"
    name: str
    notes: Optional[str] = None
    html_notes: Optional[str] = None
    archived: bool = False
    public: bool = False
    color: Optional[str] = None
    default_view: str = "list"
    due_on: Optional[str] = None
    due_at: Optional[str] = None
    start_on: Optional[str] = None
    completed: bool = False
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    workspace: Optional[dict] = None
    team: Optional[dict] = None
    owner: Optional[dict] = None
    
    class Config:
        from_attributes = True


class ProjectCompact(BaseModel):
    """Compact project representation."""
    gid: str
    resource_type: str = "project"
    name: str
    
    class Config:
        from_attributes = True


class ProjectDuplicateRequest(BaseModel):
    """Request to duplicate a project."""
    name: str = Field(..., min_length=1, max_length=255)
    team: Optional[str] = None
    include: Optional[List[str]] = Field(
        default=["members", "notes", "task_notes", "task_assignee", "task_subtasks", "task_attachments", "task_dates", "task_dependencies", "task_followers", "task_tags", "task_projects"]
    )
    schedule_dates: Optional[dict] = None


class AddMembersRequest(BaseModel):
    """Request to add members to a project."""
    members: str = Field(..., description="Comma-separated user GIDs")


class RemoveMembersRequest(BaseModel):
    """Request to remove members from a project."""
    members: str = Field(..., description="Comma-separated user GIDs")


class AddFollowersRequest(BaseModel):
    """Request to add followers to a project."""
    followers: str = Field(..., description="Comma-separated user GIDs")


class ProjectMembershipResponse(BaseModel):
    """Project membership response."""
    gid: str
    resource_type: str = "project_membership"
    user: dict
    project: dict
    access_level: str = "editor"
    write_access: str = "full_write"
    
    class Config:
        from_attributes = True


class TaskCountsResponse(BaseModel):
    """Task counts for a project."""
    num_tasks: int = 0
    num_completed_tasks: int = 0
    num_incomplete_tasks: int = 0
    num_milestones: int = 0
    num_completed_milestones: int = 0
    num_incomplete_milestones: int = 0


class ProjectStatusBase(BaseModel):
    """Base project status schema."""
    title: str = Field(..., min_length=1, max_length=255)
    text: Optional[str] = None
    html_text: Optional[str] = None
    color: str = Field(default="green", pattern="^(green|yellow|red|complete)$")


class ProjectStatusCreate(ProjectStatusBase):
    """Schema for creating a project status."""
    pass


class ProjectStatusResponse(BaseModel):
    """Project status response."""
    gid: str
    resource_type: str = "project_status"
    title: str
    text: Optional[str] = None
    html_text: Optional[str] = None
    color: str = "green"
    created_at: Optional[str] = None
    author: Optional[dict] = None
    
    class Config:
        from_attributes = True


class ProjectBriefBase(BaseModel):
    """Base project brief schema."""
    title: Optional[str] = None
    text: Optional[str] = None
    html_text: Optional[str] = None


class ProjectBriefCreate(ProjectBriefBase):
    """Schema for creating a project brief."""
    project: str = Field(..., description="Project GID")


class ProjectBriefUpdate(ProjectBriefBase):
    """Schema for updating a project brief."""
    pass


class ProjectBriefResponse(BaseModel):
    """Project brief response."""
    gid: str
    resource_type: str = "project_brief"
    title: Optional[str] = None
    text: Optional[str] = None
    html_text: Optional[str] = None
    project: Optional[dict] = None
    
    class Config:
        from_attributes = True

