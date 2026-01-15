from typing import Optional, List, Any
from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime


class TaskBase(BaseModel):
    """Base task schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    notes: Optional[str] = None
    html_notes: Optional[str] = None


class TaskCreate(TaskBase):
    """Schema for creating a task.
    
    Based on: https://developers.asana.com/reference/createtask
    Total: 23 body parameters
    """
    # Location/context (3)
    workspace: Optional[str] = Field(None, description="Workspace GID")
    projects: Optional[List[str]] = Field(None, description="List of project GIDs")
    parent: Optional[str] = Field(None, description="Parent task GID for subtasks")
    
    # Assignment (2)
    assignee: Optional[str] = Field(None, description="Assignee user GID or email")
    assignee_section: Optional[str] = Field(None, description="Section GID in assignee's My Tasks")
    
    # Dates (4)
    due_on: Optional[date] = None
    due_at: Optional[datetime] = None
    start_on: Optional[date] = None
    start_at: Optional[datetime] = None
    
    # Task type/status (4)
    resource_subtype: str = Field(default="default_task", pattern="^(default_task|milestone|section|approval)$")
    approval_status: Optional[str] = Field(None, pattern="^(pending|approved|rejected|changes_requested)$")
    custom_type: Optional[str] = Field(None, description="GID of a custom task type")
    custom_type_status_option: Optional[str] = Field(None, description="Option GID for custom type's status")
    
    # Associations (2)
    tags: Optional[List[str]] = None
    followers: Optional[List[str]] = None
    
    # State (3)
    completed: Optional[bool] = Field(None, description="Whether the task is completed")
    liked: Optional[bool] = Field(None, description="Whether the current user likes the task")
    is_rendered_as_separator: Optional[bool] = Field(None, description="For board/list rendering")
    
    # Data (2)
    custom_fields: Optional[dict] = Field(None, description="Custom field values keyed by GID")
    external: Optional[dict] = Field(None, description="External data for integrations")
    
    @model_validator(mode='after')
    def validate_workspace_parent_or_projects(self):
        """Validate that at least one of workspace, parent, or projects is provided."""
        if not self.workspace and not self.parent and not self.projects:
            raise ValueError("You should specify one of workspace, parent, projects")
        return self


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    notes: Optional[str] = None
    html_notes: Optional[str] = None
    completed: Optional[bool] = None
    assignee: Optional[str] = None
    due_on: Optional[date] = None
    due_at: Optional[datetime] = None
    start_on: Optional[date] = None
    start_at: Optional[datetime] = None
    liked: Optional[bool] = None
    approval_status: Optional[str] = Field(None, pattern="^(pending|approved|rejected|changes_requested)$")


class TaskResponse(BaseModel):
    """Task response schema.
    
    Based on: https://developers.asana.com/reference/createtask
    """
    gid: str
    resource_type: str = "task"
    resource_subtype: str = "default_task"
    name: str
    notes: Optional[str] = None
    html_notes: Optional[str] = None
    completed: bool = False
    completed_at: Optional[str] = None
    completed_by: Optional[dict] = None
    due_on: Optional[str] = None
    due_at: Optional[str] = None
    start_on: Optional[str] = None
    start_at: Optional[str] = None
    liked: bool = False
    num_likes: int = 0
    num_subtasks: int = 0
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    assignee: Optional[dict] = None
    assignee_section: Optional[dict] = None
    parent: Optional[dict] = None
    projects: Optional[List[dict]] = None
    memberships: Optional[List[dict]] = None
    tags: Optional[List[dict]] = None
    followers: Optional[List[dict]] = None
    workspace: Optional[dict] = None
    dependencies: Optional[List[dict]] = None
    dependents: Optional[List[dict]] = None
    approval_status: Optional[str] = None
    permalink_url: Optional[str] = None
    custom_fields: Optional[List[dict]] = None
    external: Optional[dict] = None
    actual_time_minutes: Optional[int] = None
    is_rendered_as_separator: bool = False
    
    class Config:
        from_attributes = True


class TaskCompact(BaseModel):
    """Compact task representation."""
    gid: str
    resource_type: str = "task"
    name: str
    resource_subtype: str = "default_task"
    
    class Config:
        from_attributes = True


class TaskDuplicateRequest(BaseModel):
    """Request to duplicate a task."""
    name: str = Field(..., min_length=1, max_length=255)
    include: Optional[List[str]] = Field(
        default=["notes", "assignee", "subtasks", "attachments", "tags", "followers", "projects", "dates", "dependencies", "parent"]
    )


class SetParentRequest(BaseModel):
    """Request to set a task's parent."""
    parent: str = Field(..., description="Parent task GID")
    insert_before: Optional[str] = None
    insert_after: Optional[str] = None


