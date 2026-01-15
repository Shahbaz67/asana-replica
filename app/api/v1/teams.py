from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.core.security import generate_gid
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMembership
from app.models.team import Team, TeamMembership
from app.schemas.team import TeamCreate, TeamUpdate, AddUserToTeamRequest
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()
membership_router = APIRouter()


@router.get("")
async def get_teams(
    workspace: Optional[str] = Query(None, description="Workspace/Organization GID"),
    user: Optional[str] = Query(None, description="User GID to filter teams"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get teams in an organization, optionally filtered by user.
    """
    query = select(Team)
    
    if workspace:
        query = query.where(Team.workspace_gid == workspace)
    
    if user:
        query = (
            query.join(TeamMembership, Team.gid == TeamMembership.team_gid)
            .where(TeamMembership.user_gid == user)
        )
    
    result = await db.execute(query)
    teams = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    team_responses = [parser.filter(t.to_response()) for t in teams]
    
    paginated = paginate(
        team_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/teams",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_team(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new team in an organization.
    """
    team_data = TeamCreate(**data.get("data", {}))
    
    # Verify workspace exists
    result = await db.execute(select(Workspace).where(Workspace.gid == team_data.organization))
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise NotFoundError("Workspace", team_data.organization)
    
    # Check if user is member of workspace
    result = await db.execute(
        select(WorkspaceMembership)
        .where(WorkspaceMembership.workspace_gid == team_data.organization)
        .where(WorkspaceMembership.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise ForbiddenError("You must be a member of the organization to create teams")
    
    team = Team(
        gid=generate_gid(),
        name=team_data.name,
        description=team_data.description,
        html_description=team_data.html_description,
        visibility=team_data.visibility,
        workspace_gid=team_data.organization,
    )
    db.add(team)
    await db.flush()
    
    # Add creator as admin
    membership = TeamMembership(
        gid=generate_gid(),
        team_gid=team.gid,
        is_admin=True,
    )
    db.add(membership)
    
    await db.commit()
    
    return wrap_response(team.to_response())


@router.get("/{team_gid}")
async def get_team(
    team_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a team by GID.
    """
    result = await db.execute(select(Team).where(Team.gid == team_gid))
    team = result.scalar_one_or_none()
    
    if not team:
        raise NotFoundError("Team", team_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(team.to_response()))


@router.put("/{team_gid}")
async def update_team(
    team_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a team.
    """
    result = await db.execute(select(Team).where(Team.gid == team_gid))
    team = result.scalar_one_or_none()
    
    if not team:
        raise NotFoundError("Team", team_gid)
    
    # Check if user is team admin
    result = await db.execute(
        select(TeamMembership)
        .where(TeamMembership.team_gid == team_gid)
        .where(TeamMembership.is_admin == True)
    )
    if not result.scalar_one_or_none():
        raise ForbiddenError("Only team admins can update team settings")
    
    update_data = TeamUpdate(**data.get("data", {}))
    
    if update_data.name is not None:
        team.name = update_data.name
    if update_data.description is not None:
        team.description = update_data.description
    if update_data.html_description is not None:
        team.html_description = update_data.html_description
    if update_data.visibility is not None:
        team.visibility = update_data.visibility
    
    await db.commit()
    await db.refresh(team)
    
    return wrap_response(team.to_response())


@router.post("/{team_gid}/addUser")
async def add_user_to_team(
    team_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a user to a team.
    """
    result = await db.execute(select(Team).where(Team.gid == team_gid))
    team = result.scalar_one_or_none()
    
    if not team:
        raise NotFoundError("Team", team_gid)
    
    request_data = AddUserToTeamRequest(**data.get("data", {}))
    user_gid = request_data.user
    
    # Verify user exists
    result = await db.execute(select(User).where(User.gid == user_gid))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", user_gid)
    
    # Check if already a member
    result = await db.execute(
        select(TeamMembership)
        .where(TeamMembership.team_gid == team_gid)
        .where(TeamMembership.user_gid == user_gid)
    )
    if result.scalar_one_or_none():
        return wrap_response(team.to_response())
    
    # Create membership
    membership = TeamMembership(
        gid=generate_gid(),
        user_gid=user_gid,
        team_gid=team_gid,
        is_admin=False,
    )
    db.add(membership)
    await db.commit()
    
    return wrap_response(team.to_response())


@router.post("/{team_gid}/removeUser")
async def remove_user_from_team(
    team_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove a user from a team.
    """
    result = await db.execute(select(Team).where(Team.gid == team_gid))
    team = result.scalar_one_or_none()
    
    if not team:
        raise NotFoundError("Team", team_gid)
    
    user_gid = data.get("data", {}).get("user")
    
    # Find membership
    result = await db.execute(
        select(TeamMembership)
        .where(TeamMembership.team_gid == team_gid)
        .where(TeamMembership.user_gid == user_gid)
    )
    membership = result.scalar_one_or_none()
    
    if membership:
        await db.delete(membership)
        await db.commit()
    
    return wrap_response(team.to_response())


@router.get("/{team_gid}/users")
async def get_team_users(
    team_gid: str,
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get all users in a team.
    """
    result = await db.execute(select(Team).where(Team.gid == team_gid))
    team = result.scalar_one_or_none()
    if not team:
        raise NotFoundError("Team", team_gid)
    
    query = (
        select(User)
        .join(TeamMembership, User.gid == TeamMembership.user_gid)
        .where(TeamMembership.team_gid == team_gid)
    )
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    user_responses = [parser.filter(u.to_response()) for u in users]
    
    paginated = paginate(
        user_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/teams/{team_gid}/users",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


# Team Memberships Router
@membership_router.get("/{team_membership_gid}")
async def get_team_membership(
    team_membership_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a team membership by GID.
    """
    result = await db.execute(
        select(TeamMembership).where(TeamMembership.gid == team_membership_gid)
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise NotFoundError("TeamMembership", team_membership_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(membership.to_response()))


@membership_router.get("")
async def get_team_memberships(
    team: Optional[str] = Query(None, description="Team GID"),
    user: Optional[str] = Query(None, description="User GID"),
    workspace: Optional[str] = Query(None, description="Workspace GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get team memberships, filtered by team, user, or workspace.
    """
    query = select(TeamMembership)
    
    if team:
        query = query.where(TeamMembership.team_gid == team)
    
    if user:
        query = query.where(TeamMembership.user_gid == user)
    
    if workspace:
        query = (
            query.join(Team, TeamMembership.team_gid == Team.gid)
            .where(Team.workspace_gid == workspace)
        )
    
    result = await db.execute(query)
    memberships = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    membership_responses = [parser.filter(m.to_response()) for m in memberships]
    
    paginated = paginate(
        membership_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/team_memberships",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }

