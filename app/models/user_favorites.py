from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class UserFavorite(AsanaBase):
    """User favorite resources."""
    __tablename__ = "user_favorites"
    
    # Resource being favorited
    resource_gid: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Foreign keys
    user_gid: Mapped[str] = mapped_column(
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
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    workspace: Mapped["Workspace"] = relationship("Workspace")
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        return {
            "gid": self.resource_gid,
            "resource_type": self.resource_type,
        }


