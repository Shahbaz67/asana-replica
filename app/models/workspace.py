from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.team import Team
    from app.models.project import Project
    from app.models.tag import Tag
    from app.models.custom_field import CustomField
    from app.models.portfolio import Portfolio
    from app.models.goal import Goal


class WorkspaceType(str, enum.Enum):
    """Type of workspace."""
    WORKSPACE = "workspace"
    ORGANIZATION = "organization"


class MembershipRole(str, enum.Enum):
    """Role in a workspace membership."""
    ADMIN = "admin"
    MEMBER = "member"
    LIMITED_ACCESS = "limited_access"


class Workspace(AsanaBase):
    """Workspace model representing an Asana workspace or organization."""
    __tablename__ = "workspaces"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_organization: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Email domains for organization (JSON array stored as string)
    email_domains: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Relationships
    memberships: Mapped[List["WorkspaceMembership"]] = relationship(
        "WorkspaceMembership",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    
    teams: Mapped[List["Team"]] = relationship(
        "Team",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    
    custom_fields: Mapped[List["CustomField"]] = relationship(
        "CustomField",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    
    portfolios: Mapped[List["Portfolio"]] = relationship(
        "Portfolio",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    
    goals: Mapped[List["Goal"]] = relationship(
        "Goal",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    
    @property
    def resource_type(self) -> str:
        return "workspace"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "is_organization": self.is_organization,
            "email_domains": self.email_domains.split(",") if self.email_domains else [],
        }


class WorkspaceMembership(AsanaBase):
    """Association between users and workspaces."""
    __tablename__ = "workspace_memberships"
    
    user_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("workspaces.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Role in the workspace
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="workspace_memberships")
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="memberships")
    
    @property
    def resource_type(self) -> str:
        return "workspace_membership"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "user": {"gid": self.user_gid, "resource_type": "user"},
            "workspace": {"gid": self.workspace_gid, "resource_type": "workspace"},
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "is_guest": self.is_guest,
        }


