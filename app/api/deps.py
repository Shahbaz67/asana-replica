from typing import Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.config import settings


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


class CommonQueryParams:
    """Common query parameters for list endpoints."""
    
    def __init__(
        self,
        limit: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
        offset: Optional[str] = Query(default=None),
        opt_fields: Optional[str] = Query(default=None, description="Comma-separated list of fields to include"),
    ):
        self.limit = limit
        self.offset = offset
        self.opt_fields = opt_fields


class WorkspaceQueryParams:
    """Query parameters that include workspace filter."""
    
    def __init__(
        self,
        workspace: Optional[str] = Query(default=None, description="Workspace GID to filter by"),
        limit: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
        offset: Optional[str] = Query(default=None),
        opt_fields: Optional[str] = Query(default=None),
    ):
        self.workspace = workspace
        self.limit = limit
        self.offset = offset
        self.opt_fields = opt_fields


class ProjectQueryParams:
    """Query parameters that include project filter."""
    
    def __init__(
        self,
        project: Optional[str] = Query(default=None, description="Project GID to filter by"),
        workspace: Optional[str] = Query(default=None, description="Workspace GID to filter by"),
        limit: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
        offset: Optional[str] = Query(default=None),
        opt_fields: Optional[str] = Query(default=None),
    ):
        self.project = project
        self.workspace = workspace
        self.limit = limit
        self.offset = offset
        self.opt_fields = opt_fields


class TaskQueryParams:
    """Query parameters for task list endpoints."""
    
    def __init__(
        self,
        project: Optional[str] = Query(default=None, description="Project GID to filter by"),
        section: Optional[str] = Query(default=None, description="Section GID to filter by"),
        workspace: Optional[str] = Query(default=None, description="Workspace GID to filter by"),
        assignee: Optional[str] = Query(default=None, description="Assignee user GID or 'me'"),
        completed_since: Optional[str] = Query(default=None, description="Only return tasks completed after this time"),
        modified_since: Optional[str] = Query(default=None, description="Only return tasks modified after this time"),
        limit: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
        offset: Optional[str] = Query(default=None),
        opt_fields: Optional[str] = Query(default=None),
    ):
        self.project = project
        self.section = section
        self.workspace = workspace
        self.assignee = assignee
        self.completed_since = completed_since
        self.modified_since = modified_since
        self.limit = limit
        self.offset = offset
        self.opt_fields = opt_fields

