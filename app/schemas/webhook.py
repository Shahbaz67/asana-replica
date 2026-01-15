from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WebhookFilter(BaseModel):
    """Webhook filter configuration."""
    resource_type: str
    resource_subtype: Optional[str] = None
    action: Optional[str] = None
    fields: Optional[List[str]] = None


class WebhookCreate(BaseModel):
    """Schema for creating a webhook."""
    resource: str = Field(..., description="Resource GID to watch")
    target: str = Field(..., description="Target URL for webhook delivery")
    filters: Optional[List[WebhookFilter]] = None


class WebhookResponse(BaseModel):
    """Webhook response schema."""
    gid: str
    resource_type: str = "webhook"
    resource: dict
    target: str
    active: bool = True
    created_at: Optional[str] = None
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    last_failure_content: Optional[str] = None
    filters: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True


class WebhookCompact(BaseModel):
    """Compact webhook representation."""
    gid: str
    resource_type: str = "webhook"
    resource: dict
    target: str
    active: bool = True
    
    class Config:
        from_attributes = True


class WebhookEvent(BaseModel):
    """Webhook event payload."""
    resource: dict
    user: Optional[dict] = None
    action: str
    change: Optional[dict] = None
    created_at: str


class WebhookDelivery(BaseModel):
    """Webhook delivery payload."""
    events: List[WebhookEvent]