class AddProjectRequest(BaseModel):
    """Request to add a task to a project."""
    project: str = Field(..., description="Project GID")
    section: Optional[str] = Field(None, description="Section GID")
    insert_before: Optional[str] = None
    insert_after: Optional[str] = None


class RemoveProjectRequest(BaseModel):
    """Request to remove a task from a project."""
    project: str = Field(..., description="Project GID")


class AddTagRequest(BaseModel):
    """Request to add a tag to a task."""
    tag: str = Field(..., description="Tag GID")


class RemoveTagRequest(BaseModel):
    """Request to remove a tag from a task."""
    tag: str = Field(..., description="Tag GID")


class AddFollowersRequest(BaseModel):
    """Request to add followers to a task."""
    followers: str = Field(..., description="Comma-separated user GIDs")


class RemoveFollowersRequest(BaseModel):
    """Request to remove followers from a task."""
    followers: str = Field(..., description="Comma-separated user GIDs")


class AddDependenciesRequest(BaseModel):
    """Request to add dependencies to a task."""
    dependencies: str = Field(..., description="Comma-separated task GIDs")


class RemoveDependenciesRequest(BaseModel):
    """Request to remove dependencies from a task."""
    dependencies: str = Field(..., description="Comma-separated task GIDs")


class AddDependentsRequest(BaseModel):
    """Request to add dependents to a task."""
    dependents: str = Field(..., description="Comma-separated task GIDs")


class RemoveDependentsRequest(BaseModel):
    """Request to remove dependents from a task."""
    dependents: str = Field(..., description="Comma-separated task GIDs")


class TaskSearchRequest(BaseModel):
    """Task search request parameters."""
    workspace: str = Field(..., description="Workspace GID")
    text: Optional[str] = None
    assignee_any: Optional[str] = None
    assignee_not: Optional[str] = None
    projects_any: Optional[str] = None
    projects_not: Optional[str] = None
    projects_all: Optional[str] = None
    sections_any: Optional[str] = None
    sections_not: Optional[str] = None
    sections_all: Optional[str] = None
    tags_any: Optional[str] = None
    tags_not: Optional[str] = None
    tags_all: Optional[str] = None
    completed: Optional[bool] = None
    is_subtask: Optional[bool] = None
    has_attachment: Optional[bool] = None
    due_on: Optional[date] = None
    due_on_before: Optional[date] = None
    due_on_after: Optional[date] = None
    start_on: Optional[date] = None
    start_on_before: Optional[date] = None
    start_on_after: Optional[date] = None
    created_on: Optional[date] = None
    created_on_before: Optional[date] = None
    created_on_after: Optional[date] = None
    modified_on: Optional[date] = None
    modified_on_before: Optional[date] = None
    modified_on_after: Optional[date] = None
    completed_on: Optional[date] = None
    completed_on_before: Optional[date] = None
    completed_on_after: Optional[date] = None
    sort_by: str = Field(default="modified_at", pattern="^(due_date|created_at|completed_at|likes|modified_at)$")
    sort_ascending: bool = False


