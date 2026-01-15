"""
Access Requests API endpoints.

Access requests represent requests for access to resources that require approval.
Users can request access to private projects, teams, or other restricted resources.
"""
from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError, ForbiddenError
from app.core.security import generate_gid
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


class AccessRequestModel:
    def __init__(self, gid: str, resource_gid: str, resource_type: str,
                 requester_gid: str, status: str = "pending", message: str = None):
        self.gid = gid
        self.resource_type_name = "access_request"
        self.resource_gid = resource_gid
        self.target_resource_type = resource_type
        self.requester_gid = requester_gid
        self.status = status
        self.message = message
        self.created_at = datetime.utcnow()
        self.resolved_at = None
        self.resolved_by_gid = None

    def to_response(self):
        return {
            "gid": self.gid,
            "resource_type": self.resource_type_name,
            "resource": {
                "gid": self.resource_gid,
                "resource_type": self.target_resource_type
            },
            "requester": {
                "gid": self.requester_gid,
                "resource_type": "user"
            },
            "status": self.status,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": {"gid": self.resolved_by_gid, "resource_type": "user"} if self.resolved_by_gid else None,
        }


_access_requests = {}


@router.get("")
async def get_access_requests(
    resource: str = Query(..., description="Resource GID to get access requests for"),
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, denied)"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get access requests for a resource.
    
    Returns all access requests for the specified resource, optionally
    filtered by status.
    """
    requests = [r for r in _access_requests.values() if r.resource_gid == resource]
    
    if status:
        requests = [r for r in requests if r.status == status]
    
    parser = OptFieldsParser(params.opt_fields)
    request_responses = [parser.filter(r.to_response()) for r in requests]
    
    paginated = paginate(
        request_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/access_requests",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_access_request(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new access request.
    
    Creates a request for access to a restricted resource. The request
    will be sent to the resource administrators for approval.
    """
    request_data = data.get("data", {})
    
    resource = request_data.get("resource")
    if not resource:
        raise ValidationError("resource is required")
    
    resource_type = request_data.get("resource_type", "project")
    
    access_request = AccessRequestModel(
        gid=generate_gid(),
        resource_gid=resource,
        resource_type=resource_type,
        requester_gid=request_data.get("requester", generate_gid()),
        message=request_data.get("message"),
    )
    
    _access_requests[access_request.gid] = access_request
    
    return wrap_response(access_request.to_response())


@router.get("/{access_request_gid}")
async def get_access_request(
    access_request_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a single access request by GID.
    
    Returns the complete access request record including status and resolution details.
    """
    access_request = _access_requests.get(access_request_gid)
    
    if not access_request:
        raise NotFoundError("AccessRequest", access_request_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(access_request.to_response()))


@router.put("/{access_request_gid}")
async def respond_to_access_request(
    access_request_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Respond to an access request.
    
    Approve or deny an access request. Only resource administrators can
    respond to access requests.
    """
    access_request = _access_requests.get(access_request_gid)
    
    if not access_request:
        raise NotFoundError("AccessRequest", access_request_gid)
    
    if access_request.status != "pending":
        raise ForbiddenError("This access request has already been resolved")
    
    response_data = data.get("data", {})
    status = response_data.get("status")
    
    if status not in ("approved", "denied"):
        raise ValidationError("status must be 'approved' or 'denied'")
    
    access_request.status = status
    access_request.resolved_at = datetime.utcnow()
    access_request.resolved_by_gid = response_data.get("resolved_by")
    
    return wrap_response(access_request.to_response())

