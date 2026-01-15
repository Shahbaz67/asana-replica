from typing import Optional, List, TYPE_CHECKING
from datetime import date
from sqlalchemy import String, Boolean, ForeignKey, Text, Date, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.user import User
    from app.models.team import Team
    from app.models.time_period import TimePeriod


class Goal(AsanaBase):
    """Goal model for tracking objectives."""
    __tablename__ = "goals"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Due date
    due_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    start_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # on_track, at_risk, off_track
    
    # Is workspace level goal
    is_workspace_level: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Liked
    liked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    num_likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Metric - target/current values
    metric_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # number, percent, currency
    metric_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metric_precision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metric_currency_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    metric_initial_number_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metric_target_number_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metric_current_number_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Foreign keys
    workspace_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("workspaces.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    owner_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    team_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("teams.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    time_period_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("time_periods.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="goals")
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_gid])
    team: Mapped[Optional["Team"]] = relationship("Team")
    time_period: Mapped[Optional["TimePeriod"]] = relationship("TimePeriod")
    
    relationships_from: Mapped[List["GoalRelationship"]] = relationship(
        "GoalRelationship",
        foreign_keys="GoalRelationship.supporting_goal_gid",
        back_populates="supporting_goal",
        cascade="all, delete-orphan",
    )
    
    relationships_to: Mapped[List["GoalRelationship"]] = relationship(
        "GoalRelationship",
        foreign_keys="GoalRelationship.supported_goal_gid",
        back_populates="supported_goal",
        cascade="all, delete-orphan",
    )
    
    status_updates: Mapped[List["StatusUpdate"]] = relationship(
        "StatusUpdate",
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    
    @property
    def resource_type(self) -> str:
        return "goal"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "notes": self.notes,
            "html_notes": self.html_notes,
            "status": self.status,
            "is_workspace_level": self.is_workspace_level,
            "liked": self.liked,
            "num_likes": self.num_likes,
            "workspace": {"gid": self.workspace_gid, "resource_type": "workspace"},
        }
        
        if self.due_on:
            response["due_on"] = self.due_on.isoformat()
        if self.start_on:
            response["start_on"] = self.start_on.isoformat()
        if self.owner_gid:
            response["owner"] = {"gid": self.owner_gid, "resource_type": "user"}
        if self.team_gid:
            response["team"] = {"gid": self.team_gid, "resource_type": "team"}
        if self.time_period_gid:
            response["time_period"] = {"gid": self.time_period_gid, "resource_type": "time_period"}
            
        if self.metric_type:
            response["metric"] = {
                "metric_type": self.metric_type,
                "unit": self.metric_unit,
                "precision": self.metric_precision,
                "currency_code": self.metric_currency_code,
                "initial_number_value": self.metric_initial_number_value,
                "target_number_value": self.metric_target_number_value,
                "current_number_value": self.metric_current_number_value,
            }
            
        return response


class GoalRelationship(AsanaBase):
    """Relationship between goals (supporting/supported)."""
    __tablename__ = "goal_relationships"
    
    # Contribution weight (0-1)
    contribution_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    
    # Foreign keys
    supporting_goal_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("goals.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    supported_goal_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("goals.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    supporting_goal: Mapped["Goal"] = relationship(
        "Goal",
        foreign_keys=[supporting_goal_gid],
        back_populates="relationships_from",
    )
    supported_goal: Mapped["Goal"] = relationship(
        "Goal",
        foreign_keys=[supported_goal_gid],
        back_populates="relationships_to",
    )
    
    @property
    def resource_type(self) -> str:
        return "goal_relationship"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "supporting_goal": {"gid": self.supporting_goal_gid, "resource_type": "goal"},
            "supported_goal": {"gid": self.supported_goal_gid, "resource_type": "goal"},
            "contribution_weight": self.contribution_weight,
        }


class GoalMembership(AsanaBase):
    """Goal membership for tracking collaborators on goals."""
    __tablename__ = "goal_memberships"
    
    # Role (owner, member)
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)
    
    # Foreign keys
    goal_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("goals.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    member_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    goal: Mapped["Goal"] = relationship("Goal")
    member: Mapped["User"] = relationship("User")
    
    @property
    def resource_type(self) -> str:
        return "goal_membership"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "goal": {"gid": self.goal_gid, "resource_type": "goal"},
            "member": {"gid": self.member_gid, "resource_type": "user"},
            "role": self.role,
        }


class StatusUpdate(AsanaBase):
    """Status update for goals and portfolios."""
    __tablename__ = "status_updates"
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status type (on_track, at_risk, off_track, on_hold, complete)
    status_type: Mapped[str] = mapped_column(String(50), default="on_track", nullable=False)
    
    # Resource subtype
    resource_subtype: Mapped[str] = mapped_column(String(50), default="status_update", nullable=False)
    
    # Foreign keys
    goal_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("goals.gid", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    author_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    goal: Mapped[Optional["Goal"]] = relationship("Goal", back_populates="status_updates")
    author: Mapped[Optional["User"]] = relationship("User")
    
    @property
    def resource_type(self) -> str:
        return "status_update"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "resource_subtype": self.resource_subtype,
            "title": self.title,
            "text": self.text,
            "html_text": self.html_text,
            "status_type": self.status_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if self.goal_gid:
            response["parent"] = {"gid": self.goal_gid, "resource_type": "goal"}
        if self.author_gid:
            response["author"] = {"gid": self.author_gid, "resource_type": "user"}
            
        return response


