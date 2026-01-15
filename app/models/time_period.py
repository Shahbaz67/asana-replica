from typing import Optional, TYPE_CHECKING
from datetime import date
from sqlalchemy import String, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.workspace import Workspace


class TimePeriod(AsanaBase):
    """Time period model for goals."""
    __tablename__ = "time_periods"
    
    # Display name
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Period type (fy, h, q, m, w, custom)
    period: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Start and end dates
    start_on: Mapped[date] = mapped_column(Date, nullable=False)
    end_on: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Foreign keys
    parent_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("workspaces.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")
    
    @property
    def resource_type(self) -> str:
        return "time_period"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "display_name": self.display_name,
            "period": self.period,
            "start_on": self.start_on.isoformat() if self.start_on else None,
            "end_on": self.end_on.isoformat() if self.end_on else None,
            "parent": {"gid": self.parent_gid, "resource_type": "workspace"},
        }


