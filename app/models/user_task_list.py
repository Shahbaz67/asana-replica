from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class UserTaskList(AsanaBase):
    """User task list - My Tasks list for a user in a workspace."""
    __tablename__ = "user_task_lists"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Foreign keys
    owner_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("workspaces.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="task_lists")
    workspace: Mapped["Workspace"] = relationship("Workspace")
    
    @property
    def resource_type(self) -> str:
        return "user_task_list"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "owner": {"gid": self.owner_gid, "resource_type": "user"},
            "workspace": {"gid": self.workspace_gid, "resource_type": "workspace"},
        }


