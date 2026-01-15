from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.user import User


class Job(AsanaBase):
    """Job model for async operations."""
    __tablename__ = "jobs"
    
    # Resource subtype
    resource_subtype: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Status (not_started, in_progress, succeeded, failed)
    status: Mapped[str] = mapped_column(String(50), default="not_started", nullable=False)
    
    # New project/task GID if applicable
    new_project_gid: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    new_task_gid: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    
    # New project template GID if applicable
    new_project_template_gid: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    
    # Created by user
    created_by_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    created_by: Mapped[Optional["User"]] = relationship("User")
    
    @property
    def resource_type(self) -> str:
        return "job"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "resource_subtype": self.resource_subtype,
            "status": self.status,
        }
        
        if self.new_project_gid:
            response["new_project"] = {"gid": self.new_project_gid, "resource_type": "project"}
        if self.new_task_gid:
            response["new_task"] = {"gid": self.new_task_gid, "resource_type": "task"}
        if self.new_project_template_gid:
            response["new_project_template"] = {
                "gid": self.new_project_template_gid,
                "resource_type": "project_template"
            }
            
        return response

