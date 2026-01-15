from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.user import User


class EventRecord(AsanaBase):
    """Event record for the Events API."""
    __tablename__ = "event_records"
    
    # Resource that changed
    resource_gid: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Parent resource (e.g., project for a task)
    parent_gid: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    parent_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Action type (changed, added, removed, deleted, undeleted)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # User who made the change
    user_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Change details (JSON stored as text)
    change: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")
    
    @property
    def event_resource_type(self) -> str:
        return "event"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "resource": {"gid": self.resource_gid, "resource_type": self.resource_type},
            "action": self.action,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if self.parent_gid:
            response["parent"] = {"gid": self.parent_gid, "resource_type": self.parent_type}
        if self.user_gid:
            response["user"] = {"gid": self.user_gid, "resource_type": "user"}
            
        return response

