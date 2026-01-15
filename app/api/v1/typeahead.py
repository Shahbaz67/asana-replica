from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.api.deps import get_db, CommonQueryParams
from app.models.user import User
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.task import Task, TaskProject
from app.models.tag import Tag
from app.utils.filters import OptFieldsParser


router = APIRouter()


@router.get("/workspaces/{workspace_gid}/typeahead")
async def typeahead_search(
    workspace_gid: str,
    resource_type: str = Query(..., description="Type of resource to search (task, project, tag, user)"),
    query: str = Query(..., description="Search query string"),
    count: int = Query(10, ge=1, le=100, description="Number of results to return"),
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Search for resources by name with typeahead.
    
    This endpoint provides quick search results for typeahead/autocomplete
    functionality. Results are matched against the beginning of words in
    the resource name.
    """
    parser = OptFieldsParser(opt_fields)
    results = []
    
    search_pattern = f"%{query}%"
    
    if resource_type == "task":
        db_query = (
            select(Task)
            .join(TaskProject, Task.gid == TaskProject.task_gid)
            .join(Project, TaskProject.project_gid == Project.gid)
            .where(Project.workspace_gid == workspace_gid)
            .where(Task.name.ilike(search_pattern))
            .limit(count)
        )
        result = await db.execute(db_query)
        tasks = result.scalars().all()
        results = [parser.filter(t.to_response()) for t in tasks]
        
    elif resource_type == "project":
        db_query = (
            select(Project)
            .where(Project.workspace_gid == workspace_gid)
            .where(Project.name.ilike(search_pattern))
            .limit(count)
        )
        result = await db.execute(db_query)
        projects = result.scalars().all()
        results = [parser.filter(p.to_response()) for p in projects]
        
    elif resource_type == "tag":
        db_query = (
            select(Tag)
            .where(Tag.workspace_gid == workspace_gid)
            .where(Tag.name.ilike(search_pattern))
            .limit(count)
        )
        result = await db.execute(db_query)
        tags = result.scalars().all()
        results = [parser.filter(t.to_response()) for t in tags]
        
    elif resource_type == "user":
        from app.models.workspace import WorkspaceMembership
        
        db_query = (
            select(User)
            .join(WorkspaceMembership, User.gid == WorkspaceMembership.user_gid)
            .where(WorkspaceMembership.workspace_gid == workspace_gid)
            .where(WorkspaceMembership.is_active == True)
            .where(
                or_(
                    User.name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                )
            )
            .limit(count)
        )
        result = await db.execute(db_query)
        users = result.scalars().all()
        results = [parser.filter(u.to_response()) for u in users]
    
    return {"data": results}


