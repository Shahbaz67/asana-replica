from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError
from app.core.security import generate_gid
from app.models.workspace import Workspace
from app.models.organization_export import OrganizationExport
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("")
async def get_organization_exports(
    organization: str = Query(..., description="Organization/Workspace GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get organization exports.
    
    Organization exports allow you to export all data from your
    organization for backup or compliance purposes.
    """
    result = await db.execute(
        select(OrganizationExport)
        .where(OrganizationExport.organization_gid == organization)
        .order_by(OrganizationExport.created_at.desc())
    )
    exports = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    export_responses = [parser.filter(e.to_response()) for e in exports]
    
    paginated = paginate(
        export_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/organization_exports",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_organization_export(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new organization export request.
    
    This starts an asynchronous export process. The export will be
    available for download once the state changes to 'finished'.
    """
    export_data = data.get("data", {})
    organization_gid = export_data.get("organization")
    
    if not organization_gid:
        from app.core.exceptions import ValidationError
        raise ValidationError("organization is required")
    
    # Verify organization exists
    result = await db.execute(select(Workspace).where(Workspace.gid == organization_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Organization", organization_gid)
    
    export = OrganizationExport(
        gid=generate_gid(),
        organization_gid=organization_gid,
        state="pending",
    )
    db.add(export)
    
    # In production, would queue a background job here
    # For now, we'll simulate completion
    export.state = "finished"
    export.download_url = f"/exports/{export.gid}.zip"
    
    await db.commit()
    
    return wrap_response(export.to_response())


@router.get("/{organization_export_gid}")
async def get_organization_export(
    organization_export_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get an organization export by GID.
    """
    result = await db.execute(
        select(OrganizationExport).where(OrganizationExport.gid == organization_export_gid)
    )
    export = result.scalar_one_or_none()
    
    if not export:
        raise NotFoundError("OrganizationExport", organization_export_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(export.to_response()))

