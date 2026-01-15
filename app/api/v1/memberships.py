"""
Memberships API endpoints.

Generic memberships endpoint that provides access to various types of
memberships across the system - workspace, team, project, and portfolio memberships.
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.models.workspace import WorkspaceMembership
from app.models.team import TeamMembership
from app.models.project import ProjectMembership
from app.models.portfolio import PortfolioMembership
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("")
async def get_memberships(
    parent: str = Query(..., description="Parent resource GID"),
    member: Optional[str] = Query(None, description="Filter by member/user GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get memberships for a parent resource.
    
    Returns all memberships associated with the specified parent resource.
    The parent can be a workspace, team, project, or portfolio.
    """
    all_memberships = []
    
    # Check workspace memberships
    result = await db.execute(
        select(WorkspaceMembership).where(WorkspaceMembership.workspace_gid == parent)
    )
    workspace_memberships = result.scalars().all()
    all_memberships.extend(workspace_memberships)
    
    # Check team memberships
    result = await db.execute(
        select(TeamMembership).where(TeamMembership.team_gid == parent)
    )
    team_memberships = result.scalars().all()
    all_memberships.extend(team_memberships)
    
    # Check project memberships
    result = await db.execute(
        select(ProjectMembership).where(ProjectMembership.project_gid == parent)
    )
    project_memberships = result.scalars().all()
    all_memberships.extend(project_memberships)
    
    # Check portfolio memberships
    result = await db.execute(
        select(PortfolioMembership).where(PortfolioMembership.portfolio_gid == parent)
    )
    portfolio_memberships = result.scalars().all()
    all_memberships.extend(portfolio_memberships)
    
    # Filter by member if specified
    if member:
        all_memberships = [m for m in all_memberships if getattr(m, 'user_gid', None) == member]
    
    parser = OptFieldsParser(params.opt_fields)
    membership_responses = [parser.filter(m.to_response()) for m in all_memberships]
    
    paginated = paginate(
        membership_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/memberships",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_membership(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new membership.
    
    Creates a membership associating a user with a parent resource.
    The type of membership created depends on the parent resource type.
    """
    membership_data = data.get("data", {})
    
    parent = membership_data.get("parent")
    member = membership_data.get("member")
    
    if not parent:
        raise ValidationError("parent is required")
    if not member:
        raise ValidationError("member is required")
    
    # Determine parent type and create appropriate membership
    # Try workspace first
    from app.models.workspace import Workspace
    result = await db.execute(select(Workspace).where(Workspace.gid == parent))
    if result.scalar_one_or_none():
        membership = WorkspaceMembership(
            gid=generate_gid(),
            workspace_gid=parent,
            user_gid=member,
            is_admin=membership_data.get("is_admin", False),
            is_active=True,
        )
        db.add(membership)
        await db.commit()
        return wrap_response(membership.to_response())
    
    # Try team
    from app.models.team import Team
    result = await db.execute(select(Team).where(Team.gid == parent))
    if result.scalar_one_or_none():
        membership = TeamMembership(
            gid=generate_gid(),
            team_gid=parent,
            user_gid=member,
            is_admin=membership_data.get("is_admin", False),
        )
        db.add(membership)
        await db.commit()
        return wrap_response(membership.to_response())
    
    # Try project
    from app.models.project import Project
    result = await db.execute(select(Project).where(Project.gid == parent))
    if result.scalar_one_or_none():
        membership = ProjectMembership(
            gid=generate_gid(),
            project_gid=parent,
            user_gid=member,
            access_level=membership_data.get("access_level", "editor"),
            write_access=membership_data.get("write_access", "full_write"),
        )
        db.add(membership)
        await db.commit()
        return wrap_response(membership.to_response())
    
    # Try portfolio
    from app.models.portfolio import Portfolio
    result = await db.execute(select(Portfolio).where(Portfolio.gid == parent))
    if result.scalar_one_or_none():
        membership = PortfolioMembership(
            gid=generate_gid(),
            portfolio_gid=parent,
            user_gid=member,
            access_level=membership_data.get("access_level", "editor"),
        )
        db.add(membership)
        await db.commit()
        return wrap_response(membership.to_response())
    
    raise NotFoundError("Parent", parent)


@router.get("/{membership_gid}")
async def get_membership(
    membership_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a membership by GID.
    
    Returns the complete membership record including access level and permissions.
    """
    # Try to find in all membership types
    result = await db.execute(
        select(WorkspaceMembership).where(WorkspaceMembership.gid == membership_gid)
    )
    membership = result.scalar_one_or_none()
    if membership:
        parser = OptFieldsParser(opt_fields)
        return wrap_response(parser.filter(membership.to_response()))
    
    result = await db.execute(
        select(TeamMembership).where(TeamMembership.gid == membership_gid)
    )
    membership = result.scalar_one_or_none()
    if membership:
        parser = OptFieldsParser(opt_fields)
        return wrap_response(parser.filter(membership.to_response()))
    
    result = await db.execute(
        select(ProjectMembership).where(ProjectMembership.gid == membership_gid)
    )
    membership = result.scalar_one_or_none()
    if membership:
        parser = OptFieldsParser(opt_fields)
        return wrap_response(parser.filter(membership.to_response()))
    
    result = await db.execute(
        select(PortfolioMembership).where(PortfolioMembership.gid == membership_gid)
    )
    membership = result.scalar_one_or_none()
    if membership:
        parser = OptFieldsParser(opt_fields)
        return wrap_response(parser.filter(membership.to_response()))
    
    raise NotFoundError("Membership", membership_gid)


@router.put("/{membership_gid}")
async def update_membership(
    membership_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a membership.
    
    Updates the membership with new access level or admin status.
    """
    update_data = data.get("data", {})
    
    # Try to find and update in all membership types
    result = await db.execute(
        select(WorkspaceMembership).where(WorkspaceMembership.gid == membership_gid)
    )
    membership = result.scalar_one_or_none()
    if membership:
        if "is_admin" in update_data:
            membership.is_admin = update_data["is_admin"]
        await db.commit()
        await db.refresh(membership)
        return wrap_response(membership.to_response())
    
    result = await db.execute(
        select(TeamMembership).where(TeamMembership.gid == membership_gid)
    )
    membership = result.scalar_one_or_none()
    if membership:
        if "is_admin" in update_data:
            membership.is_admin = update_data["is_admin"]
        await db.commit()
        await db.refresh(membership)
        return wrap_response(membership.to_response())
    
    result = await db.execute(
        select(ProjectMembership).where(ProjectMembership.gid == membership_gid)
    )
    membership = result.scalar_one_or_none()
    if membership:
        if "access_level" in update_data:
            membership.access_level = update_data["access_level"]
        if "write_access" in update_data:
            membership.write_access = update_data["write_access"]
        await db.commit()
        await db.refresh(membership)
        return wrap_response(membership.to_response())
    
    result = await db.execute(
        select(PortfolioMembership).where(PortfolioMembership.gid == membership_gid)
    )
    membership = result.scalar_one_or_none()
    if membership:
        if "access_level" in update_data:
            membership.access_level = update_data["access_level"]
        await db.commit()
        await db.refresh(membership)
        return wrap_response(membership.to_response())
    
    raise NotFoundError("Membership", membership_gid)


@router.delete("/{membership_gid}")
async def delete_membership(
    membership_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a membership.
    
    Removes the membership, revoking the user's access to the parent resource.
    """
    # Try to find and delete in all membership types
    result = await db.execute(
        select(WorkspaceMembership).where(WorkspaceMembership.gid == membership_gid)
    )
    membership = result.scalar_one_or_none()
    if membership:
        await db.delete(membership)
        await db.commit()
        return wrap_response({})
    
    result = await db.execute(
        select(TeamMembership).where(TeamMembership.gid == membership_gid)
    )
    membership = result.scalar_one_or_none()
    if membership:
        await db.delete(membership)
        await db.commit()
        return wrap_response({})
    
    result = await db.execute(
        select(ProjectMembership).where(ProjectMembership.gid == membership_gid)
    )
    membership = result.scalar_one_or_none()
    if membership:
        await db.delete(membership)
        await db.commit()
        return wrap_response({})
    
    result = await db.execute(
        select(PortfolioMembership).where(PortfolioMembership.gid == membership_gid)
    )
    membership = result.scalar_one_or_none()
    if membership:
        await db.delete(membership)
        await db.commit()
        return wrap_response({})
    
    raise NotFoundError("Membership", membership_gid)

