from typing import Optional, TYPE_CHECKING
from datetime import date
from sqlalchemy import String, ForeignKey, Date, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class TimeTrackingEntry(AsanaBase):
    """Time tracking entry for tasks."""
    __tablename__ = "time_tracking_entries"
    
    # Duration in minutes
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Entry date
    entered_on: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Foreign keys
    task_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("tasks.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    created_by_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    task: Mapped["Task"] = relationship("Task")
    created_by: Mapped[Optional["User"]] = relationship("User")
    
    @property
    def resource_type(self) -> str:
        return "time_tracking_entry"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "duration_minutes": self.duration_minutes,
            "entered_on": self.entered_on.isoformat() if self.entered_on else None,
            "task": {"gid": self.task_gid, "resource_type": "task"},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if self.created_by_gid:
            response["created_by"] = {"gid": self.created_by_gid, "resource_type": "user"}
            
        return response


