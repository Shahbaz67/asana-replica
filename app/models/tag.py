from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.task import TaskTag


class Tag(AsanaBase):
    """Tag model for labeling tasks."""
    __tablename__ = "tags"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Color
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Notes/description
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    workspace_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("workspaces.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="tags")
    
    task_tags: Mapped[List["TaskTag"]] = relationship(
        "TaskTag",
        back_populates="tag",
        cascade="all, delete-orphan",
    )
    
    @property
    def resource_type(self) -> str:
        return "tag"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "workspace": {"gid": self.workspace_gid, "resource_type": "workspace"},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if self.color:
            response["color"] = self.color
        if self.notes:
            response["notes"] = self.notes
            
        return response


