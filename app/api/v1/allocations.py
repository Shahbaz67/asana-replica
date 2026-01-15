"""
Allocations API endpoints.

An allocation is a defined time period in which a user is assigned to work on a project.
Allocations allow tracking how user capacity is distributed across projects.
"""
from typing import Any, Optional
from datetime import date

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


# In-memory storage for allocations (would be a database model in production)
class AllocationModel:
    def __init__(self, gid: str, assignee_gid: str, project_gid: str, 
                 start_date: str, end_date: str, effort: float = None,
                 parent_gid: str = None):
        self.gid = gid
        self.resource_type = "allocation"
        self.assignee_gid = assignee_gid
        self.project_gid = project_gid
        self.start_date = start_date
        self.end_date = end_date
        self.effort = effort
        self.parent_gid = parent_gid
        self.created_at = None
        self.modified_at = None

    def to_response(self):
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "assignee": {"gid": self.assignee_gid, "resource_type": "user"},
            "project": {"gid": self.project_gid, "resource_type": "project"} if self.project_gid else None,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "effort": self.effort,
            "parent": {"gid": self.parent_gid} if self.parent_gid else None,
        }


# Temporary in-memory store
_allocations = {}


@router.get("")
async def get_allocations(
    workspace: str = Query(..., description="Workspace GID"),
    project: Optional[str] = Query(None, description="Filter by project GID"),
    assignee: Optional[str] = Query(None, description="Filter by assignee GID"),
    start_date: Optional[str] = Query(None, description="Filter by start date"),
    end_date: Optional[str] = Query(None, description="Filter by end date"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get multiple allocations.
    
    Returns all allocations in the given workspace, optionally filtered by
    project, assignee, or date range.
    """
    allocations = list(_allocations.values())
    
    if project:
        allocations = [a for a in allocations if a.project_gid == project]
    if assignee:
        allocations = [a for a in allocations if a.assignee_gid == assignee]
    
    parser = OptFieldsParser(params.opt_fields)
    allocation_responses = [parser.filter(a.to_response()) for a in allocations]
    
    paginated = paginate(
        allocation_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/allocations",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_allocation(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new allocation.
    
    Creates a new allocation assigning a user to a project for a specific
    time period with optional effort tracking.
    """
    allocation_data = data.get("data", {})
    
    assignee = allocation_data.get("assignee")
    if not assignee:
        raise ValidationError("assignee is required")
    
    start_date = allocation_data.get("start_date")
    end_date = allocation_data.get("end_date")
    
    if not start_date or not end_date:
        raise ValidationError("start_date and end_date are required")
    
    allocation = AllocationModel(
        gid=generate_gid(),
        assignee_gid=assignee,
        project_gid=allocation_data.get("project"),
        start_date=start_date,
        end_date=end_date,
        effort=allocation_data.get("effort"),
        parent_gid=allocation_data.get("parent"),
    )
    
    _allocations[allocation.gid] = allocation
    
    return wrap_response(allocation.to_response())


@router.get("/{allocation_gid}")
async def get_allocation(
    allocation_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a single allocation by GID.
    
    Returns the complete allocation record for the specified GID.
    """
    allocation = _allocations.get(allocation_gid)
    
    if not allocation:
        raise NotFoundError("Allocation", allocation_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(allocation.to_response()))


@router.put("/{allocation_gid}")
async def update_allocation(
    allocation_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update an allocation.
    
    Updates the specified allocation with new values for dates, effort, or assignment.
    """
    allocation = _allocations.get(allocation_gid)
    
    if not allocation:
        raise NotFoundError("Allocation", allocation_gid)
    
    update_data = data.get("data", {})
    
    if "start_date" in update_data:
        allocation.start_date = update_data["start_date"]
    if "end_date" in update_data:
        allocation.end_date = update_data["end_date"]
    if "effort" in update_data:
        allocation.effort = update_data["effort"]
    if "assignee" in update_data:
        allocation.assignee_gid = update_data["assignee"]
    if "project" in update_data:
        allocation.project_gid = update_data["project"]
    
    return wrap_response(allocation.to_response())


@router.delete("/{allocation_gid}")
async def delete_allocation(
    allocation_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete an allocation.
    
    Permanently removes the specified allocation from the system.
    """
    if allocation_gid not in _allocations:
        raise NotFoundError("Allocation", allocation_gid)
    
    del _allocations[allocation_gid]
    
    return wrap_response({})

