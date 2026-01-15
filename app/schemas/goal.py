from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date


class MetricBase(BaseModel):
    """Base metric schema for goals."""
    metric_type: Optional[str] = Field(None, pattern="^(number|percent|currency)$")
    unit: Optional[str] = None
    precision: int = 0
    currency_code: Optional[str] = None
    initial_number_value: Optional[float] = None
    target_number_value: Optional[float] = None
    current_number_value: Optional[float] = None


class GoalBase(BaseModel):
    """Base goal schema."""
    name: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None
    html_notes: Optional[str] = None


class GoalCreate(GoalBase):
    """Schema for creating a goal."""
    workspace: str = Field(..., description="Workspace GID")
    team: Optional[str] = Field(None, description="Team GID")
    owner: Optional[str] = Field(None, description="Owner user GID")
    time_period: Optional[str] = Field(None, description="Time period GID")
    due_on: Optional[date] = None
    start_on: Optional[date] = None
    is_workspace_level: bool = False
    status: Optional[str] = Field(None, pattern="^(on_track|at_risk|off_track)$")
    metric: Optional[MetricBase] = None


class GoalUpdate(BaseModel):
    """Schema for updating a goal."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    notes: Optional[str] = None
    html_notes: Optional[str] = None
    due_on: Optional[date] = None
    start_on: Optional[date] = None
    owner: Optional[str] = None
    team: Optional[str] = None
    time_period: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(on_track|at_risk|off_track)$")
    liked: Optional[bool] = None


class GoalResponse(BaseModel):
    """Goal response schema."""
    gid: str
    resource_type: str = "goal"
    name: str
    notes: Optional[str] = None
    html_notes: Optional[str] = None
    due_on: Optional[str] = None
    start_on: Optional[str] = None
    status: Optional[str] = None
    is_workspace_level: bool = False
    liked: bool = False
    num_likes: int = 0
    workspace: Optional[dict] = None
    owner: Optional[dict] = None
    team: Optional[dict] = None
    time_period: Optional[dict] = None
    metric: Optional[dict] = None
    
    class Config:
        from_attributes = True


class GoalCompact(BaseModel):
    """Compact goal representation."""
    gid: str
    resource_type: str = "goal"
    name: str
    
    class Config:
        from_attributes = True


class GoalRelationshipCreate(BaseModel):
    """Schema for creating a goal relationship."""
    supporting_resource: str = Field(..., description="Supporting goal GID")
    contribution_weight: float = Field(default=1.0, ge=0, le=1)


class GoalRelationshipUpdate(BaseModel):
    """Schema for updating a goal relationship."""
    contribution_weight: Optional[float] = Field(None, ge=0, le=1)


class GoalRelationshipResponse(BaseModel):
    """Goal relationship response schema."""
    gid: str
    resource_type: str = "goal_relationship"
    supporting_goal: dict
    supported_goal: dict
    contribution_weight: float = 1.0
    
    class Config:
        from_attributes = True


class StatusUpdateBase(BaseModel):
    """Base status update schema."""
    title: str = Field(..., min_length=1, max_length=255)
    text: Optional[str] = None
    html_text: Optional[str] = None
    status_type: str = Field(default="on_track", pattern="^(on_track|at_risk|off_track|on_hold|complete)$")


class StatusUpdateCreate(StatusUpdateBase):
    """Schema for creating a status update."""
    parent: str = Field(..., description="Goal GID")


class StatusUpdateResponse(BaseModel):
    """Status update response schema."""
    gid: str
    resource_type: str = "status_update"
    resource_subtype: str = "status_update"
    title: str
    text: Optional[str] = None
    html_text: Optional[str] = None
    status_type: str = "on_track"
    created_at: Optional[str] = None
    author: Optional[dict] = None
    parent: Optional[dict] = None
    
    class Config:
        from_attributes = True


