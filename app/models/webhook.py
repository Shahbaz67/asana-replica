from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.user import User


class Webhook(AsanaBase):
    """Webhook subscription model."""
    __tablename__ = "webhooks"
    
    # Target URL for webhook delivery
    target: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Resource being watched (project, task, etc.)
    resource_gid: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Active status
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Webhook secret for verification
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Filters (JSON stored as text)
    filters: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Last delivered at timestamp
    last_success_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_failure_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_failure_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Created by user
    created_by_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    created_by: Mapped[Optional["User"]] = relationship("User")
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": "webhook",
            "resource": {"gid": self.resource_gid, "resource_type": self.resource_type},
            "target": self.target,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if self.last_success_at:
            response["last_success_at"] = self.last_success_at
        if self.last_failure_at:
            response["last_failure_at"] = self.last_failure_at
        if self.last_failure_content:
            response["last_failure_content"] = self.last_failure_content
            
        return response

