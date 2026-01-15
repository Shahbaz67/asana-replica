from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.models.user import User
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.portfolio import Portfolio, PortfolioMembership, PortfolioItem
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate,
    AddItemRequest, RemoveItemRequest,
    AddMembersRequest, RemoveMembersRequest,
)
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()
membership_router = APIRouter()


@router.get("")
async def get_portfolios(
    workspace: str = Query(..., description="Workspace GID"),
    owner: Optional[str] = Query(None, description="Owner user GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get portfolios in a workspace.
    """
    query = select(Portfolio).where(Portfolio.workspace_gid == workspace)
    
    if owner:
        query = query.where(Portfolio.owner_gid == owner)
    
    result = await db.execute(query.order_by(Portfolio.name))
    portfolios = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    portfolio_responses = [parser.filter(p.to_response()) for p in portfolios]
    
    paginated = paginate(
        portfolio_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/portfolios",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_portfolio(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new portfolio.
    """
    portfolio_data = PortfolioCreate(**data.get("data", {}))
    
    # Verify workspace exists
    result = await db.execute(select(Workspace).where(Workspace.gid == portfolio_data.workspace))
    if not result.scalar_one_or_none():
        raise NotFoundError("Workspace", portfolio_data.workspace)
    
    portfolio = Portfolio(
        gid=generate_gid(),
        name=portfolio_data.name,
        color=portfolio_data.color,
        public=portfolio_data.public,
        workspace_gid=portfolio_data.workspace,
    )
    db.add(portfolio)
    await db.flush()
    
    # Add owner as member
    membership = PortfolioMembership(
        gid=generate_gid(),
        portfolio_gid=portfolio.gid,
        access_level="admin",
    )
    db.add(membership)
    
    # Add additional members if specified
    if portfolio_data.members:
        for user_gid in portfolio_data.members:
                member = PortfolioMembership(
                    gid=generate_gid(),
                    portfolio_gid=portfolio.gid,
                    user_gid=user_gid,
                    access_level="editor",
                )
                db.add(member)
    
    await db.commit()
    
    return wrap_response(portfolio.to_response())


@router.get("/{portfolio_gid}")
async def get_portfolio(
    portfolio_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a portfolio by GID.
    """
    result = await db.execute(select(Portfolio).where(Portfolio.gid == portfolio_gid))
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise NotFoundError("Portfolio", portfolio_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(portfolio.to_response()))


@router.put("/{portfolio_gid}")
async def update_portfolio(
    portfolio_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a portfolio.
    """
    result = await db.execute(select(Portfolio).where(Portfolio.gid == portfolio_gid))
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise NotFoundError("Portfolio", portfolio_gid)
    
    update_data = PortfolioUpdate(**data.get("data", {}))
    
    if update_data.name is not None:
        portfolio.name = update_data.name
    if update_data.color is not None:
        portfolio.color = update_data.color
    if update_data.public is not None:
        portfolio.public = update_data.public
    
    await db.commit()
    await db.refresh(portfolio)
    
    return wrap_response(portfolio.to_response())


@router.delete("/{portfolio_gid}")
async def delete_portfolio(
    portfolio_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a portfolio.
    """
    result = await db.execute(select(Portfolio).where(Portfolio.gid == portfolio_gid))
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise NotFoundError("Portfolio", portfolio_gid)
    
    await db.delete(portfolio)
    await db.commit()
    
    return wrap_response({})


@router.get("/{portfolio_gid}/items")
async def get_portfolio_items(
    portfolio_gid: str,
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get projects in a portfolio.
    """
    result = await db.execute(select(Portfolio).where(Portfolio.gid == portfolio_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Portfolio", portfolio_gid)
    
    result = await db.execute(
        select(Project)
        .join(PortfolioItem, Project.gid == PortfolioItem.project_gid)
        .where(PortfolioItem.portfolio_gid == portfolio_gid)
        .order_by(PortfolioItem.order)
    )
    projects = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    project_responses = [parser.filter(p.to_response()) for p in projects]
    
    paginated = paginate(
        project_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/portfolios/{portfolio_gid}/items",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("/{portfolio_gid}/addItem")
async def add_portfolio_item(
    portfolio_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a project to a portfolio.
    """
    result = await db.execute(select(Portfolio).where(Portfolio.gid == portfolio_gid))
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise NotFoundError("Portfolio", portfolio_gid)
    
    request_data = AddItemRequest(**data.get("data", {}))
    
    # Verify project exists
    result = await db.execute(select(Project).where(Project.gid == request_data.item))
    if not result.scalar_one_or_none():
        raise NotFoundError("Project", request_data.item)
    
    # Check if already in portfolio
    result = await db.execute(
        select(PortfolioItem)
        .where(PortfolioItem.portfolio_gid == portfolio_gid)
        .where(PortfolioItem.project_gid == request_data.item)
    )
    if result.scalar_one_or_none():
        return wrap_response(portfolio.to_response())
    
    # Get max order
    result = await db.execute(
        select(PortfolioItem)
        .where(PortfolioItem.portfolio_gid == portfolio_gid)
        .order_by(PortfolioItem.order.desc())
        .limit(1)
    )
    last_item = result.scalar_one_or_none()
    order = (last_item.order + 1) if last_item else 0
    
    item = PortfolioItem(
        gid=generate_gid(),
        portfolio_gid=portfolio_gid,
        project_gid=request_data.item,
        order=order,
    )
    db.add(item)
    await db.commit()
    
    return wrap_response(portfolio.to_response())


@router.post("/{portfolio_gid}/removeItem")
async def remove_portfolio_item(
    portfolio_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove a project from a portfolio.
    """
    result = await db.execute(select(Portfolio).where(Portfolio.gid == portfolio_gid))
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise NotFoundError("Portfolio", portfolio_gid)
    
    request_data = RemoveItemRequest(**data.get("data", {}))
    
    result = await db.execute(
        select(PortfolioItem)
        .where(PortfolioItem.portfolio_gid == portfolio_gid)
        .where(PortfolioItem.project_gid == request_data.item)
    )
    item = result.scalar_one_or_none()
    
    if item:
        await db.delete(item)
        await db.commit()
    
    return wrap_response(portfolio.to_response())


@router.post("/{portfolio_gid}/addMembers")
async def add_portfolio_members(
    portfolio_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add members to a portfolio.
    """
    result = await db.execute(select(Portfolio).where(Portfolio.gid == portfolio_gid))
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise NotFoundError("Portfolio", portfolio_gid)
    
    members_str = data.get("data", {}).get("members", "")
    member_gids = [m.strip() for m in members_str.split(",") if m.strip()]
    
    for user_gid in member_gids:
        result = await db.execute(
            select(PortfolioMembership)
            .where(PortfolioMembership.portfolio_gid == portfolio_gid)
            .where(PortfolioMembership.user_gid == user_gid)
        )
        if not result.scalar_one_or_none():
            membership = PortfolioMembership(
                gid=generate_gid(),
                portfolio_gid=portfolio_gid,
                user_gid=user_gid,
                access_level="editor",
            )
            db.add(membership)
    
    await db.commit()
    
    return wrap_response(portfolio.to_response())


@router.post("/{portfolio_gid}/removeMembers")
async def remove_portfolio_members(
    portfolio_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove members from a portfolio.
    """
    result = await db.execute(select(Portfolio).where(Portfolio.gid == portfolio_gid))
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise NotFoundError("Portfolio", portfolio_gid)
    
    members_str = data.get("data", {}).get("members", "")
    member_gids = [m.strip() for m in members_str.split(",") if m.strip()]
    
    for user_gid in member_gids:
        result = await db.execute(
            select(PortfolioMembership)
            .where(PortfolioMembership.portfolio_gid == portfolio_gid)
            .where(PortfolioMembership.user_gid == user_gid)
        )
        membership = result.scalar_one_or_none()
        if membership:
            await db.delete(membership)
    
    await db.commit()
    
    return wrap_response(portfolio.to_response())


# Portfolio Memberships Router
@membership_router.get("/{portfolio_membership_gid}")
async def get_portfolio_membership(
    portfolio_membership_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a portfolio membership by GID.
    """
    result = await db.execute(
        select(PortfolioMembership).where(PortfolioMembership.gid == portfolio_membership_gid)
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise NotFoundError("PortfolioMembership", portfolio_membership_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(membership.to_response()))


@membership_router.get("")
async def get_portfolio_memberships(
    portfolio: Optional[str] = Query(None, description="Portfolio GID"),
    user: Optional[str] = Query(None, description="User GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get portfolio memberships.
    """
    query = select(PortfolioMembership)
    
    if portfolio:
        query = query.where(PortfolioMembership.portfolio_gid == portfolio)
    if user:
        query = query.where(PortfolioMembership.user_gid == user)
    
    result = await db.execute(query)
    memberships = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    membership_responses = [parser.filter(m.to_response()) for m in memberships]
    
    paginated = paginate(
        membership_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/portfolio_memberships",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }

