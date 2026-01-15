from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


class Attachment(AsanaBase):
    """Attachment model for files attached to tasks."""
    __tablename__ = "attachments"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Resource subtype (asana, external, dropbox, gdrive, onedrive, box, vimeo)
    resource_subtype: Mapped[str] = mapped_column(String(50), default="asana", nullable=False)
    
    # Host type (asana, dropbox, etc.)
    host: Mapped[str] = mapped_column(String(50), default="asana", nullable=False)
    
    # File URLs
    download_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    view_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    permanent_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # File size in bytes
    size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Connected to parent (for external attachments like Figma)
    connected_to_app: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # Foreign keys
    parent_gid: Mapped[str] = mapped_column(
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
    parent_task: Mapped["Task"] = relationship("Task", back_populates="attachments")
    created_by: Mapped[Optional["User"]] = relationship("User")
    
    @property
    def resource_type(self) -> str:
        return "attachment"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "resource_subtype": self.resource_subtype,
            "name": self.name,
            "host": self.host,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "parent": {"gid": self.parent_gid, "resource_type": "task"},
        }
        
        if self.download_url:
            response["download_url"] = self.download_url
        if self.view_url:
            response["view_url"] = self.view_url
        if self.permanent_url:
            response["permanent_url"] = self.permanent_url
        if self.size is not None:
            response["size"] = self.size
        if self.connected_to_app:
            response["connected_to_app"] = self.connected_to_app
            
        return response


