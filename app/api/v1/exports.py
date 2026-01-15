"""
Exports API endpoints.

Exports allow users to export project data in various formats for
backup, reporting, or data analysis purposes.
"""
from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.models.project import Project
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


class ExportModel:
    def __init__(self, gid: str, project_gid: str, export_type: str = "json"):
        self.gid = gid
        self.resource_type = "export"
        self.project_gid = project_gid
        self.export_type = export_type
        self.state = "pending"
        self.download_url = None
        self.created_at = datetime.utcnow()

    def to_response(self):
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "project": {"gid": self.project_gid, "resource_type": "project"},
            "export_type": self.export_type,
            "state": self.state,
            "download_url": self.download_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


_exports = {}


@router.post("")
async def create_export(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new export.
    
    Initiates an export of project data. The export will be processed
    asynchronously and a download URL will be provided when complete.
    """
    export_data = data.get("data", {})
    
    project_gid = export_data.get("project")
    if not project_gid:
        raise ValidationError("project is required")
    
    # Verify project exists
    result = await db.execute(select(Project).where(Project.gid == project_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Project", project_gid)
    
    export = ExportModel(
        gid=generate_gid(),
        project_gid=project_gid,
        export_type=export_data.get("export_type", "json"),
    )
    
    # Simulate export completion
    export.state = "finished"
    export.download_url = f"/exports/{export.gid}.{export.export_type}"
    
    _exports[export.gid] = export
    
    return wrap_response(export.to_response())


@router.get("/{export_gid}")
async def get_export(
    export_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get an export by GID.
    
    Returns the export status and download URL if the export is complete.
    """
    export = _exports.get(export_gid)
    
    if not export:
        raise NotFoundError("Export", export_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(export.to_response()))

