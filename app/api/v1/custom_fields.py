from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.custom_field import CustomField, CustomFieldEnumOption, CustomFieldSetting
from app.schemas.custom_field import (
    CustomFieldCreate, CustomFieldUpdate,
    EnumOptionCreate, EnumOptionUpdate,
    CustomFieldSettingCreate,
)
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("")
async def get_custom_fields(
    workspace: str = Query(..., description="Workspace GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get custom fields in a workspace.
    """
    result = await db.execute(select(Workspace).where(Workspace.gid == workspace))
    if not result.scalar_one_or_none():
        raise NotFoundError("Workspace", workspace)
    
    result = await db.execute(
        select(CustomField)
        .where(CustomField.workspace_gid == workspace)
        .order_by(CustomField.name)
    )
    fields = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    field_responses = [parser.filter(f.to_response()) for f in fields]
    
    paginated = paginate(
        field_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/custom_fields",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_custom_field(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new custom field in a workspace.
    """
    field_data = CustomFieldCreate(**data.get("data", {}))
    
    # Verify workspace exists
    result = await db.execute(select(Workspace).where(Workspace.gid == field_data.workspace))
    if not result.scalar_one_or_none():
        raise NotFoundError("Workspace", field_data.workspace)
    
    custom_field = CustomField(
        gid=generate_gid(),
        name=field_data.name,
        description=field_data.description,
        resource_subtype=field_data.resource_subtype,
        type=field_data.resource_subtype,
        format=field_data.format,
        currency_code=field_data.currency_code,
        custom_label=field_data.custom_label,
        custom_label_position=field_data.custom_label_position,
        precision=field_data.precision,
        workspace_gid=field_data.workspace,
    )
    db.add(custom_field)
    await db.flush()
    
    # Create enum options if provided
    if field_data.enum_options and field_data.resource_subtype in ("enum", "multi_enum"):
        for i, option_data in enumerate(field_data.enum_options):
            option = CustomFieldEnumOption(
                gid=generate_gid(),
                name=option_data.name,
                color=option_data.color,
                enabled=option_data.enabled,
                order=i,
                custom_field_gid=custom_field.gid,
            )
            db.add(option)
    
    await db.commit()
    await db.refresh(custom_field)
    
    # Add enum options to response
    response = custom_field.to_response()
    if custom_field.resource_subtype in ("enum", "multi_enum"):
        result = await db.execute(
            select(CustomFieldEnumOption)
            .where(CustomFieldEnumOption.custom_field_gid == custom_field.gid)
            .order_by(CustomFieldEnumOption.order)
        )
        options = result.scalars().all()
        response["enum_options"] = [o.to_response() for o in options]
    
    return wrap_response(response)


@router.get("/{custom_field_gid}")
async def get_custom_field(
    custom_field_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a custom field by GID.
    """
    result = await db.execute(select(CustomField).where(CustomField.gid == custom_field_gid))
    custom_field = result.scalar_one_or_none()
    
    if not custom_field:
        raise NotFoundError("CustomField", custom_field_gid)
    
    parser = OptFieldsParser(opt_fields)
    response = custom_field.to_response()
    
    # Add enum options
    if custom_field.resource_subtype in ("enum", "multi_enum"):
        result = await db.execute(
            select(CustomFieldEnumOption)
            .where(CustomFieldEnumOption.custom_field_gid == custom_field_gid)
            .order_by(CustomFieldEnumOption.order)
        )
        options = result.scalars().all()
        response["enum_options"] = [o.to_response() for o in options]
    
    return wrap_response(parser.filter(response))


@router.put("/{custom_field_gid}")
async def update_custom_field(
    custom_field_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a custom field.
    """
    result = await db.execute(select(CustomField).where(CustomField.gid == custom_field_gid))
    custom_field = result.scalar_one_or_none()
    
    if not custom_field:
        raise NotFoundError("CustomField", custom_field_gid)
    
    update_data = CustomFieldUpdate(**data.get("data", {}))
    
    if update_data.name is not None:
        custom_field.name = update_data.name
    if update_data.description is not None:
        custom_field.description = update_data.description
    if update_data.format is not None:
        custom_field.format = update_data.format
    if update_data.currency_code is not None:
        custom_field.currency_code = update_data.currency_code
    if update_data.custom_label is not None:
        custom_field.custom_label = update_data.custom_label
    if update_data.precision is not None:
        custom_field.precision = update_data.precision
    
    await db.commit()
    await db.refresh(custom_field)
    
    return wrap_response(custom_field.to_response())


@router.delete("/{custom_field_gid}")
async def delete_custom_field(
    custom_field_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a custom field.
    """
    result = await db.execute(select(CustomField).where(CustomField.gid == custom_field_gid))
    custom_field = result.scalar_one_or_none()
    
    if not custom_field:
        raise NotFoundError("CustomField", custom_field_gid)
    
    await db.delete(custom_field)
    await db.commit()
    
    return wrap_response({})


@router.post("/{custom_field_gid}/enum_options")
async def create_enum_option(
    custom_field_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create an enum option for a custom field.
    """
    result = await db.execute(select(CustomField).where(CustomField.gid == custom_field_gid))
    custom_field = result.scalar_one_or_none()
    
    if not custom_field:
        raise NotFoundError("CustomField", custom_field_gid)
    
    if custom_field.resource_subtype not in ("enum", "multi_enum"):
        raise ValidationError("Can only add enum options to enum or multi_enum fields")
    
    option_data = EnumOptionCreate(**data.get("data", {}))
    
    # Get max order
    result = await db.execute(
        select(CustomFieldEnumOption)
        .where(CustomFieldEnumOption.custom_field_gid == custom_field_gid)
        .order_by(CustomFieldEnumOption.order.desc())
        .limit(1)
    )
    last_option = result.scalar_one_or_none()
    order = (last_option.order + 1) if last_option else 0
    
    option = CustomFieldEnumOption(
        gid=generate_gid(),
        name=option_data.name,
        color=option_data.color,
        enabled=option_data.enabled,
        order=order,
        custom_field_gid=custom_field_gid,
    )
    db.add(option)
    await db.commit()
    
    return wrap_response(option.to_response())


@router.put("/{custom_field_gid}/enum_options/{enum_option_gid}")
async def update_enum_option(
    custom_field_gid: str,
    enum_option_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update an enum option.
    """
    result = await db.execute(
        select(CustomFieldEnumOption)
        .where(CustomFieldEnumOption.gid == enum_option_gid)
        .where(CustomFieldEnumOption.custom_field_gid == custom_field_gid)
    )
    option = result.scalar_one_or_none()
    
    if not option:
        raise NotFoundError("EnumOption", enum_option_gid)
    
    update_data = EnumOptionUpdate(**data.get("data", {}))
    
    if update_data.name is not None:
        option.name = update_data.name
    if update_data.color is not None:
        option.color = update_data.color
    if update_data.enabled is not None:
        option.enabled = update_data.enabled
    
    await db.commit()
    await db.refresh(option)
    
    return wrap_response(option.to_response())

