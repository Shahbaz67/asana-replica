from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.workspace import WorkspaceMembership
    from app.models.team import TeamMembership
    from app.models.project import ProjectMembership
    from app.models.task import Task
    from app.models.story import Story
    from app.models.user_task_list import UserTaskList
    from app.models.user_favorites import UserFavorite


class User(AsanaBase):
    """User model representing an Asana user."""
    __tablename__ = "users"
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # Profile
    photo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # URL to photo
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    workspace_memberships: Mapped[List["WorkspaceMembership"]] = relationship(
        "WorkspaceMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    team_memberships: Mapped[List["TeamMembership"]] = relationship(
        "TeamMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    project_memberships: Mapped[List["ProjectMembership"]] = relationship(
        "ProjectMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    assigned_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="assignee",
        foreign_keys="Task.assignee_gid",
    )
    
    stories: Mapped[List["Story"]] = relationship(
        "Story",
        back_populates="created_by",
    )
    
    task_lists: Mapped[List["UserTaskList"]] = relationship(
        "UserTaskList",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    
    favorites: Mapped[List["UserFavorite"]] = relationship(
        "UserFavorite",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    @property
    def resource_type(self) -> str:
        return "user"
    
    def to_response(self, include_email: bool = False) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
        }
        if include_email:
            response["email"] = self.email
        if self.photo:
            response["photo"] = {
                "image_128x128": self.photo,
                "image_60x60": self.photo,
                "image_36x36": self.photo,
                "image_27x27": self.photo,
                "image_21x21": self.photo,
            }
        return response

