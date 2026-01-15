from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.core.security import generate_gid
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMembership
from app.models.team import Team
from app.models.project import Project, ProjectMembership, ProjectStatus, ProjectBrief
from app.models.section import Section
from app.models.task import Task, TaskProject
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectDuplicateRequest,
    AddMembersRequest, RemoveMembersRequest, AddFollowersRequest,
    TaskCountsResponse, ProjectStatusCreate,
    ProjectBriefCreate, ProjectBriefUpdate,
)
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()
membership_router = APIRouter()
status_router = APIRouter()
brief_router = APIRouter()


@router.get("")
async def get_projects(
    workspace: Optional[str] = Query(None, description="Workspace GID"),
    team: Optional[str] = Query(None, description="Team GID"),
    archived: Optional[bool] = Query(None, description="Filter by archived status"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get multiple projects.
    """
    query = select(Project)
    
    if workspace:
        query = query.where(Project.workspace_gid == workspace)
    
    if team:
        query = query.where(Project.team_gid == team)
    
    if archived is not None:
        query = query.where(Project.archived == archived)
    
    result = await db.execute(query.order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    project_responses = [parser.filter(p.to_response()) for p in projects]
    
    paginated = paginate(
        project_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/projects",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_project(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new project.
    """
    project_data = ProjectCreate(**data.get("data", {}))
    
    # Verify workspace exists
    result = await db.execute(select(Workspace).where(Workspace.gid == project_data.workspace))
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise NotFoundError("Workspace", project_data.workspace)
    
    # Verify team if provided
    if project_data.team:
        result = await db.execute(select(Team).where(Team.gid == project_data.team))
        if not result.scalar_one_or_none():
            raise NotFoundError("Team", project_data.team)
    
    project = Project(
        gid=generate_gid(),
        name=project_data.name,
        notes=project_data.notes,
        html_notes=project_data.html_notes,
        workspace_gid=project_data.workspace,
        team_gid=project_data.team,
        public=project_data.public,
        color=project_data.color,
        default_view=project_data.default_view,
        due_on=project_data.due_on,
        start_on=project_data.start_on,
        owner_gid=project_data.owner,
    )
    db.add(project)
    await db.flush()
    
    # Add creator as project member
    membership = ProjectMembership(
        gid=generate_gid(),
        project_gid=project.gid,
        access_level="editor",
        write_access="full_write",
    )
    db.add(membership)
    
    # Create default section
    default_section = Section(
        gid=generate_gid(),
        name="Untitled section",
        project_gid=project.gid,
        order=0,
    )
    db.add(default_section)
    
    await db.commit()
    
    return wrap_response(project.to_response())


@router.get("/{project_gid}")
async def get_project(
    project_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a project by GID.
    """
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_gid)
    
    parser = OptFieldsParser(opt_fields)
    response = project.to_response()
    
    # Add members if requested
    if parser.has_field("members"):
        result = await db.execute(
            select(ProjectMembership).where(ProjectMembership.project_gid == project_gid)
        )
        memberships = result.scalars().all()
        response["members"] = [m.to_response() for m in memberships]
    
    return wrap_response(parser.filter(response))


@router.put("/{project_gid}")
async def update_project(
    project_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a project.
    """
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_gid)
    
    update_data = ProjectUpdate(**data.get("data", {}))
    
    for field, value in update_data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(project, field, value)
    
    if update_data.completed and not project.completed_at:
        project.completed_at = datetime.utcnow()
    elif update_data.completed is False:
        project.completed_at = None
    
    await db.commit()
    await db.refresh(project)
    
    return wrap_response(project.to_response())


@router.delete("/{project_gid}")
async def delete_project(
    project_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a project.
    """
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_gid)
    
    await db.delete(project)
    await db.commit()
    
    return wrap_response({})


@router.post("/{project_gid}/duplicate")
async def duplicate_project(
    project_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Duplicate a project.
    """
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_gid)
    
    dup_data = ProjectDuplicateRequest(**data.get("data", {}))
    
    # Create new project
    new_project = Project(
        gid=generate_gid(),
        name=dup_data.name,
        notes=project.notes if "notes" in (dup_data.include or []) else None,
        html_notes=project.html_notes if "notes" in (dup_data.include or []) else None,
        workspace_gid=project.workspace_gid,
        team_gid=dup_data.team or project.team_gid,
        public=project.public,
        color=project.color,
        default_view=project.default_view,
    )
    db.add(new_project)
    await db.flush()
    
    # Add creator as member
    membership = ProjectMembership(
        gid=generate_gid(),
        project_gid=new_project.gid,
        access_level="editor",
        write_access="full_write",
    )
    db.add(membership)
    
    await db.commit()
    
    # Return job response (simplified - immediate completion)
    from app.models.job import Job
    job = Job(
        gid=generate_gid(),
        resource_subtype="duplicate_project",
        status="succeeded",
        new_project_gid=new_project.gid,
    )
    db.add(job)
    await db.commit()
    
    return wrap_response(job.to_response())


@router.get("/{project_gid}/task_counts")
async def get_project_task_counts(
    project_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get task counts for a project.
    """
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_gid)
    
    # Count tasks
    result = await db.execute(
        select(func.count(Task.gid))
        .join(TaskProject, Task.gid == TaskProject.task_gid)
        .where(TaskProject.project_gid == project_gid)
    )
    total = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Task.gid))
        .join(TaskProject, Task.gid == TaskProject.task_gid)
        .where(TaskProject.project_gid == project_gid)
        .where(Task.completed == True)
    )
    completed = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Task.gid))
        .join(TaskProject, Task.gid == TaskProject.task_gid)
        .where(TaskProject.project_gid == project_gid)
        .where(Task.resource_subtype == "milestone")
    )
    milestones = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Task.gid))
        .join(TaskProject, Task.gid == TaskProject.task_gid)
        .where(TaskProject.project_gid == project_gid)
        .where(Task.resource_subtype == "milestone")
        .where(Task.completed == True)
    )
    completed_milestones = result.scalar() or 0
    
    return wrap_response({
        "num_tasks": total,
        "num_completed_tasks": completed,
        "num_incomplete_tasks": total - completed,
        "num_milestones": milestones,
        "num_completed_milestones": completed_milestones,
        "num_incomplete_milestones": milestones - completed_milestones,
    })


@router.post("/{project_gid}/addMembers")
async def add_project_members(
    project_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add members to a project.
    """
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_gid)
    
    members_str = data.get("data", {}).get("members", "")
    member_gids = [m.strip() for m in members_str.split(",") if m.strip()]
    
    for user_gid in member_gids:
        # Check if already a member
        result = await db.execute(
            select(ProjectMembership)
            .where(ProjectMembership.project_gid == project_gid)
            .where(ProjectMembership.user_gid == user_gid)
        )
        if not result.scalar_one_or_none():
            membership = ProjectMembership(
                gid=generate_gid(),
                user_gid=user_gid,
                project_gid=project_gid,
                access_level="editor",
                write_access="full_write",
            )
            db.add(membership)
    
    await db.commit()
    
    return wrap_response(project.to_response())


@router.post("/{project_gid}/removeMembers")
async def remove_project_members(
    project_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove members from a project.
    """
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_gid)
    
    members_str = data.get("data", {}).get("members", "")
    member_gids = [m.strip() for m in members_str.split(",") if m.strip()]
    
    for user_gid in member_gids:
        result = await db.execute(
            select(ProjectMembership)
            .where(ProjectMembership.project_gid == project_gid)
            .where(ProjectMembership.user_gid == user_gid)
        )
        membership = result.scalar_one_or_none()
        if membership:
            await db.delete(membership)
    
    await db.commit()
    
    return wrap_response(project.to_response())


@router.get("/{project_gid}/sections")
async def get_project_sections(
    project_gid: str,
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get sections in a project.
    """
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Project", project_gid)
    
    result = await db.execute(
        select(Section)
        .where(Section.project_gid == project_gid)
        .order_by(Section.order)
    )
    sections = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    section_responses = [parser.filter(s.to_response()) for s in sections]
    
    paginated = paginate(
        section_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/projects/{project_gid}/sections",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.get("/{project_gid}/tasks")
async def get_project_tasks(
    project_gid: str,
    completed_since: Optional[str] = Query(None),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get tasks in a project.
    """
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Project", project_gid)
    
    query = (
        select(Task)
        .join(TaskProject, Task.gid == TaskProject.task_gid)
        .where(TaskProject.project_gid == project_gid)
        .order_by(Task.created_at.desc())
    )
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    task_responses = [parser.filter(t.to_response()) for t in tasks]
    
    paginated = paginate(
        task_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/projects/{project_gid}/tasks",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.get("/{project_gid}/project_statuses")
async def get_project_statuses(
    project_gid: str,
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get status updates for a project.
    """
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Project", project_gid)
    
    result = await db.execute(
        select(ProjectStatus)
        .where(ProjectStatus.project_gid == project_gid)
        .order_by(ProjectStatus.created_at.desc())
    )
    statuses = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    status_responses = [parser.filter(s.to_response()) for s in statuses]
    
    paginated = paginate(
        status_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/projects/{project_gid}/project_statuses",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("/{project_gid}/project_statuses")
async def create_project_status(
    project_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a status update for a project.
    """
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_gid)
    
    status_data = ProjectStatusCreate(**data.get("data", {}))
    
    status = ProjectStatus(
        gid=generate_gid(),
        title=status_data.title,
        text=status_data.text,
        html_text=status_data.html_text,
        color=status_data.color,
        project_gid=project_gid,
    )
    db.add(status)
    
    # Update project's current status
    project.current_status_update_gid = status.gid
    
    await db.commit()
    
    return wrap_response(status.to_response())


# Project Memberships Router
@membership_router.get("/{project_membership_gid}")
async def get_project_membership(
    project_membership_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a project membership by GID.
    """
    result = await db.execute(
        select(ProjectMembership).where(ProjectMembership.gid == project_membership_gid)
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise NotFoundError("ProjectMembership", project_membership_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(membership.to_response()))


@membership_router.get("")
async def get_project_memberships(
    project: Optional[str] = Query(None, description="Project GID"),
    user: Optional[str] = Query(None, description="User GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get project memberships.
    """
    query = select(ProjectMembership)
    
    if project:
        query = query.where(ProjectMembership.project_gid == project)
    if user:
        query = query.where(ProjectMembership.user_gid == user)
    
    result = await db.execute(query)
    memberships = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    membership_responses = [parser.filter(m.to_response()) for m in memberships]
    
    paginated = paginate(
        membership_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/project_memberships",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


# Project Status Router
@status_router.get("/{project_status_gid}")
async def get_project_status(
    project_status_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a project status by GID.
    """
    result = await db.execute(
        select(ProjectStatus).where(ProjectStatus.gid == project_status_gid)
    )
    status = result.scalar_one_or_none()
    
    if not status:
        raise NotFoundError("ProjectStatus", project_status_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(status.to_response()))


@status_router.delete("/{project_status_gid}")
async def delete_project_status(
    project_status_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a project status.
    """
    result = await db.execute(
        select(ProjectStatus).where(ProjectStatus.gid == project_status_gid)
    )
    status = result.scalar_one_or_none()
    
    if not status:
        raise NotFoundError("ProjectStatus", project_status_gid)
    
    await db.delete(status)
    await db.commit()
    
    return wrap_response({})


# Project Brief Router
@brief_router.get("/{project_brief_gid}")
async def get_project_brief(
    project_brief_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a project brief by GID.
    """
    result = await db.execute(
        select(ProjectBrief).where(ProjectBrief.gid == project_brief_gid)
    )
    brief = result.scalar_one_or_none()
    
    if not brief:
        raise NotFoundError("ProjectBrief", project_brief_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(brief.to_response()))


@brief_router.put("/{project_brief_gid}")
async def update_project_brief(
    project_brief_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a project brief.
    """
    result = await db.execute(
        select(ProjectBrief).where(ProjectBrief.gid == project_brief_gid)
    )
    brief = result.scalar_one_or_none()
    
    if not brief:
        raise NotFoundError("ProjectBrief", project_brief_gid)
    
    update_data = ProjectBriefUpdate(**data.get("data", {}))
    
    if update_data.title is not None:
        brief.title = update_data.title
    if update_data.text is not None:
        brief.text = update_data.text
    if update_data.html_text is not None:
        brief.html_text = update_data.html_text
    
    await db.commit()
    await db.refresh(brief)
    
    return wrap_response(brief.to_response())


@brief_router.delete("/{project_brief_gid}")
async def delete_project_brief(
    project_brief_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a project brief.
    """
    result = await db.execute(
        select(ProjectBrief).where(ProjectBrief.gid == project_brief_gid)
    )
    brief = result.scalar_one_or_none()
    
    if not brief:
        raise NotFoundError("ProjectBrief", project_brief_gid)
    
    await db.delete(brief)
    await db.commit()
    
    return wrap_response({})

