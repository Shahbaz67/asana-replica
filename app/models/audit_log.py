from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class AuditLogEvent(AsanaBase):
    """Audit log event for enterprise features."""
    __tablename__ = "audit_log_events"
    
    # Event type (e.g., task_created, task_updated, login_success)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Event category (e.g., logins, task_actions)
    event_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Actor (who performed the action)
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)  # user, app, asana
    actor_gid: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    actor_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Resource that was acted upon
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_gid: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    resource_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Context (workspace/organization)
    context_type: Mapped[str] = mapped_column(String(50), nullable=False)  # workspace, organization
    context_gid: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    
    # Details (JSON stored as text)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Client info
    client_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    @property
    def audit_resource_type(self) -> str:
        return "audit_log_event"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.audit_resource_type,
            "event_type": self.event_type,
            "event_category": self.event_category,
            "actor": {
                "actor_type": self.actor_type,
                "gid": self.actor_gid,
                "email": self.actor_email,
            },
            "context": {
                "context_type": self.context_type,
                "gid": self.context_gid,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if self.resource_type:
            response["resource"] = {
                "resource_type": self.resource_type,
                "gid": self.resource_gid,
                "name": self.resource_name,
            }
            
        return response


