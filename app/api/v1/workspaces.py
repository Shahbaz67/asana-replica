from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.core.security import generate_gid
from app.models.workspace import Workspace, WorkspaceMembership
from app.models.user_task_list import UserTaskList
from app.schemas.workspace import (
    WorkspaceCreate, 
    WorkspaceUpdate, 
    AddUserRequest, 
    RemoveUserRequest,
)
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()
membership_router = APIRouter()


@router.get("")
async def get_workspaces(
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all workspaces.
    """
    # Get all workspaces
    query = select(Workspace)
    
    result = await db.execute(query)
    workspaces = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    workspace_responses = [parser.filter(w.to_response()) for w in workspaces]
    
    paginated = paginate(
        workspace_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/workspaces",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_workspace(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new workspace.
    """
    workspace_data = WorkspaceCreate(**data.get("data", {}))
    
    workspace = Workspace(
        gid=generate_gid(),
        name=workspace_data.name,
        is_organization=workspace_data.is_organization,
        email_domains=",".join(workspace_data.email_domains) if workspace_data.email_domains else None,
    )
    db.add(workspace)
    await db.flush()
    
    # Add creator as admin
    membership = WorkspaceMembership(
        gid=generate_gid(),
        workspace_gid=workspace.gid,
        is_admin=True,
        is_active=True,
    )
    db.add(membership)
    
    # Create user task list
    task_list = UserTaskList(
        gid=generate_gid(),
        name="My Tasks",
        workspace_gid=workspace.gid,
    )
    db.add(task_list)
    
    await db.commit()
    
    return wrap_response(workspace.to_response())


@router.get("/{workspace_gid}")
async def get_workspace(
    workspace_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a workspace by GID.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace_gid))
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise NotFoundError("Workspace", workspace_gid)
    
    # Check if user has access
    result = await db.execute(
        select(WorkspaceMembership)
        .where(WorkspaceMembership.workspace_gid == workspace_gid)
        .where(WorkspaceMembership.is_active == True)
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise ForbiddenError("You do not have access to this workspace")
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(workspace.to_response()))


@router.put("/{workspace_gid}")
async def update_workspace(
    workspace_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a workspace.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace_gid))
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise NotFoundError("Workspace", workspace_gid)
    
    # Check if user is admin
    result = await db.execute(
        select(WorkspaceMembership)
        .where(WorkspaceMembership.workspace_gid == workspace_gid)
        .where(WorkspaceMembership.is_admin == True)
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise ForbiddenError("Only workspace admins can update workspace settings")
    
    update_data = WorkspaceUpdate(**data.get("data", {}))
    
    if update_data.name is not None:
        workspace.name = update_data.name
    
    await db.commit()
    await db.refresh(workspace)
    
    return wrap_response(workspace.to_response())


@router.post("/{workspace_gid}/addUser")
async def add_user_to_workspace(
    workspace_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a user to a workspace.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace_gid))
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise NotFoundError("Workspace", workspace_gid)
    
    # Check if current user is admin
    result = await db.execute(
        select(WorkspaceMembership)
        .where(WorkspaceMembership.workspace_gid == workspace_gid)
        .where(WorkspaceMembership.is_admin == True)
    )
    if not result.scalar_one_or_none():
        raise ForbiddenError("Only workspace admins can add users")
    
    request_data = AddUserRequest(**data.get("data", {}))
    user_gid = request_data.user
    
    # Verify user exists
    result = await db.execute(select(User).where(User.gid == user_gid))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", user_gid)
    
    # Check if already a member
    result = await db.execute(
        select(WorkspaceMembership)
        .where(WorkspaceMembership.workspace_gid == workspace_gid)
        .where(WorkspaceMembership.user_gid == user_gid)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.is_active = True
        await db.commit()
        return wrap_response(workspace.to_response())
    
    # Create membership
    membership = WorkspaceMembership(
        gid=generate_gid(),
        user_gid=user_gid,
        workspace_gid=workspace_gid,
        is_admin=False,
        is_active=True,
    )
    db.add(membership)
    
    # Create user task list
    task_list = UserTaskList(
        gid=generate_gid(),
        name="My Tasks",
        owner_gid=user_gid,
        workspace_gid=workspace_gid,
    )
    db.add(task_list)
    
    await db.commit()
    
    return wrap_response(workspace.to_response())


@router.post("/{workspace_gid}/removeUser")
async def remove_user_from_workspace(
    workspace_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove a user from a workspace.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace_gid))
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise NotFoundError("Workspace", workspace_gid)
    
    # Check if current user is admin
    result = await db.execute(
        select(WorkspaceMembership)
        .where(WorkspaceMembership.workspace_gid == workspace_gid)
        .where(WorkspaceMembership.is_admin == True)
    )
    if not result.scalar_one_or_none():
        raise ForbiddenError("Only workspace admins can remove users")
    
    request_data = RemoveUserRequest(**data.get("data", {}))
    user_gid = request_data.user
    
    # Find membership
    result = await db.execute(
        select(WorkspaceMembership)
        .where(WorkspaceMembership.workspace_gid == workspace_gid)
        .where(WorkspaceMembership.user_gid == user_gid)
    )
    membership = result.scalar_one_or_none()
    
    if membership:
        membership.is_active = False
        await db.commit()
    
    return wrap_response(workspace.to_response())


@router.get("/{workspace_gid}/users")
async def get_workspace_users(
    workspace_gid: str,
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all users in a workspace.
    """
    # Verify workspace exists and user has access
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace_gid))
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise NotFoundError("Workspace", workspace_gid)
    
    # Get users
    query = (
        select(User)
        .join(WorkspaceMembership, User.gid == WorkspaceMembership.user_gid)
        .where(WorkspaceMembership.workspace_gid == workspace_gid)
        .where(WorkspaceMembership.is_active == True)
    )
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    user_responses = [parser.filter(u.to_response()) for u in users]
    
    paginated = paginate(
        user_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/workspaces/{workspace_gid}/users",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


# Workspace Memberships Router
@membership_router.get("/{workspace_membership_gid}")
async def get_workspace_membership(
    workspace_membership_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a workspace membership by GID.
    """
    result = await db.execute(
        select(WorkspaceMembership).where(WorkspaceMembership.gid == workspace_membership_gid)
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise NotFoundError("WorkspaceMembership", workspace_membership_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(membership.to_response()))

