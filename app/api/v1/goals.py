from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError
from app.core.security import generate_gid
from app.models.workspace import Workspace
from app.models.team import Team
from app.models.goal import Goal, GoalRelationship, StatusUpdate, GoalMembership
from app.schemas.goal import (
    GoalCreate, GoalUpdate,
    GoalRelationshipCreate, GoalRelationshipUpdate,
    StatusUpdateCreate,
)
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()
relationship_router = APIRouter()
status_router = APIRouter()
membership_router = APIRouter()


@router.get("")
async def get_goals(
    workspace: str = Query(..., description="Workspace GID"),
    team: Optional[str] = Query(None, description="Team GID"),
    time_periods: Optional[str] = Query(None, description="Time period GIDs"),
    is_workspace_level: Optional[bool] = Query(None),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get goals in a workspace.
    """
    query = select(Goal).where(Goal.workspace_gid == workspace)
    
    if team:
        query = query.where(Goal.team_gid == team)
    
    if is_workspace_level is not None:
        query = query.where(Goal.is_workspace_level == is_workspace_level)
    
    if time_periods:
        period_gids = [p.strip() for p in time_periods.split(",")]
        query = query.where(Goal.time_period_gid.in_(period_gids))
    
    result = await db.execute(query.order_by(Goal.name))
    goals = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    goal_responses = [parser.filter(g.to_response()) for g in goals]
    
    paginated = paginate(
        goal_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/goals",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_goal(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new goal.
    """
    goal_data = GoalCreate(**data.get("data", {}))
    
    # Verify workspace exists
    result = await db.execute(select(Workspace).where(Workspace.gid == goal_data.workspace))
    if not result.scalar_one_or_none():
        raise NotFoundError("Workspace", goal_data.workspace)
    
    goal = Goal(
        gid=generate_gid(),
        name=goal_data.name,
        notes=goal_data.notes,
        html_notes=goal_data.html_notes,
        workspace_gid=goal_data.workspace,
        team_gid=goal_data.team,
        owner_gid=goal_data.owner,
        time_period_gid=goal_data.time_period,
        due_on=goal_data.due_on,
        start_on=goal_data.start_on,
        is_workspace_level=goal_data.is_workspace_level,
        status=goal_data.status,
    )
    
    # Set metric if provided
    if goal_data.metric:
        goal.metric_type = goal_data.metric.metric_type
        goal.metric_unit = goal_data.metric.unit
        goal.metric_precision = goal_data.metric.precision
        goal.metric_currency_code = goal_data.metric.currency_code
        goal.metric_initial_number_value = goal_data.metric.initial_number_value
        goal.metric_target_number_value = goal_data.metric.target_number_value
        goal.metric_current_number_value = goal_data.metric.current_number_value
    
    db.add(goal)
    await db.commit()
    
    return wrap_response(goal.to_response())


@router.get("/{goal_gid}")
async def get_goal(
    goal_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a goal by GID.
    """
    result = await db.execute(select(Goal).where(Goal.gid == goal_gid))
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise NotFoundError("Goal", goal_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(goal.to_response()))


@router.put("/{goal_gid}")
async def update_goal(
    goal_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a goal.
    """
    result = await db.execute(select(Goal).where(Goal.gid == goal_gid))
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise NotFoundError("Goal", goal_gid)
    
    update_data = GoalUpdate(**data.get("data", {}))
    
    for field, value in update_data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(goal, field, value)
    
    await db.commit()
    await db.refresh(goal)
    
    return wrap_response(goal.to_response())


@router.delete("/{goal_gid}")
async def delete_goal(
    goal_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a goal.
    """
    result = await db.execute(select(Goal).where(Goal.gid == goal_gid))
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise NotFoundError("Goal", goal_gid)
    
    await db.delete(goal)
    await db.commit()
    
    return wrap_response({})


@router.post("/{goal_gid}/setMetric")
async def set_goal_metric(
    goal_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Set the metric for a goal.
    """
    result = await db.execute(select(Goal).where(Goal.gid == goal_gid))
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise NotFoundError("Goal", goal_gid)
    
    metric_data = data.get("data", {}).get("metric", {})
    
    goal.metric_type = metric_data.get("metric_type")
    goal.metric_unit = metric_data.get("unit")
    goal.metric_precision = metric_data.get("precision", 0)
    goal.metric_currency_code = metric_data.get("currency_code")
    goal.metric_initial_number_value = metric_data.get("initial_number_value")
    goal.metric_target_number_value = metric_data.get("target_number_value")
    goal.metric_current_number_value = metric_data.get("current_number_value")
    
    await db.commit()
    await db.refresh(goal)
    
    return wrap_response(goal.to_response())


@router.post("/{goal_gid}/setMetricCurrentValue")
async def set_goal_metric_current_value(
    goal_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Set the current value of a goal's metric.
    """
    result = await db.execute(select(Goal).where(Goal.gid == goal_gid))
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise NotFoundError("Goal", goal_gid)
    
    current_value = data.get("data", {}).get("current_number_value")
    if current_value is not None:
        goal.metric_current_number_value = current_value
    
    await db.commit()
    await db.refresh(goal)
    
    return wrap_response(goal.to_response())


@router.post("/{goal_gid}/addSupportingRelationship")
async def add_supporting_relationship(
    goal_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a supporting goal relationship.
    """
    result = await db.execute(select(Goal).where(Goal.gid == goal_gid))
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise NotFoundError("Goal", goal_gid)
    
    relationship_data = GoalRelationshipCreate(**data.get("data", {}))
    
    relationship = GoalRelationship(
        gid=generate_gid(),
        supporting_goal_gid=relationship_data.supporting_resource,
        supported_goal_gid=goal_gid,
        contribution_weight=relationship_data.contribution_weight,
    )
    db.add(relationship)
    await db.commit()
    
    return wrap_response(relationship.to_response())


@router.post("/{goal_gid}/removeSupportingRelationship")
async def remove_supporting_relationship(
    goal_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove a supporting goal relationship.
    """
    supporting_goal_gid = data.get("data", {}).get("supporting_resource")
    
    result = await db.execute(
        select(GoalRelationship)
        .where(GoalRelationship.supported_goal_gid == goal_gid)
        .where(GoalRelationship.supporting_goal_gid == supporting_goal_gid)
    )
    relationship = result.scalar_one_or_none()
    
    if relationship:
        await db.delete(relationship)
        await db.commit()
    
    return wrap_response({})


@router.get("/{goal_gid}/parentGoals")
async def get_parent_goals(
    goal_gid: str,
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get parent goals (goals this goal supports).
    """
    result = await db.execute(
        select(Goal)
        .join(GoalRelationship, Goal.gid == GoalRelationship.supported_goal_gid)
        .where(GoalRelationship.supporting_goal_gid == goal_gid)
    )
    goals = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    goal_responses = [parser.filter(g.to_response()) for g in goals]
    
    return {"data": goal_responses}


# Goal Relationships Router
@relationship_router.get("/{goal_relationship_gid}")
async def get_goal_relationship(
    goal_relationship_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a goal relationship by GID.
    """
    result = await db.execute(
        select(GoalRelationship).where(GoalRelationship.gid == goal_relationship_gid)
    )
    relationship = result.scalar_one_or_none()
    
    if not relationship:
        raise NotFoundError("GoalRelationship", goal_relationship_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(relationship.to_response()))


@relationship_router.put("/{goal_relationship_gid}")
async def update_goal_relationship(
    goal_relationship_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a goal relationship.
    """
    result = await db.execute(
        select(GoalRelationship).where(GoalRelationship.gid == goal_relationship_gid)
    )
    relationship = result.scalar_one_or_none()
    
    if not relationship:
        raise NotFoundError("GoalRelationship", goal_relationship_gid)
    
    update_data = GoalRelationshipUpdate(**data.get("data", {}))
    
    if update_data.contribution_weight is not None:
        relationship.contribution_weight = update_data.contribution_weight
    
    await db.commit()
    await db.refresh(relationship)
    
    return wrap_response(relationship.to_response())


@relationship_router.delete("/{goal_relationship_gid}")
async def delete_goal_relationship(
    goal_relationship_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a goal relationship.
    """
    result = await db.execute(
        select(GoalRelationship).where(GoalRelationship.gid == goal_relationship_gid)
    )
    relationship = result.scalar_one_or_none()
    
    if not relationship:
        raise NotFoundError("GoalRelationship", goal_relationship_gid)
    
    await db.delete(relationship)
    await db.commit()
    
    return wrap_response({})


# Status Updates Router
@status_router.get("/{status_update_gid}")
async def get_status_update(
    status_update_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a status update by GID.
    """
    result = await db.execute(
        select(StatusUpdate).where(StatusUpdate.gid == status_update_gid)
    )
    status_update = result.scalar_one_or_none()
    
    if not status_update:
        raise NotFoundError("StatusUpdate", status_update_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(status_update.to_response()))


@status_router.post("")
async def create_status_update(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a status update for a goal.
    """
    status_data = StatusUpdateCreate(**data.get("data", {}))
    
    # Verify goal exists
    result = await db.execute(select(Goal).where(Goal.gid == status_data.parent))
    goal = result.scalar_one_or_none()
    if not goal:
        raise NotFoundError("Goal", status_data.parent)
    
    status_update = StatusUpdate(
        gid=generate_gid(),
        title=status_data.title,
        text=status_data.text,
        html_text=status_data.html_text,
        status_type=status_data.status_type,
        goal_gid=status_data.parent,
    )
    db.add(status_update)
    
    # Update goal status
    goal.status = status_data.status_type
    
    await db.commit()
    
    return wrap_response(status_update.to_response())


@status_router.delete("/{status_update_gid}")
async def delete_status_update(
    status_update_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a status update.
    """
    result = await db.execute(
        select(StatusUpdate).where(StatusUpdate.gid == status_update_gid)
    )
    status_update = result.scalar_one_or_none()
    
    if not status_update:
        raise NotFoundError("StatusUpdate", status_update_gid)
    
    await db.delete(status_update)
    await db.commit()
    
    return wrap_response({})


@status_router.get("")
async def get_status_updates(
    parent: str = Query(..., description="Parent resource GID (goal or project)"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get status updates for a parent resource.
    
    Returns all status updates for the specified goal or project.
    """
    result = await db.execute(
        select(StatusUpdate)
        .where(StatusUpdate.goal_gid == parent)
        .order_by(StatusUpdate.created_at.desc())
    )
    status_updates = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    update_responses = [parser.filter(s.to_response()) for s in status_updates]
    
    paginated = paginate(
        update_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/status_updates",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


# Additional Goal Relationship endpoints
@relationship_router.get("")
async def get_goal_relationships(
    supported_goal: str = Query(..., description="Supported Goal GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get goal relationships for a supported goal.
    
    Returns all relationships where other goals support the specified goal.
    """
    result = await db.execute(
        select(GoalRelationship)
        .where(GoalRelationship.supported_goal_gid == supported_goal)
    )
    relationships = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    relationship_responses = [parser.filter(r.to_response()) for r in relationships]
    
    paginated = paginate(
        relationship_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/goal_relationships",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@relationship_router.post("")
async def create_goal_relationship(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a goal relationship.
    
    Creates a new supporting relationship between two goals.
    """
    relationship_data = GoalRelationshipCreate(**data.get("data", {}))
    
    relationship = GoalRelationship(
        gid=generate_gid(),
        supporting_goal_gid=relationship_data.supporting_resource,
        supported_goal_gid=relationship_data.supported_goal,
        contribution_weight=relationship_data.contribution_weight,
    )
    db.add(relationship)
    await db.commit()
    
    return wrap_response(relationship.to_response())


# =============================================================================
# GOAL MEMBERSHIPS (2 APIs per Asana spec)
# =============================================================================

@membership_router.get("")
async def get_goal_memberships(
    parent: str = Query(..., description="Goal GID"),
    member: Optional[str] = Query(None, description="Filter by member GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get goal memberships.
    
    Returns the compact goal membership records for a goal.
    """
    query = select(GoalMembership).where(GoalMembership.goal_gid == parent)
    
    if member:
        query = query.where(GoalMembership.member_gid == member)
    
    result = await db.execute(query)
    memberships = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    membership_responses = [parser.filter(m.to_response()) for m in memberships]
    
    paginated = paginate(
        membership_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/goal_memberships",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@membership_router.get("/{goal_membership_gid}")
async def get_goal_membership(
    goal_membership_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a goal membership.
    
    Returns the complete goal membership record for a single goal membership.
    """
    result = await db.execute(
        select(GoalMembership).where(GoalMembership.gid == goal_membership_gid)
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise NotFoundError("GoalMembership", goal_membership_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(membership.to_response()))


@router.post("/{goal_gid}/addFollowers")
async def add_followers_to_goal(
    goal_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a follower to a goal.
    
    Adds followers to a goal. Returns the goal the followers were added to.
    """
    result = await db.execute(select(Goal).where(Goal.gid == goal_gid))
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise NotFoundError("Goal", goal_gid)
    
    followers_str = data.get("data", {}).get("followers", "")
    follower_gids = [f.strip() for f in followers_str.split(",") if f.strip()]
    
    for follower_gid in follower_gids:
        # Check if already a follower
        result = await db.execute(
            select(GoalMembership)
            .where(GoalMembership.goal_gid == goal_gid)
            .where(GoalMembership.member_gid == follower_gid)
        )
        if not result.scalar_one_or_none():
            membership = GoalMembership(
                gid=generate_gid(),
                goal_gid=goal_gid,
                member_gid=follower_gid,
                role="follower",
            )
            db.add(membership)
    
    await db.commit()
    
    return wrap_response(goal.to_response())


@router.post("/{goal_gid}/removeFollowers")
async def remove_followers_from_goal(
    goal_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove a follower from a goal.
    
    Removes followers from a goal. Returns the goal the followers were removed from.
    """
    result = await db.execute(select(Goal).where(Goal.gid == goal_gid))
    goal = result.scalar_one_or_none()
    
    if not goal:
        raise NotFoundError("Goal", goal_gid)
    
    followers_str = data.get("data", {}).get("followers", "")
    follower_gids = [f.strip() for f in followers_str.split(",") if f.strip()]
    
    for follower_gid in follower_gids:
        result = await db.execute(
            select(GoalMembership)
            .where(GoalMembership.goal_gid == goal_gid)
            .where(GoalMembership.member_gid == follower_gid)
        )
        membership = result.scalar_one_or_none()
        if membership:
            await db.delete(membership)
    
    await db.commit()
    
    return wrap_response(goal.to_response())

