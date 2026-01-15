from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError
from app.core.security import generate_gid
from app.models.team import Team
from app.models.project import ProjectTemplate
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("")
async def get_project_templates(
    team: Optional[str] = Query(None, description="Team GID"),
    workspace: Optional[str] = Query(None, description="Workspace GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get project templates.
    """
    query = select(ProjectTemplate)
    
    if team:
        query = query.where(ProjectTemplate.team_gid == team)
    
    if workspace:
        query = (
            query.join(Team, ProjectTemplate.team_gid == Team.gid)
            .where(Team.workspace_gid == workspace)
        )
    
    result = await db.execute(query.order_by(ProjectTemplate.name))
    templates = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    template_responses = [parser.filter(t.to_response()) for t in templates]
    
    paginated = paginate(
        template_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/project_templates",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.get("/{project_template_gid}")
async def get_project_template(
    project_template_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a project template by GID.
    """
    result = await db.execute(
        select(ProjectTemplate).where(ProjectTemplate.gid == project_template_gid)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise NotFoundError("ProjectTemplate", project_template_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(template.to_response()))


@router.post("/{project_template_gid}/instantiateProject")
async def instantiate_project_from_template(
    project_template_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new project from a template.
    """
    from app.models.project import Project
    from app.models.job import Job
    
    result = await db.execute(
        select(ProjectTemplate).where(ProjectTemplate.gid == project_template_gid)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise NotFoundError("ProjectTemplate", project_template_gid)
    
    project_data = data.get("data", {})
    
    # Get team's workspace
    result = await db.execute(select(Team).where(Team.gid == template.team_gid))
    team = result.scalar_one_or_none()
    
    # Create project from template
    project = Project(
        gid=generate_gid(),
        name=project_data.get("name", template.name),
        notes=template.description,
        html_notes=template.html_description,
        workspace_gid=team.workspace_gid if team else None,
        team_gid=template.team_gid,
        public=project_data.get("public", template.public),
        color=template.color,
    )
    db.add(project)
    await db.flush()
    
    # Create job for tracking
    job = Job(
        gid=generate_gid(),
        resource_subtype="instantiate_project_template",
        status="succeeded",
        new_project_gid=project.gid,
    )
    db.add(job)
    await db.commit()
    
    return wrap_response(job.to_response())


@router.delete("/{project_template_gid}")
async def delete_project_template(
    project_template_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a project template.
    """
    result = await db.execute(
        select(ProjectTemplate).where(ProjectTemplate.gid == project_template_gid)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise NotFoundError("ProjectTemplate", project_template_gid)
    
    await db.delete(template)
    await db.commit()
    
    return wrap_response({})


@router.get("/{project_template_gid}/team")
async def get_project_template_team(
    project_template_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get the team for a project template.
    
    Returns the team that owns the project template.
    """
    result = await db.execute(
        select(ProjectTemplate).where(ProjectTemplate.gid == project_template_gid)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise NotFoundError("ProjectTemplate", project_template_gid)
    
    if not template.team_gid:
        raise NotFoundError("Team", "None")
    
    result = await db.execute(select(Team).where(Team.gid == template.team_gid))
    team = result.scalar_one_or_none()
    
    if not team:
        raise NotFoundError("Team", template.team_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(team.to_response()))


