"""
Workspaces API endpoints.

A workspace is the highest-level organizational unit in Asana. All projects
and tasks have an associated workspace.

Based on: https://developers.asana.com/reference/workspaces
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ForbiddenError
from app.core.security import generate_gid
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMembership
from app.models.user_task_list import UserTaskList
from app.schemas.workspace import (
    WorkspaceUpdate, 
    AddUserRequest, 
    RemoveUserRequest,
)
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()
membership_router = APIRouter()


# =============================================================================
# WORKSPACES (6 APIs per Asana spec)
# =============================================================================

@router.get("")
async def get_workspaces(
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get multiple workspaces.
    
    Returns the compact records for all workspaces visible to the authorized user.
    """
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


@router.get("/{workspace_gid}")
async def get_workspace(
    workspace_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a workspace.
    
    Returns the full workspace record for a single workspace.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace_gid))
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise NotFoundError("Workspace", workspace_gid)
    
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
    
    A specific, existing workspace can be updated by making a PUT request on
    the URL for that workspace. Only the fields provided in the data block
    will be updated; any unspecified fields will remain unchanged.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace_gid))
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise NotFoundError("Workspace", workspace_gid)
    
    update_data = WorkspaceUpdate(**data.get("data", {}))
    
    if update_data.name is not None:
        workspace.name = update_data.name
    
    await db.commit()
    await db.refresh(workspace)
    
    return wrap_response(workspace.to_response())


@router.post("/{workspace_gid}/addUser")
async def add_user_for_workspace(
    workspace_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a user to a workspace or organization.
    
    Add a user to a workspace or organization. The user can be referenced
    by their globally unique user ID or their email address.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace_gid))
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise NotFoundError("Workspace", workspace_gid)
    
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
async def remove_user_for_workspace(
    workspace_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove a user from a workspace or organization.
    
    Remove a user from a workspace or organization. The user making this
    call must be an admin in the workspace.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace_gid))
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise NotFoundError("Workspace", workspace_gid)
    
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


@router.get("/{workspace_gid}/events")
async def get_workspace_events(
    workspace_gid: str,
    sync: Optional[str] = Query(None, description="Sync token from last request"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get workspace events.
    
    Returns the full record for all events that have occurred since the
    sync token was created.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace_gid))
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise NotFoundError("Workspace", workspace_gid)
    
    # Generate or validate sync token
    if not sync:
        sync_token = f"sync:{workspace_gid}:{generate_gid()}"
    else:
        sync_token = sync
    
    # Return events (simplified - would use event store in production)
    return {
        "data": [],
        "sync": sync_token,
        "has_more": False,
    }


# =============================================================================
# WORKSPACE MEMBERSHIPS (3 APIs per Asana spec)
# Paths: 
# - GET /workspace_memberships/{gid}
# - GET /users/{user_gid}/workspace_memberships (in users.py)
# - GET /workspaces/{workspace_gid}/workspace_memberships
# =============================================================================

@membership_router.get("/{workspace_membership_gid}")
async def get_workspace_membership(
    workspace_membership_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a workspace membership.
    
    Returns the complete workspace membership record for a single
    workspace membership.
    """
    result = await db.execute(
        select(WorkspaceMembership).where(WorkspaceMembership.gid == workspace_membership_gid)
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise NotFoundError("WorkspaceMembership", workspace_membership_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(membership.to_response()))


# Note: GET /users/{user_gid}/workspace_memberships is handled in users.py

@router.get("/{workspace_gid}/workspace_memberships")
async def get_workspace_memberships_for_workspace(
    workspace_gid: str,
    user: Optional[str] = Query(None, description="Filter by user GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get the workspace memberships for a workspace.
    
    Returns the compact workspace membership records for the workspace.
    """
    query = (
        select(WorkspaceMembership)
        .where(WorkspaceMembership.workspace_gid == workspace_gid)
        .where(WorkspaceMembership.is_active == True)
    )
    
    if user:
        query = query.where(WorkspaceMembership.user_gid == user)
    
    result = await db.execute(query)
    memberships = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    membership_responses = [parser.filter(m.to_response()) for m in memberships]
    
    paginated = paginate(
        membership_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/workspaces/{workspace_gid}/workspace_memberships",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }
