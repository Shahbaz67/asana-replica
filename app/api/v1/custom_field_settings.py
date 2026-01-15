"""
Custom Field Settings API endpoints.

Custom field settings control how a custom field behaves within a specific
project or portfolio context.
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.models.custom_field import CustomFieldSetting, CustomField
from app.models.project import Project
from app.models.portfolio import Portfolio
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("")
async def get_custom_field_settings_for_project(
    project: str = Query(..., description="Project GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get custom field settings for a project.
    
    Returns all custom field settings associated with the specified project,
    showing which custom fields are enabled and how they are configured.
    """
    # Verify project exists
    result = await db.execute(select(Project).where(Project.gid == project))
    if not result.scalar_one_or_none():
        raise NotFoundError("Project", project)
    
    result = await db.execute(
        select(CustomFieldSetting)
        .where(CustomFieldSetting.project_gid == project)
        .order_by(CustomFieldSetting.order)
    )
    settings = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    setting_responses = [parser.filter(s.to_response()) for s in settings]
    
    paginated = paginate(
        setting_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/custom_field_settings",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def add_custom_field_to_project(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a custom field setting to a project.
    
    Associates a custom field with a project and configures how it should
    be displayed and used within that project context.
    """
    setting_data = data.get("data", {})
    
    project_gid = setting_data.get("project")
    custom_field_gid = setting_data.get("custom_field")
    
    if not project_gid:
        raise ValidationError("project is required")
    if not custom_field_gid:
        raise ValidationError("custom_field is required")
    
    # Verify project exists
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Project", project_gid)
    
    # Verify custom field exists
    result = await db.execute(select(CustomField).where(CustomField.gid == custom_field_gid))
    custom_field = result.scalar_one_or_none()
    if not custom_field:
        raise NotFoundError("CustomField", custom_field_gid)
    
    # Check if already exists
    result = await db.execute(
        select(CustomFieldSetting)
        .where(CustomFieldSetting.project_gid == project_gid)
        .where(CustomFieldSetting.custom_field_gid == custom_field_gid)
    )
    if result.scalar_one_or_none():
        raise ValidationError("Custom field is already added to this project")
    
    # Get max order
    result = await db.execute(
        select(CustomFieldSetting)
        .where(CustomFieldSetting.project_gid == project_gid)
        .order_by(CustomFieldSetting.order.desc())
        .limit(1)
    )
    last_setting = result.scalar_one_or_none()
    order = (last_setting.order + 1) if last_setting else 0
    
    setting = CustomFieldSetting(
        gid=generate_gid(),
        project_gid=project_gid,
        custom_field_gid=custom_field_gid,
        is_important=setting_data.get("is_important", False),
        order=order,
    )
    db.add(setting)
    await db.commit()
    
    return wrap_response(setting.to_response())


@router.get("/{custom_field_setting_gid}")
async def get_custom_field_setting(
    custom_field_setting_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a custom field setting by GID.
    
    Returns the complete custom field setting including the associated
    custom field and project configuration.
    """
    result = await db.execute(
        select(CustomFieldSetting).where(CustomFieldSetting.gid == custom_field_setting_gid)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise NotFoundError("CustomFieldSetting", custom_field_setting_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(setting.to_response()))


@router.delete("/{custom_field_setting_gid}")
async def remove_custom_field_from_project(
    custom_field_setting_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove a custom field setting from a project.
    
    Removes the association between a custom field and a project.
    This does not delete the custom field itself.
    """
    result = await db.execute(
        select(CustomFieldSetting).where(CustomFieldSetting.gid == custom_field_setting_gid)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise NotFoundError("CustomFieldSetting", custom_field_setting_gid)
    
    await db.delete(setting)
    await db.commit()
    
    return wrap_response({})

