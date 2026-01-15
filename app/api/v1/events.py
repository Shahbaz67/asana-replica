from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.events import event_store
from app.models.event import EventRecord
from app.utils.filters import OptFieldsParser


router = APIRouter()


@router.get("")
async def get_events(
    resource: str = Query(..., description="Resource GID to get events for"),
    sync: Optional[str] = Query(None, description="Sync token from previous request"),
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get events for a resource.
    
    The Events API allows you to subscribe to events on a resource.
    This endpoint returns all events that have occurred since the last
    sync token was generated.
    
    If no sync token is provided, returns an empty list and the current
    sync token.
    """
    if sync:
        # Get events since sync token
        events, new_sync, has_more = await event_store.get_events(resource, sync)
        
        parser = OptFieldsParser(opt_fields)
        event_responses = [
            parser.filter({
                "resource": {"gid": e.resource_gid, "resource_type": e.resource_type},
                "action": e.action,
                "created_at": e.created_at.isoformat(),
                "user": {"gid": e.user_gid, "resource_type": "user"} if e.user_gid else None,
                "parent": e.parent,
                "change": e.change,
            })
            for e in events
        ]
        
        return {
            "data": event_responses,
            "sync": new_sync,
            "has_more": has_more,
        }
    else:
        # Get initial sync token
        sync_token = await event_store.get_sync_token(resource)
        if not sync_token:
            sync_token = f"sync:{resource}"
        
        return {
            "data": [],
            "sync": sync_token,
            "has_more": False,
        }


@router.get("/poll")
async def poll_events(
    resource: str = Query(..., description="Resource GID to poll events for"),
    sync: str = Query(..., description="Sync token from previous request"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Poll for new events since the given sync token.
    
    This is a convenience endpoint that always returns events
    even if there are none (with has_more=False).
    """
    events, new_sync, has_more = await event_store.get_events(resource, sync)
    
    event_responses = [
        {
            "resource": {"gid": e.resource_gid, "resource_type": e.resource_type},
            "action": e.action,
            "created_at": e.created_at.isoformat(),
            "user": {"gid": e.user_gid, "resource_type": "user"} if e.user_gid else None,
            "parent": e.parent,
            "change": e.change,
        }
        for e in events
    ]
    
    return {
        "data": event_responses,
        "sync": new_sync,
        "has_more": has_more,
    }


