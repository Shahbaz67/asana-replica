from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.core.security import generate_gid


class TimestampMixin:
    """Mixin for created_at and modified_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class GIDMixin:
    """Mixin for GID (Global ID) field."""
    gid: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_gid,
        index=True,
    )


class AsanaBase(Base, GIDMixin, TimestampMixin):
    """Base class for all Asana-like models."""
    __abstract__ = True
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


