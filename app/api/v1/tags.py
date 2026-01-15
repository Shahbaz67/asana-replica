from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.models.workspace import Workspace
from app.models.tag import Tag
from app.models.task import Task, TaskTag
from app.schemas.tag import TagCreate, TagUpdate
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("")
async def get_tags(
    workspace: str = Query(..., description="Workspace GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get tags in a workspace.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace))
    if not result.scalar_one_or_none():
        raise NotFoundError("Workspace", workspace)
    
    result = await db.execute(
        select(Tag)
        .where(Tag.workspace_gid == workspace)
        .order_by(Tag.name)
    )
    tags = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    tag_responses = [parser.filter(t.to_response()) for t in tags]
    
    paginated = paginate(
        tag_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/tags",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_tag(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new tag in a workspace.
    """
    tag_data = TagCreate(**data.get("data", {}))
    
    # Verify workspace exists
    result = await db.execute(select(Workspace).where(Workspace.gid == tag_data.workspace))
    if not result.scalar_one_or_none():
        raise NotFoundError("Workspace", tag_data.workspace)
    
    tag = Tag(
        gid=generate_gid(),
        name=tag_data.name,
        color=tag_data.color,
        notes=tag_data.notes,
        workspace_gid=tag_data.workspace,
    )
    db.add(tag)
    await db.commit()
    
    return wrap_response(tag.to_response())


@router.get("/{tag_gid}")
async def get_tag(
    tag_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a tag by GID.
    """
    result = await db.execute(select(Tag).where(Tag.gid == tag_gid))
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise NotFoundError("Tag", tag_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(tag.to_response()))


@router.put("/{tag_gid}")
async def update_tag(
    tag_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a tag.
    """
    result = await db.execute(select(Tag).where(Tag.gid == tag_gid))
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise NotFoundError("Tag", tag_gid)
    
    update_data = TagUpdate(**data.get("data", {}))
    
    if update_data.name is not None:
        tag.name = update_data.name
    if update_data.color is not None:
        tag.color = update_data.color
    if update_data.notes is not None:
        tag.notes = update_data.notes
    
    await db.commit()
    await db.refresh(tag)
    
    return wrap_response(tag.to_response())


@router.delete("/{tag_gid}")
async def delete_tag(
    tag_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a tag.
    """
    result = await db.execute(select(Tag).where(Tag.gid == tag_gid))
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise NotFoundError("Tag", tag_gid)
    
    await db.delete(tag)
    await db.commit()
    
    return wrap_response({})


@router.get("/{tag_gid}/tasks")
async def get_tag_tasks(
    tag_gid: str,
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get tasks with a specific tag.
    """
    result = await db.execute(select(Tag).where(Tag.gid == tag_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Tag", tag_gid)
    
    result = await db.execute(
        select(Task)
        .join(TaskTag, Task.gid == TaskTag.task_gid)
        .where(TaskTag.tag_gid == tag_gid)
        .order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    task_responses = [parser.filter(t.to_response()) for t in tasks]
    
    paginated = paginate(
        task_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/tags/{tag_gid}/tasks",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_tag_for_workspace(
    workspace: str = Query(..., description="Workspace GID"),
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a tag in a workspace.
    
    Alternative endpoint to create a tag specifying the workspace via query parameter.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace))
    if not result.scalar_one_or_none():
        raise NotFoundError("Workspace", workspace)
    
    tag_data = data.get("data", {})
    
    tag = Tag(
        gid=generate_gid(),
        name=tag_data.get("name", "New Tag"),
        color=tag_data.get("color"),
        notes=tag_data.get("notes"),
        workspace_gid=workspace,
    )
    db.add(tag)
    await db.commit()
    
    return wrap_response(tag.to_response())


@router.get("/workspaces/{workspace_gid}/tags")
async def get_tags_for_workspace(
    workspace_gid: str,
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get tags in a workspace (alternative endpoint).
    
    Returns all tags in the specified workspace.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Workspace", workspace_gid)
    
    result = await db.execute(
        select(Tag)
        .where(Tag.workspace_gid == workspace_gid)
        .order_by(Tag.name)
    )
    tags = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    tag_responses = [parser.filter(t.to_response()) for t in tags]
    
    paginated = paginate(
        tag_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/workspaces/{workspace_gid}/tags",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


