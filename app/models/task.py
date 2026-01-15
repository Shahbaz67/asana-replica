from typing import Optional, List, TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import String, Boolean, ForeignKey, Text, Date, DateTime, Integer, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.section import Section
    from app.models.project import Project
    from app.models.story import Story
    from app.models.attachment import Attachment
    from app.models.tag import Tag
    from app.models.custom_field import TaskCustomFieldValue


class Task(AsanaBase):
    """Task model representing an Asana task."""
    __tablename__ = "tasks"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Resource subtype (default_task, milestone, section, approval)
    resource_subtype: Mapped[str] = mapped_column(String(50), default="default_task", nullable=False)
    
    # Completion
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Due dates
    due_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    start_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Approval status (pending, approved, rejected, changes_requested)
    approval_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Liked
    liked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    num_likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Hearts (legacy - same as likes)
    hearted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    num_hearts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Subtasks count
    num_subtasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Order within section/project
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Permalink URL (generated)
    permalink_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Foreign keys
    assignee_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Assignee status/section (deprecated but still used)
    assignee_status: Mapped[str] = mapped_column(String(50), default="upcoming", nullable=False)
    
    # Section (can be null for tasks not in a section)
    section_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("sections.gid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Parent task (for subtasks)
    parent_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("tasks.gid", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Relationships
    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="assigned_tasks",
        foreign_keys=[assignee_gid],
    )
    
    section: Mapped[Optional["Section"]] = relationship("Section", back_populates="tasks")
    
    parent: Mapped[Optional["Task"]] = relationship(
        "Task",
        remote_side="Task.gid",
        back_populates="subtasks",
        foreign_keys=[parent_gid],
    )
    
    subtasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="parent",
        foreign_keys="Task.parent_gid",
        order_by="Task.order",
    )
    
    stories: Mapped[List["Story"]] = relationship(
        "Story",
        back_populates="target_task",
        cascade="all, delete-orphan",
        order_by="Story.created_at",
    )
    
    attachments: Mapped[List["Attachment"]] = relationship(
        "Attachment",
        back_populates="parent_task",
        cascade="all, delete-orphan",
    )
    
    # Many-to-many relationships
    projects: Mapped[List["TaskProject"]] = relationship(
        "TaskProject",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    
    task_tags: Mapped[List["TaskTag"]] = relationship(
        "TaskTag",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    
    dependencies: Mapped[List["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_gid",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    
    dependents: Mapped[List["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_gid",
        back_populates="depends_on",
        cascade="all, delete-orphan",
    )
    
    followers: Mapped[List["TaskFollower"]] = relationship(
        "TaskFollower",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    
    custom_field_values: Mapped[List["TaskCustomFieldValue"]] = relationship(
        "TaskCustomFieldValue",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    
    @property
    def resource_type(self) -> str:
        return "task"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "resource_subtype": self.resource_subtype,
            "name": self.name,
            "notes": self.notes,
            "html_notes": self.html_notes,
            "completed": self.completed,
            "liked": self.liked,
            "num_likes": self.num_likes,
            "num_subtasks": self.num_subtasks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }
        
        if self.completed_at:
            response["completed_at"] = self.completed_at.isoformat()
        if self.due_on:
            response["due_on"] = self.due_on.isoformat()
        if self.due_at:
            response["due_at"] = self.due_at.isoformat()
        if self.start_on:
            response["start_on"] = self.start_on.isoformat()
        if self.start_at:
            response["start_at"] = self.start_at.isoformat()
        if self.assignee_gid:
            response["assignee"] = {"gid": self.assignee_gid, "resource_type": "user"}
        if self.parent_gid:
            response["parent"] = {"gid": self.parent_gid, "resource_type": "task"}
        if self.approval_status:
            response["approval_status"] = self.approval_status
        if self.permalink_url:
            response["permalink_url"] = self.permalink_url
            
        return response


class TaskProject(AsanaBase):
    """Association between tasks and projects."""
    __tablename__ = "task_projects"
    
    task_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("tasks.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("projects.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("sections.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="projects")
    project: Mapped["Project"] = relationship("Project")
    section: Mapped[Optional["Section"]] = relationship("Section")


class TaskTag(AsanaBase):
    """Association between tasks and tags."""
    __tablename__ = "task_tags"
    
    task_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("tasks.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("tags.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="task_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="task_tags")


class TaskDependency(AsanaBase):
    """Task dependency relationship."""
    __tablename__ = "task_dependencies"
    
    task_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("tasks.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    depends_on_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("tasks.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        foreign_keys=[task_gid],
        back_populates="dependencies",
    )
    depends_on: Mapped["Task"] = relationship(
        "Task",
        foreign_keys=[depends_on_gid],
        back_populates="dependents",
    )


class TaskFollower(AsanaBase):
    """Task followers."""
    __tablename__ = "task_followers"
    
    task_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("tasks.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="followers")
    user: Mapped["User"] = relationship("User")


class TaskTemplate(AsanaBase):
    """Task template for creating new tasks."""
    __tablename__ = "task_templates"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Template data (JSON stored as text)
    template_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    project_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("projects.gid", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    created_by_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    @property
    def resource_type(self) -> str:
        return "task_template"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "description": self.description,
        }
        if self.project_gid:
            response["project"] = {"gid": self.project_gid, "resource_type": "project"}
        return response


