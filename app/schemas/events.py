from typing import Optional, List
from pydantic import BaseModel


class EventResponse(BaseModel):
    """Event response schema."""
    resource: dict
    action: str
    created_at: str
    user: Optional[dict] = None
    parent: Optional[dict] = None
    change: Optional[dict] = None


class EventsResponse(BaseModel):
    """Events API response."""
    data: List[EventResponse]
    sync: str
    has_more: bool = False


