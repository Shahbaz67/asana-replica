from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AsanaBase

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class Story(AsanaBase):
    """Story model representing comments and system updates on tasks."""
    __tablename__ = "stories"
    
    # Resource subtype
    # comment, attachment, like, assigned, due_date_changed, etc.
    resource_subtype: Mapped[str] = mapped_column(String(50), default="comment", nullable=False)
    
    # Text content (for comments)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Is pinned to top
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Is edited
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Like count
    liked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    num_likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Sticker name (for reactions)
    sticker_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Type (comment or system)
    type: Mapped[str] = mapped_column(String(50), default="comment", nullable=False)
    
    # Source (web, api, mobile, etc.)
    source: Mapped[str] = mapped_column(String(50), default="api", nullable=False)
    
    # Foreign keys
    created_by_gid: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.gid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    target_gid: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("tasks.gid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Relationships
    created_by: Mapped[Optional["User"]] = relationship("User", back_populates="stories")
    target_task: Mapped["Task"] = relationship("Task", back_populates="stories")
    
    @property
    def resource_type(self) -> str:
        return "story"
    
    def to_response(self) -> dict:
        """Convert to API response format."""
        response = {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "resource_subtype": self.resource_subtype,
            "text": self.text,
            "html_text": self.html_text,
            "is_pinned": self.is_pinned,
            "is_edited": self.is_edited,
            "liked": self.liked,
            "num_likes": self.num_likes,
            "type": self.type,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "target": {"gid": self.target_gid, "resource_type": "task"},
        }
        
        if self.created_by_gid:
            response["created_by"] = {"gid": self.created_by_gid, "resource_type": "user"}
        if self.sticker_name:
            response["sticker_name"] = self.sticker_name
            
        return response

