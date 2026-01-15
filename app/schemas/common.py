from typing import Optional, List, Any, Dict, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime


T = TypeVar("T")


class ResourceRef(BaseModel):
    """Reference to a resource."""
    gid: str
    resource_type: str


class AsanaResponse(BaseModel, Generic[T]):
    """Standard Asana API response wrapper."""
    data: T


class NextPage(BaseModel):
    """Pagination info."""
    offset: str
    path: str
    uri: str


class AsanaListResponse(BaseModel, Generic[T]):
    """Asana API response with list data and pagination."""
    data: List[T]
    next_page: Optional[NextPage] = None


class AsanaErrorDetail(BaseModel):
    """Error detail in Asana format."""
    message: str
    help: Optional[str] = None
    phrase: Optional[str] = None


class AsanaErrorResponse(BaseModel):
    """Error response in Asana format."""
    errors: List[AsanaErrorDetail]


class RequestData(BaseModel, Generic[T]):
    """Request wrapper with data field."""
    data: T


