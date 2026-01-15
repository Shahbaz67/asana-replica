"""
Project schemas based on Asana API Reference.

Reference: https://developers.asana.com/reference/projects
         https://developers.asana.com/reference/createproject
"""
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import date


# =============================================================================
# COLOR ENUM VALUES (from Asana API)
# =============================================================================
# Valid colors: dark-pink, dark-green, dark-blue, dark-red, dark-teal,
# dark-brown, dark-orange, dark-purple, dark-warm-gray, light-pink,
# light-green, light-blue, light-red, light-teal, light-brown,
# light-orange, light-purple, light-warm-gray, none


# =============================================================================
# BASE SCHEMAS
# =============================================================================

class ProjectBase(BaseModel):
    """Base project schema with common writable fields."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Name of the project")
    notes: Optional[str] = Field(None, description="Free-form textual description of the project")
    html_notes: Optional[str] = Field(None, description="HTML formatted notes for the project")


# =============================================================================
# CREATE PROJECT SCHEMA (17 body parameters)
# =============================================================================

class ProjectCreate(ProjectBase):
    """Schema for creating a project.
    
    Based on: https://developers.asana.com/reference/createproject
    
    Total body parameters: 22 (extracted from live API docs)
    - Required: name, workspace (or team for organizations)
    """
    # Required field
    name: str = Field(..., min_length=1, max_length=255, description="Name of the project")
    
    # Location/context (2)
    workspace: Optional[str] = Field(None, description="Workspace GID. Required if team is not specified")
    team: Optional[str] = Field(None, description="Team GID. Required for projects in organizations")
    
    # Privacy (2)
    public: Optional[bool] = Field(None, description="DEPRECATED: Use privacy_setting instead")
    privacy_setting: Optional[str] = Field(
        None,
        pattern="^(public_to_workspace|private_to_team|private)$",
        description="Privacy setting: public_to_workspace, private_to_team, or private"
    )
    
    # Display (3)
    color: Optional[str] = Field(
        None,
        description="Color of the project (e.g., dark-pink, light-green, none)"
    )
    default_view: Optional[str] = Field(
        None,
        pattern="^(list|board|calendar|timeline)$",
        description="Default view: list, board, calendar, or timeline"
    )
    icon: Optional[str] = Field(
        None,
        description="Icon for the project (e.g., list, board, timeline, calendar, rocket, etc.)"
    )
    
    # Dates (3 - including deprecated)
    start_on: Optional[date] = Field(None, description="Start date in YYYY-MM-DD format")
    due_on: Optional[date] = Field(None, description="Due date in YYYY-MM-DD format")
    due_date: Optional[date] = Field(None, description="DEPRECATED: Use due_on instead")
    
    # State (2)
    archived: Optional[bool] = Field(None, description="Whether the project is archived")
    current_status_update: Optional[str] = Field(None, description="Status update GID to set as current")
    
    # Assignment (2)
    owner: Optional[str] = Field(None, description="Owner user GID")
    followers: Optional[str] = Field(None, description="Comma-separated user GIDs (Create-only)")
    
    # Access control (3)
    default_access_level: Optional[str] = Field(
        None,
        pattern="^(admin|editor|commenter|viewer)$",
        description="Default access for users who join: admin, editor, commenter, viewer"
    )
    minimum_access_level_for_customization: Optional[str] = Field(
        None,
        pattern="^(admin|editor)$",
        description="Minimum access to modify workflow: admin or editor"
    )
    minimum_access_level_for_sharing: Optional[str] = Field(
        None,
        pattern="^(admin|editor)$",
        description="Minimum access to share and manage memberships: admin or editor"
    )
    
    # Custom data (1)
    custom_fields: Optional[dict] = Field(
        None,
        description="Custom field values as {custom_field_gid: value}"
    )


# =============================================================================
# UPDATE PROJECT SCHEMA (15 body parameters)
# =============================================================================

class ProjectUpdate(BaseModel):
    """Schema for updating a project.
    
    Based on: https://developers.asana.com/reference/updateproject
    
    Note: workspace and team cannot be changed after creation
    """
    # Content (3)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    notes: Optional[str] = None
    html_notes: Optional[str] = None
    
    # State (2)
    archived: Optional[bool] = Field(None, description="Whether the project is archived")
    completed: Optional[bool] = Field(None, description="Whether the project is complete")
    
    # Privacy (2)
    public: Optional[bool] = Field(None, description="DEPRECATED: Use privacy_setting")
    privacy_setting: Optional[str] = Field(
        None,
        pattern="^(public_to_workspace|private_to_team|private)$"
    )
    
    # Display (3)
    color: Optional[str] = None
    default_view: Optional[str] = Field(None, pattern="^(list|board|calendar|timeline)$")
    icon: Optional[str] = None
    
    # Dates (2)
    start_on: Optional[date] = None
    due_on: Optional[date] = None
    
    # Assignment (2)
    owner: Optional[str] = None
    current_status_update: Optional[str] = Field(None, description="Status update GID to set as current")
    
    # Access control (3)
    default_access_level: Optional[str] = Field(
        None,
        pattern="^(admin|editor|commenter|viewer)$",
        description="Default access for users who join: admin, editor, commenter, viewer"
    )
    minimum_access_level_for_customization: Optional[str] = Field(
        None,
        pattern="^(admin|editor)$",
        description="Minimum access to modify workflow: admin or editor"
    )
    minimum_access_level_for_sharing: Optional[str] = Field(
        None,
        pattern="^(admin|editor)$",
        description="Minimum access to share and manage memberships: admin or editor"
    )
    
    # Custom data (1)
    custom_fields: Optional[dict] = None


# =============================================================================
# COMPACT/NESTED RESPONSE SCHEMAS
# Based on: https://developers.asana.com/reference/getproject (200 response)
# =============================================================================

class UserCompact(BaseModel):
    """Compact user schema for nested responses."""
    gid: str
    resource_type: str = "user"
    name: str


class WorkspaceCompact(BaseModel):
    """Compact workspace schema for nested responses."""
    gid: str
    resource_type: str = "workspace"
    name: str


class TeamCompact(BaseModel):
    """Compact team schema for nested responses."""
    gid: str
    resource_type: str = "team"
    name: str


class ProjectTemplateCompact(BaseModel):
    """Compact project template schema for nested responses."""
    gid: str
    resource_type: str = "project_template"
    name: str


class ProjectBriefCompact(BaseModel):
    """Compact project brief schema for nested responses."""
    gid: str
    resource_type: str = "project_brief"


class EnumOptionCompact(BaseModel):
    """Compact enum option schema for custom fields."""
    gid: str
    resource_type: str = "enum_option"
    name: str
    enabled: bool = True
    color: Optional[str] = None


class DateValue(BaseModel):
    """Date value schema for custom field date values."""
    date: Optional[str] = None
    date_time: Optional[str] = None


class CustomFieldResponse(BaseModel):
    """Full custom field response schema for project custom_fields array.
    
    Based on: https://developers.asana.com/reference/customfields
    """
    gid: str
    resource_type: str = "custom_field"
    name: str
    type: str  # "text", "enum", "multi_enum", "number", "date", "people", "formula"
    
    # Enum fields
    enum_options: Optional[List[EnumOptionCompact]] = None
    enum_value: Optional[EnumOptionCompact] = None
    multi_enum_values: Optional[List[EnumOptionCompact]] = None
    
    # Value fields
    text_value: Optional[str] = None
    number_value: Optional[float] = None
    date_value: Optional[DateValue] = None
    people_value: Optional[List[UserCompact]] = None
    display_value: Optional[str] = None
    
    # Metadata
    enabled: bool = True
    representation_type: Optional[str] = None
    id_prefix: Optional[str] = None
    input_restrictions: Optional[str] = None
    is_formula_field: bool = False
    description: Optional[str] = None
    precision: Optional[int] = None
    format: Optional[str] = None
    currency_code: Optional[str] = None
    custom_label: Optional[str] = None
    custom_label_position: Optional[str] = None
    is_global_to_workspace: bool = False
    has_notifications_enabled: bool = False
    asana_created_field: Optional[str] = None
    is_value_read_only: bool = False
    created_by: Optional[UserCompact] = None
    reference_value: Optional[List[dict]] = None
    privacy_setting: Optional[str] = None
    default_access_level: Optional[str] = None
    resource_subtype: Optional[str] = None


class CustomFieldSettingResponse(BaseModel):
    """Custom field setting response schema for project custom_field_settings array.
    
    Based on: https://developers.asana.com/reference/customfieldsettings
    """
    gid: str
    resource_type: str = "custom_field_setting"
    project: Optional[dict] = None  # ProjectCompact (deprecated - use parent)
    parent: Optional[dict] = None  # ProjectCompact or PortfolioCompact
    is_important: bool = False
    custom_field: Optional[CustomFieldResponse] = None


class ProjectStatusResponse(BaseModel):
    """Project status (deprecated) response schema.
    
    Note: This is deprecated. Use status_updates instead.
    Based on: https://developers.asana.com/reference/projectstatuses
    """
    gid: str
    resource_type: str = "project_status"
    title: str
    text: Optional[str] = None
    html_text: Optional[str] = None
    color: str = "green"  # green, yellow, red, complete
    author: Optional[UserCompact] = None
    created_at: Optional[str] = None
    created_by: Optional[UserCompact] = None
    modified_at: Optional[str] = None


class StatusUpdateCompact(BaseModel):
    """Compact status update schema for current_status_update field."""
    gid: str
    resource_type: str = "status_update"
    title: str
    resource_subtype: str = "project_status_update"


# =============================================================================
# PROJECT RESPONSE SCHEMA (Full 200 response)
# Based on: https://developers.asana.com/reference/getproject
# =============================================================================

class ProjectResponse(BaseModel):
    """Full project response schema matching Asana API 200 response.
    
    Based on: https://developers.asana.com/reference/getproject
    Sample response: https://developers.asana.com/reference/createproject
    """
    # Identity
    gid: str
    resource_type: str = "project"
    
    # Content
    name: str
    notes: Optional[str] = None
    html_notes: Optional[str] = None
    
    # State
    archived: bool = False
    completed: bool = False
    completed_at: Optional[str] = None
    completed_by: Optional[UserCompact] = None
    
    # Privacy
    privacy_setting: Optional[str] = None  # "public_to_workspace", "private_to_team", "private"
    
    # Display
    color: Optional[str] = None
    default_view: str = "list"  # "list", "board", "calendar", "timeline"
    icon: Optional[str] = None
    
    # Dates
    start_on: Optional[str] = None  # YYYY-MM-DD
    due_on: Optional[str] = None  # YYYY-MM-DD
    due_date: Optional[str] = None  # Deprecated: use due_on
    
    # Timestamps
    created_at: Optional[str] = None  # ISO 8601 datetime
    modified_at: Optional[str] = None  # ISO 8601 datetime
    
    # Relationships - Compact objects
    workspace: Optional[WorkspaceCompact] = None
    team: Optional[TeamCompact] = None
    owner: Optional[UserCompact] = None
    members: Optional[List[UserCompact]] = None
    followers: Optional[List[UserCompact]] = None
    
    # Status
    current_status: Optional[ProjectStatusResponse] = None  # Deprecated
    current_status_update: Optional[StatusUpdateCompact] = None
    
    # Custom fields
    custom_fields: Optional[List[CustomFieldResponse]] = None
    custom_field_settings: Optional[List[CustomFieldSettingResponse]] = None
    
    # Template/Brief
    created_from_template: Optional[ProjectTemplateCompact] = None
    project_brief: Optional[ProjectBriefCompact] = None
    
    # URL
    permalink_url: Optional[str] = None
    
    # Access control
    default_access_level: Optional[str] = None  # "admin", "editor", "commenter", "viewer"
    minimum_access_level_for_customization: Optional[str] = None  # "admin", "editor"
    minimum_access_level_for_sharing: Optional[str] = None  # "admin", "editor"
    
    class Config:
        from_attributes = True


# =============================================================================
# LIST RESPONSE WITH PAGINATION
# =============================================================================

class NextPage(BaseModel):
    """Pagination next_page object."""
    offset: str
    path: str
    uri: str


class ProjectListResponse(BaseModel):
    """Response schema for GET /projects (list with pagination).
    
    Based on: https://developers.asana.com/reference/getprojects
    """
    data: List[ProjectResponse]
    next_page: Optional[NextPage] = None


# =============================================================================
# ERROR RESPONSE SCHEMAS
# =============================================================================

class ErrorDetail(BaseModel):
    """Individual error detail in error response."""
    message: str
    help: Optional[str] = None
    phrase: Optional[str] = None  # 500 errors only


class ErrorResponse(BaseModel):
    """Standard Asana error response format.
    
    Used for status codes: 400, 401, 403, 404, 500
    """
    errors: List[ErrorDetail]


# =============================================================================
# COMPACT SCHEMAS FOR NESTED USE
# =============================================================================

class ProjectCompact(BaseModel):
    """Compact project representation for nested responses."""
    gid: str
    resource_type: str = "project"
    name: str
    
    class Config:
        from_attributes = True


# =============================================================================
# DUPLICATE PROJECT REQUEST
# =============================================================================

class DuplicateIncludeOption(str, Enum):
    """Options for what to include when duplicating a project."""
    MEMBERS = "members"
    NOTES = "notes"
    FORMS = "forms"
    TASK_NOTES = "task_notes"
    TASK_ASSIGNEE = "task_assignee"
    TASK_SUBTASKS = "task_subtasks"
    TASK_ATTACHMENTS = "task_attachments"
    TASK_DATES = "task_dates"
    TASK_DEPENDENCIES = "task_dependencies"
    TASK_FOLLOWERS = "task_followers"
    TASK_TAGS = "task_tags"
    TASK_PROJECTS = "task_projects"


class DuplicateScheduleDates(BaseModel):
    """Schedule dates configuration for project duplication."""
    should_skip_weekends: Optional[bool] = Field(None, description="Skip weekends when scheduling")
    start_on: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    due_on: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")


class ProjectDuplicateRequest(BaseModel):
    """Request to duplicate a project.
    
    Based on: https://developers.asana.com/reference/duplicateproject
    """
    name: str = Field(..., min_length=1, max_length=255, description="New project name")
    team: Optional[str] = Field(None, description="Target team GID")
    include: Optional[List[str]] = Field(
        default=[
            "members",
            "notes", 
            "task_notes",
            "task_assignee",
            "task_subtasks",
            "task_attachments",
            "task_dates",
            "task_dependencies",
            "task_followers",
            "task_tags",
            "task_projects"
        ],
        description="Elements to duplicate: members, notes, forms, task_notes, task_assignee, task_subtasks, task_attachments, task_dates, task_dependencies, task_followers, task_tags, task_projects"
    )
    schedule_dates: Optional[DuplicateScheduleDates] = Field(
        None,
        description="Schedule dates config for shifting task dates"
    )


# =============================================================================
# PROJECT MEMBERSHIP SCHEMAS
# =============================================================================

class AddMembersRequest(BaseModel):
    """Request to add members to a project."""
    members: str = Field(..., description="Comma-separated user GIDs")


class RemoveMembersRequest(BaseModel):
    """Request to remove members from a project."""
    members: str = Field(..., description="Comma-separated user GIDs")


class AddFollowersRequest(BaseModel):
    """Request to add followers to a project."""
    followers: str = Field(..., description="Comma-separated user GIDs")


class RemoveFollowersRequest(BaseModel):
    """Request to remove followers from a project."""
    followers: str = Field(..., description="Comma-separated user GIDs")


class ProjectMembershipResponse(BaseModel):
    """Project membership response.
    
    Based on: https://developers.asana.com/reference/getprojectmembership
    """
    gid: str
    resource_type: str = "project_membership"
    user: dict
    project: dict
    parent: Optional[dict] = None
    member: Optional[dict] = None
    access_level: str = "editor"
    write_access: str = "full_write"
    
    class Config:
        from_attributes = True


# =============================================================================
# PROJECT TASK COUNTS
# =============================================================================

class TaskCountsResponse(BaseModel):
    """Task counts for a project.
    
    Based on: https://developers.asana.com/reference/gettaskcountsforproject
    """
    num_tasks: int = 0
    num_completed_tasks: int = 0
    num_incomplete_tasks: int = 0
    num_milestones: int = 0
    num_completed_milestones: int = 0
    num_incomplete_milestones: int = 0


# =============================================================================
# PROJECT STATUS SCHEMAS
# =============================================================================

class ProjectStatusBase(BaseModel):
    """Base project status schema."""
    title: str = Field(..., min_length=1, max_length=255)
    text: Optional[str] = None
    html_text: Optional[str] = None
    color: str = Field(
        default="green",
        pattern="^(green|yellow|red|blue|complete)$",
        description="Status color: green, yellow, red, blue, complete"
    )


class ProjectStatusCreate(ProjectStatusBase):
    """Schema for creating a project status."""
    pass


class ProjectStatusResponse(BaseModel):
    """Project status response (DEPRECATED - use status_updates).
    
    Based on: https://developers.asana.com/reference/getprojectstatus
    """
    gid: str
    resource_type: str = "project_status"
    title: str
    text: Optional[str] = None
    html_text: Optional[str] = None
    color: str = "green"
    created_at: Optional[str] = None
    created_by: Optional[dict] = None
    author: Optional[dict] = None
    modified_at: Optional[str] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# PROJECT BRIEF SCHEMAS
# =============================================================================

class ProjectBriefBase(BaseModel):
    """Base project brief schema."""
    title: Optional[str] = None
    text: Optional[str] = None
    html_text: Optional[str] = None


class ProjectBriefCreate(ProjectBriefBase):
    """Schema for creating a project brief.
    
    Based on: https://developers.asana.com/reference/createprojectbrief
    """
    project: str = Field(..., description="Project GID")


class ProjectBriefUpdate(ProjectBriefBase):
    """Schema for updating a project brief."""
    pass


class ProjectBriefResponse(BaseModel):
    """Project brief response.
    
    Based on: https://developers.asana.com/reference/getprojectbrief
    """
    gid: str
    resource_type: str = "project_brief"
    title: Optional[str] = None
    text: Optional[str] = None
    html_text: Optional[str] = None
    project: Optional[dict] = None
    permalink_url: Optional[str] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# CUSTOM FIELD SETTINGS FOR PROJECT
# =============================================================================

class AddCustomFieldRequest(BaseModel):
    """Request to add a custom field to a project.
    
    Based on: https://developers.asana.com/reference/addcustomfieldtoproject
    """
    custom_field: str = Field(..., description="Custom field GID")
    is_important: Optional[bool] = Field(None, description="Whether to pin the field")
    insert_before: Optional[str] = Field(None, description="Custom field setting GID to insert before")
    insert_after: Optional[str] = Field(None, description="Custom field setting GID to insert after")


class RemoveCustomFieldRequest(BaseModel):
    """Request to remove a custom field from a project."""
    custom_field: str = Field(..., description="Custom field GID")


# =============================================================================
# SAVE AS TEMPLATE REQUEST
# =============================================================================

class SaveAsTemplateRequest(BaseModel):
    """Request to create a project template from a project.
    
    Based on: https://developers.asana.com/reference/projectsaveasstemplate
    """
    name: str = Field(..., min_length=1, max_length=255, description="Name for the new template")
    team: Optional[str] = Field(None, description="Team GID to share the template with")
    public: Optional[bool] = Field(None, description="Whether the template is public")


# =============================================================================
# PROJECT QUERY PARAMETERS (for GET requests)
# =============================================================================

class ProjectQueryParams(BaseModel):
    """Query parameters for GET /projects endpoints.
    
    Based on: https://developers.asana.com/reference/getprojects
    """
    workspace: Optional[str] = Field(None, description="Workspace GID to filter projects")
    team: Optional[str] = Field(None, description="Team GID to filter projects")
    archived: Optional[bool] = Field(None, description="Filter for archived projects")
    limit: Optional[int] = Field(None, ge=1, le=100, description="Results per page (max 100)")
    offset: Optional[str] = Field(None, description="Pagination offset token")
    opt_fields: Optional[str] = Field(None, description="Comma-separated list of optional fields")
    opt_pretty: Optional[bool] = Field(None, description="Pretty print the response")


# =============================================================================
# CUSTOM FIELD SETTING RESPONSE
# =============================================================================

class CustomFieldSettingResponse(BaseModel):
    """Custom field setting response.
    
    Based on: https://developers.asana.com/reference/customfieldsettings
    """
    gid: str
    resource_type: str = "custom_field_setting"
    project: Optional[dict] = Field(None, description="Deprecated: use parent")
    parent: Optional[dict] = Field(None, description="Project or portfolio this setting belongs to")
    is_important: bool = False
    custom_field: Optional[dict] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# JOB RESPONSE (for async operations like duplicate)
# =============================================================================

class JobResponse(BaseModel):
    """Job response for async operations.
    
    Based on: https://developers.asana.com/reference/getjob
    """
    gid: str
    resource_type: str = "job"
    resource_subtype: str = "duplicate_project"
    status: str = "not_started"
    new_project: Optional[dict] = None
    new_task: Optional[dict] = None
    new_task_template: Optional[dict] = None
    new_project_template: Optional[dict] = None
    
    class Config:
        from_attributes = True
