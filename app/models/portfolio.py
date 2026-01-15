from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.user import User
    from app.models.project import Project


class Portfolio(AsanaBase):
    """Portfolio model for grouping projects."""
    __tablename__ = "portfolios"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Color
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Public to workspace
    public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
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
    
    # Current status update
    current_status_update_gid: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="portfolios")
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_gid])
    
    memberships: Mapped[List["PortfolioMembership"]] = relationship(
        "PortfolioMembership",
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )
    
    items: Mapped[List["PortfolioItem"]] = relationship(
        "PortfolioItem",
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )
    
    @property
    def resource_type(self) -> str:
        return "portfolio"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "color": self.color,
            "public": self.public,
            "workspace": {"gid": self.workspace_gid, "resource_type": "workspace"},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if self.owner_gid:
            response["owner"] = {"gid": self.owner_gid, "resource_type": "user"}
            
        return response


class PortfolioMembership(AsanaBase):
    """Association between users and portfolios."""
    __tablename__ = "portfolio_memberships"
    
    # Foreign keys
    portfolio_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("portfolios.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Access level
    access_level: Mapped[str] = mapped_column(String(50), default="editor", nullable=False)
    
    # Relationships
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="memberships")
    user: Mapped["User"] = relationship("User")
    
    @property
    def resource_type(self) -> str:
        return "portfolio_membership"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "portfolio": {"gid": self.portfolio_gid, "resource_type": "portfolio"},
            "user": {"gid": self.user_gid, "resource_type": "user"},
            "access_level": self.access_level,
        }


class PortfolioItem(AsanaBase):
    """Projects in a portfolio."""
    __tablename__ = "portfolio_items"
    
    # Order
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Foreign keys
    portfolio_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("portfolios.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("projects.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="items")
    project: Mapped["Project"] = relationship("Project")
    
    @property
    def resource_type(self) -> str:
        return "portfolio_item"


