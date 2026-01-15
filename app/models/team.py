from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace
    from app.models.project import Project


class Team(AsanaBase):
    """Team model representing an Asana team."""
    __tablename__ = "teams"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Visibility: public, members, secret
    visibility: Mapped[str] = mapped_column(String(50), default="members", nullable=False)
    
    # Edit team name/description setting
    edit_team_name_or_description_access_level: Mapped[str] = mapped_column(
        String(50), default="all_team_members", nullable=False
    )
    
    # Edit team visibility setting
    edit_team_visibility_or_trash_team_access_level: Mapped[str] = mapped_column(
        String(50), default="only_team_admins", nullable=False
    )
    
    # Guest invite management
    guest_invite_management_access_level: Mapped[str] = mapped_column(
        String(50), default="only_team_admins", nullable=False
    )
    
    # Join request management
    join_request_management_access_level: Mapped[str] = mapped_column(
        String(50), default="only_team_admins", nullable=False
    )
    
    # Member invite management
    member_invite_management_access_level: Mapped[str] = mapped_column(
        String(50), default="only_team_admins", nullable=False
    )
    
    # Team member removal
    team_member_removal_access_level: Mapped[str] = mapped_column(
        String(50), default="only_team_admins", nullable=False
    )
    
    # Foreign keys
    workspace_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("workspaces.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="teams")
    
    memberships: Mapped[List["TeamMembership"]] = relationship(
        "TeamMembership",
        back_populates="team",
        cascade="all, delete-orphan",
    )
    
    projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="team",
    )
    
    @property
    def resource_type(self) -> str:
        return "team"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "description": self.description,
            "html_description": self.html_description,
            "visibility": self.visibility,
            "organization": {"gid": self.workspace_gid, "resource_type": "workspace"},
        }


class TeamMembership(AsanaBase):
    """Association between users and teams."""
    __tablename__ = "team_memberships"
    
    user_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("teams.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_limited_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="team_memberships")
    team: Mapped["Team"] = relationship("Team", back_populates="memberships")
    
    @property
    def resource_type(self) -> str:
        return "team_membership"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "user": {"gid": self.user_gid, "resource_type": "user"},
            "team": {"gid": self.team_gid, "resource_type": "team"},
            "is_admin": self.is_admin,
            "is_guest": self.is_guest,
            "is_limited_access": self.is_limited_access,
        }


