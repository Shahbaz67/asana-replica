"""
Custom Types API endpoints.

Custom types define the schema for custom objects that can be created
and managed within Asana workspaces.
"""
from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


class CustomTypeModel:
    def __init__(self, gid: str, name: str, workspace_gid: str,
                 description: str = None, enabled: bool = True):
        self.gid = gid
        self.resource_type = "custom_type"
        self.name = name
        self.description = description
        self.workspace_gid = workspace_gid
        self.enabled = enabled
        self.created_at = datetime.utcnow()

    def to_response(self):
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "description": self.description,
            "workspace": {"gid": self.workspace_gid, "resource_type": "workspace"},
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


_custom_types = {}


@router.get("")
async def get_custom_types(
    workspace: str = Query(..., description="Workspace GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get custom types in a workspace.
    
    Returns all custom types defined in the specified workspace.
    Custom types define the structure of custom objects.
    """
    custom_types = [ct for ct in _custom_types.values() if ct.workspace_gid == workspace]
    
    parser = OptFieldsParser(params.opt_fields)
    type_responses = [parser.filter(ct.to_response()) for ct in custom_types]
    
    paginated = paginate(
        type_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/custom_types",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.get("/{custom_type_gid}")
async def get_custom_type(
    custom_type_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a custom type by GID.
    
    Returns the complete custom type definition including all properties
    and configuration.
    """
    custom_type = _custom_types.get(custom_type_gid)
    
    if not custom_type:
        raise NotFoundError("CustomType", custom_type_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(custom_type.to_response()))

