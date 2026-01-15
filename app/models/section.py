from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.task import Task


class Section(AsanaBase):
    """Section model representing a section in a project."""
    __tablename__ = "sections"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Order within the project
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Foreign keys
    project_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("projects.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="sections")
    
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="section",
        order_by="Task.order",
    )
    
    @property
    def resource_type(self) -> str:
        return "section"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "project": {"gid": self.project_gid, "resource_type": "project"},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

