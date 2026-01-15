from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.models.audit_log import AuditLogEvent
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser


router = APIRouter()


@router.get("")
async def get_audit_log_events(
    workspace: str = Query(..., description="Workspace/Organization GID"),
    start_at: Optional[str] = Query(None, description="Start datetime (ISO 8601)"),
    end_at: Optional[str] = Query(None, description="End datetime (ISO 8601)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    actor_type: Optional[str] = Query(None, description="Filter by actor type"),
    actor_gid: Optional[str] = Query(None, description="Filter by actor GID"),
    resource_gid: Optional[str] = Query(None, description="Filter by resource GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get audit log events for an organization.
    
    This is an enterprise feature. Audit logs capture events that
    occur within your organization, such as logins, task changes,
    and permission changes.
    """
    query = select(AuditLogEvent).where(AuditLogEvent.context_gid == workspace)
    
    if start_at:
        try:
            start_dt = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
            query = query.where(AuditLogEvent.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_at:
        try:
            end_dt = datetime.fromisoformat(end_at.replace("Z", "+00:00"))
            query = query.where(AuditLogEvent.created_at <= end_dt)
        except ValueError:
            pass
    
    if event_type:
        query = query.where(AuditLogEvent.event_type == event_type)
    
    if actor_type:
        query = query.where(AuditLogEvent.actor_type == actor_type)
    
    if actor_gid:
        query = query.where(AuditLogEvent.actor_gid == actor_gid)
    
    if resource_gid:
        query = query.where(AuditLogEvent.resource_gid == resource_gid)
    
    query = query.order_by(AuditLogEvent.created_at.desc())
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    event_responses = [parser.filter(e.to_response()) for e in events]
    
    paginated = paginate(
        event_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/audit_log_events",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }

