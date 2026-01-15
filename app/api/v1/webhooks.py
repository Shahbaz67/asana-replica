from typing import Any, Optional
import json

from fastapi import APIRouter, Depends, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError
from app.core.security import generate_gid, generate_webhook_secret
from app.models.webhook import Webhook
from app.schemas.webhook import WebhookCreate
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("")
async def get_webhooks(
    workspace: str = Query(..., description="Workspace GID"),
    resource: Optional[str] = Query(None, description="Resource GID to filter by"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get webhooks in a workspace.
    """
    # For simplicity, we'll get webhooks created by the user
    query = select(Webhook)
    
    if resource:
        query = query.where(Webhook.resource_gid == resource)
    
    result = await db.execute(query)
    webhooks = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    webhook_responses = [parser.filter(w.to_response()) for w in webhooks]
    
    paginated = paginate(
        webhook_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/webhooks",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_webhook(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new webhook.
    
    The webhook will be created and immediately attempt to establish
    a handshake with the target URL.
    """
    webhook_data = WebhookCreate(**data.get("data", {}))
    
    # Determine resource type from resource GID (simplified)
    # In production, would look up the actual resource
    resource_type = "project"  # Default assumption
    
    webhook = Webhook(
        gid=generate_gid(),
        target=webhook_data.target,
        resource_gid=webhook_data.resource,
        resource_type=resource_type,
        active=True,
        secret=generate_webhook_secret(),
        filters=json.dumps([f.model_dump() for f in webhook_data.filters]) if webhook_data.filters else None,
    )
    db.add(webhook)
    await db.commit()
    
    # In production, would attempt handshake here
    # and set webhook.active based on success
    
    response = webhook.to_response()
    # Include secret only in creation response
    response["secret"] = webhook.secret
    
    return wrap_response(response)


@router.get("/{webhook_gid}")
async def get_webhook(
    webhook_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a webhook by GID.
    """
    result = await db.execute(select(Webhook).where(Webhook.gid == webhook_gid))
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise NotFoundError("Webhook", webhook_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(webhook.to_response()))


@router.put("/{webhook_gid}")
async def update_webhook(
    webhook_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a webhook.
    """
    result = await db.execute(select(Webhook).where(Webhook.gid == webhook_gid))
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise NotFoundError("Webhook", webhook_gid)
    
    update_data = data.get("data", {})
    
    if "filters" in update_data:
        webhook.filters = json.dumps(update_data["filters"]) if update_data["filters"] else None
    
    await db.commit()
    await db.refresh(webhook)
    
    return wrap_response(webhook.to_response())


@router.delete("/{webhook_gid}")
async def delete_webhook(
    webhook_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a webhook.
    """
    result = await db.execute(select(Webhook).where(Webhook.gid == webhook_gid))
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise NotFoundError("Webhook", webhook_gid)
    
    await db.delete(webhook)
    await db.commit()
    
    return wrap_response({})


