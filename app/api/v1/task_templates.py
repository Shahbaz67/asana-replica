from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError
from app.core.security import generate_gid
from app.models.project import Project
from app.models.task import Task, TaskTemplate, TaskProject
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("")
async def get_task_templates(
    project: str = Query(..., description="Project GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get task templates in a project.
    """
    result = await db.execute(select(Project).where(Project.gid == project))
    if not result.scalar_one_or_none():
        raise NotFoundError("Project", project)
    
    result = await db.execute(
        select(TaskTemplate)
        .where(TaskTemplate.project_gid == project)
        .order_by(TaskTemplate.name)
    )
    templates = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    template_responses = [parser.filter(t.to_response()) for t in templates]
    
    paginated = paginate(
        template_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/task_templates",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.get("/{task_template_gid}")
async def get_task_template(
    task_template_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a task template by GID.
    """
    result = await db.execute(
        select(TaskTemplate).where(TaskTemplate.gid == task_template_gid)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise NotFoundError("TaskTemplate", task_template_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(template.to_response()))


@router.post("/{task_template_gid}/instantiateTask")
async def instantiate_task_from_template(
    task_template_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new task from a template.
    """
    from app.models.job import Job
    
    result = await db.execute(
        select(TaskTemplate).where(TaskTemplate.gid == task_template_gid)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise NotFoundError("TaskTemplate", task_template_gid)
    
    task_data = data.get("data", {})
    
    # Create task from template
    task = Task(
        gid=generate_gid(),
        name=task_data.get("name", template.name),
        notes=template.description,
    )
    db.add(task)
    await db.flush()
    
    # Add to project if template has project
    if template.project_gid:
        task_project = TaskProject(
            gid=generate_gid(),
            task_gid=task.gid,
            project_gid=template.project_gid,
        )
        db.add(task_project)
    
    # Create job for tracking
    job = Job(
        gid=generate_gid(),
        resource_subtype="instantiate_task_template",
        status="succeeded",
        new_task_gid=task.gid,
    )
    db.add(job)
    await db.commit()
    
    return wrap_response(job.to_response())


@router.delete("/{task_template_gid}")
async def delete_task_template(
    task_template_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a task template.
    """
    result = await db.execute(
        select(TaskTemplate).where(TaskTemplate.gid == task_template_gid)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise NotFoundError("TaskTemplate", task_template_gid)
    
    await db.delete(template)
    await db.commit()
    
    return wrap_response({})


