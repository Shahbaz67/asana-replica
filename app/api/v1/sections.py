from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.models.project import Project
from app.models.section import Section
from app.models.task import Task, TaskProject
from app.schemas.section import SectionCreate, SectionUpdate, AddTaskRequest
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("")
async def get_sections(
    project: str = Query(..., description="Project GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get sections in a project.
    """
    result = await db.execute(select(Project).where(Project.gid == project))
    if not result.scalar_one_or_none():
        raise NotFoundError("Project", project)
    
    result = await db.execute(
        select(Section)
        .where(Section.project_gid == project)
        .order_by(Section.order)
    )
    sections = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    section_responses = [parser.filter(s.to_response()) for s in sections]
    
    paginated = paginate(
        section_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/sections",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_section(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new section in a project.
    """
    section_data = SectionCreate(**data.get("data", {}))
    
    # Verify project exists
    result = await db.execute(select(Project).where(Project.gid == section_data.project))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project", section_data.project)
    
    # Determine order
    result = await db.execute(
        select(func.max(Section.order))
        .where(Section.project_gid == section_data.project)
    )
    max_order = result.scalar() or 0
    order = max_order + 1
    
    if section_data.insert_before:
        result = await db.execute(
            select(Section).where(Section.gid == section_data.insert_before)
        )
        before_section = result.scalar_one_or_none()
        if before_section:
            order = before_section.order
            # Shift other sections down
            await db.execute(
                select(Section)
                .where(Section.project_gid == section_data.project)
                .where(Section.order >= order)
            )
    elif section_data.insert_after:
        result = await db.execute(
            select(Section).where(Section.gid == section_data.insert_after)
        )
        after_section = result.scalar_one_or_none()
        if after_section:
            order = after_section.order + 1
    
    section = Section(
        gid=generate_gid(),
        name=section_data.name,
        project_gid=section_data.project,
        order=order,
    )
    db.add(section)
    await db.commit()
    
    return wrap_response(section.to_response())


@router.get("/{section_gid}")
async def get_section(
    section_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a section by GID.
    """
    result = await db.execute(select(Section).where(Section.gid == section_gid))
    section = result.scalar_one_or_none()
    
    if not section:
        raise NotFoundError("Section", section_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(section.to_response()))


@router.put("/{section_gid}")
async def update_section(
    section_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a section.
    """
    result = await db.execute(select(Section).where(Section.gid == section_gid))
    section = result.scalar_one_or_none()
    
    if not section:
        raise NotFoundError("Section", section_gid)
    
    update_data = SectionUpdate(**data.get("data", {}))
    
    if update_data.name is not None:
        section.name = update_data.name
    
    await db.commit()
    await db.refresh(section)
    
    return wrap_response(section.to_response())


@router.delete("/{section_gid}")
async def delete_section(
    section_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a section.
    """
    result = await db.execute(select(Section).where(Section.gid == section_gid))
    section = result.scalar_one_or_none()
    
    if not section:
        raise NotFoundError("Section", section_gid)
    
    await db.delete(section)
    await db.commit()
    
    return wrap_response({})


@router.post("/{section_gid}/addTask")
async def add_task_to_section(
    section_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a task to a section.
    """
    result = await db.execute(select(Section).where(Section.gid == section_gid))
    section = result.scalar_one_or_none()
    
    if not section:
        raise NotFoundError("Section", section_gid)
    
    request_data = AddTaskRequest(**data.get("data", {}))
    task_gid = request_data.task
    
    # Verify task exists
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundError("Task", task_gid)
    
    # Update task's section
    task.section_gid = section_gid
    
    # Update or create task-project association
    result = await db.execute(
        select(TaskProject)
        .where(TaskProject.task_gid == task_gid)
        .where(TaskProject.project_gid == section.project_gid)
    )
    task_project = result.scalar_one_or_none()
    
    if task_project:
        task_project.section_gid = section_gid
    else:
        task_project = TaskProject(
            gid=generate_gid(),
            task_gid=task_gid,
            project_gid=section.project_gid,
            section_gid=section_gid,
        )
        db.add(task_project)
    
    await db.commit()
    
    return wrap_response(section.to_response())


@router.get("/{section_gid}/tasks")
async def get_section_tasks(
    section_gid: str,
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get tasks in a section.
    """
    result = await db.execute(select(Section).where(Section.gid == section_gid))
    section = result.scalar_one_or_none()
    
    if not section:
        raise NotFoundError("Section", section_gid)
    
    result = await db.execute(
        select(Task)
        .where(Task.section_gid == section_gid)
        .order_by(Task.order)
    )
    tasks = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    task_responses = [parser.filter(t.to_response()) for t in tasks]
    
    paginated = paginate(
        task_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/sections/{section_gid}/tasks",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("/{section_gid}/insert")
async def insert_section(
    section_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Move a section to a specific position.
    """
    result = await db.execute(select(Section).where(Section.gid == section_gid))
    section = result.scalar_one_or_none()
    
    if not section:
        raise NotFoundError("Section", section_gid)
    
    before_section_gid = data.get("data", {}).get("before_section")
    after_section_gid = data.get("data", {}).get("after_section")
    
    if before_section_gid:
        result = await db.execute(
            select(Section).where(Section.gid == before_section_gid)
        )
        before_section = result.scalar_one_or_none()
        if before_section:
            section.order = before_section.order - 1
    elif after_section_gid:
        result = await db.execute(
            select(Section).where(Section.gid == after_section_gid)
        )
        after_section = result.scalar_one_or_none()
        if after_section:
            section.order = after_section.order + 1
    
    await db.commit()
    await db.refresh(section)
    
    return wrap_response(section.to_response())

