from typing import Any, Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError
from app.models.workspace import WorkspaceMembership
from app.models.user_task_list import UserTaskList
from app.models.user_favorites import UserFavorite
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response, wrap_list_response


router = APIRouter()




@router.get("")
async def get_users(
    workspace: Optional[str] = Query(None, description="Workspace GID to filter users"),
    team: Optional[str] = Query(None, description="Team GID to filter users"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get multiple users. Can be filtered by workspace or team.
    """
    query = select(User).where(User.is_active == True)
    
    if workspace:
        # Get users in a specific workspace
        query = (
            select(User)
            .join(WorkspaceMembership, User.gid == WorkspaceMembership.user_gid)
            .where(WorkspaceMembership.workspace_gid == workspace)
            .where(WorkspaceMembership.is_active == True)
        )
    
    if team:
        # Get users in a specific team
        from app.models.team import TeamMembership
        query = (
            select(User)
            .join(TeamMembership, User.gid == TeamMembership.user_gid)
            .where(TeamMembership.team_gid == team)
        )
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    user_responses = [parser.filter(u.to_response()) for u in users]
    
    paginated = paginate(
        user_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/users",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.get("/{user_gid}")
async def get_user(
    user_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a single user by GID.
    """
    result = await db.execute(select(User).where(User.gid == user_gid))
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("User", user_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(user.to_response()))


@router.get("/{user_gid}/favorites")
async def get_user_favorites(
    user_gid: str,
    workspace: str = Query(..., description="Workspace GID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a user's favorites in a workspace.
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.gid == user_gid))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", user_gid)
    
    # Get favorites
    query = (
        select(UserFavorite)
        .where(UserFavorite.user_gid == user_gid)
        .where(UserFavorite.workspace_gid == workspace)
    )
    
    if resource_type:
        query = query.where(UserFavorite.resource_type == resource_type)
    
    result = await db.execute(query)
    favorites = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    favorite_responses = [parser.filter(f.to_response()) for f in favorites]
    
    paginated = paginate(
        favorite_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/users/{user_gid}/favorites",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.get("/{user_gid}/user_task_list")
async def get_user_task_list(
    user_gid: str,
    workspace: str = Query(..., description="Workspace GID"),
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a user's task list (My Tasks) in a workspace.
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.gid == user_gid))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", user_gid)
    
    # Get user task list
    result = await db.execute(
        select(UserTaskList)
        .where(UserTaskList.owner_gid == user_gid)
        .where(UserTaskList.workspace_gid == workspace)
    )
    task_list = result.scalar_one_or_none()
    
    if not task_list:
        raise NotFoundError("UserTaskList", f"{user_gid}/{workspace}")
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(task_list.to_response()))


@router.get("/{user_gid}/teams")
async def get_user_teams(
    user_gid: str,
    organization: str = Query(..., description="Organization/Workspace GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get teams a user belongs to in an organization.
    """
    from app.models.team import Team, TeamMembership
    
    # Verify user exists
    result = await db.execute(select(User).where(User.gid == user_gid))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", user_gid)
    
    # Get user's teams
    query = (
        select(Team)
        .join(TeamMembership, Team.gid == TeamMembership.team_gid)
        .where(TeamMembership.user_gid == user_gid)
        .where(Team.workspace_gid == organization)
    )
    
    result = await db.execute(query)
    teams = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    team_responses = [parser.filter(t.to_response()) for t in teams]
    
    paginated = paginate(
        team_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/users/{user_gid}/teams",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.get("/{user_gid}/workspace_memberships")
async def get_user_workspace_memberships(
    user_gid: str,
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a user's workspace memberships.
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.gid == user_gid))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", user_gid)
    
    # Get workspace memberships
    result = await db.execute(
        select(WorkspaceMembership)
        .where(WorkspaceMembership.user_gid == user_gid)
        .where(WorkspaceMembership.is_active == True)
    )
    memberships = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    membership_responses = [parser.filter(m.to_response()) for m in memberships]
    
    paginated = paginate(
        membership_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/users/{user_gid}/workspace_memberships",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }

