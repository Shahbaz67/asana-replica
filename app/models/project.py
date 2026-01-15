from typing import Optional, List, TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import String, Boolean, ForeignKey, Text, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace
    from app.models.team import Team
    from app.models.section import Section
    from app.models.task import Task
    from app.models.custom_field import CustomFieldSetting


class Project(AsanaBase):
    """Project model representing an Asana project."""
    __tablename__ = "projects"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Archived status
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Public to workspace
    public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Color (dark-pink, dark-green, dark-blue, dark-red, dark-teal, dark-brown, 
    # dark-orange, dark-purple, dark-warm-gray, light-pink, light-green, light-blue,
    # light-red, light-teal, light-brown, light-orange, light-purple, light-warm-gray)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Layout (list, board, calendar, timeline)
    default_view: Mapped[str] = mapped_column(String(50), default="list", nullable=False)
    
    # Due dates
    due_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    start_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Completion status
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Owner
    owner_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Current status text
    current_status_update_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
    )
    
    # Icon
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Privacy setting
    privacy_setting: Mapped[str] = mapped_column(String(50), default="public_to_workspace", nullable=False)
    
    # Foreign keys
    workspace_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("workspaces.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("teams.gid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="projects")
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="projects")
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_gid])
    
    sections: Mapped[List["Section"]] = relationship(
        "Section",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Section.order",
    )
    
    memberships: Mapped[List["ProjectMembership"]] = relationship(
        "ProjectMembership",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    
    statuses: Mapped[List["ProjectStatus"]] = relationship(
        "ProjectStatus",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectStatus.created_at.desc()",
    )
    
    briefs: Mapped[List["ProjectBrief"]] = relationship(
        "ProjectBrief",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    
    custom_field_settings: Mapped[List["CustomFieldSetting"]] = relationship(
        "CustomFieldSetting",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    
    @property
    def resource_type(self) -> str:
        return "project"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "notes": self.notes,
            "html_notes": self.html_notes,
            "archived": self.archived,
            "public": self.public,
            "color": self.color,
            "default_view": self.default_view,
            "completed": self.completed,
            "privacy_setting": self.privacy_setting,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "workspace": {"gid": self.workspace_gid, "resource_type": "workspace"},
        }
        
        if self.due_on:
            response["due_on"] = self.due_on.isoformat()
        if self.due_at:
            response["due_at"] = self.due_at.isoformat()
        if self.start_on:
            response["start_on"] = self.start_on.isoformat()
        if self.completed_at:
            response["completed_at"] = self.completed_at.isoformat()
        if self.owner_gid:
            response["owner"] = {"gid": self.owner_gid, "resource_type": "user"}
        if self.team_gid:
            response["team"] = {"gid": self.team_gid, "resource_type": "team"}
        if self.icon:
            response["icon"] = self.icon
            
        return response


class ProjectMembership(AsanaBase):
    """Association between users and projects."""
    __tablename__ = "project_memberships"
    
    user_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("projects.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Access level: editor, commenter, viewer
    access_level: Mapped[str] = mapped_column(String(50), default="editor", nullable=False)
    
    # Write access
    write_access: Mapped[str] = mapped_column(String(50), default="full_write", nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="project_memberships")
    project: Mapped["Project"] = relationship("Project", back_populates="memberships")
    
    @property
    def resource_type(self) -> str:
        return "project_membership"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "user": {"gid": self.user_gid, "resource_type": "user"},
            "project": {"gid": self.project_gid, "resource_type": "project"},
            "access_level": self.access_level,
            "write_access": self.write_access,
        }


class ProjectStatus(AsanaBase):
    """Project status update."""
    __tablename__ = "project_statuses"
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Color: green, yellow, red, complete
    color: Mapped[str] = mapped_column(String(50), default="green", nullable=False)
    
    # Foreign keys
    project_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("projects.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="statuses")
    author: Mapped[Optional["User"]] = relationship("User", foreign_keys=[author_gid])
    
    @property
    def resource_type(self) -> str:
        return "project_status"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "title": self.title,
            "text": self.text,
            "html_text": self.html_text,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if self.author_gid:
            response["author"] = {"gid": self.author_gid, "resource_type": "user"}
        return response


class ProjectBrief(AsanaBase):
    """Project brief - the overview document for a project."""
    __tablename__ = "project_briefs"
    
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    project_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("projects.gid", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="briefs")
    
    @property
    def resource_type(self) -> str:
        return "project_brief"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "title": self.title,
            "text": self.text,
            "html_text": self.html_text,
            "project": {"gid": self.project_gid, "resource_type": "project"},
        }


class ProjectTemplate(AsanaBase):
    """Project template for creating new projects."""
    __tablename__ = "project_templates"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Public to workspace
    public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Color
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Template data (JSON stored as text)
    template_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    team_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("teams.gid", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    owner_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    @property
    def resource_type(self) -> str:
        return "project_template"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "description": self.description,
            "html_description": self.html_description,
            "public": self.public,
            "color": self.color,
        }
        if self.team_gid:
            response["team"] = {"gid": self.team_gid, "resource_type": "team"}
        if self.owner_gid:
            response["owner"] = {"gid": self.owner_gid, "resource_type": "user"}
        return response

