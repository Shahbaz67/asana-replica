from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class OrganizationExport(AsanaBase):
    """Organization export job for data export."""
    __tablename__ = "organization_exports"
    
    # State (pending, started, finished, error)
    state: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    
    # Download URL when finished
    download_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Organization/workspace GID
    organization_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("workspaces.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Created by user
    created_by_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    organization: Mapped["Workspace"] = relationship("Workspace")
    created_by: Mapped[Optional["User"]] = relationship("User")
    
    @property
    def resource_type(self) -> str:
        return "organization_export"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "state": self.state,
            "organization": {"gid": self.organization_gid, "resource_type": "workspace"},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if self.download_url:
            response["download_url"] = self.download_url
            
        return response


