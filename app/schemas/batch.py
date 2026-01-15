from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BatchRequest(BaseModel):
    """Single request in a batch."""
    relative_path: str = Field(..., description="API path relative to /api/1.0")
    method: str = Field(default="GET", pattern="^(GET|POST|PUT|DELETE|PATCH)$")
    data: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None


class BatchAction(BaseModel):
    """Batch API action."""
    actions: List[BatchRequest] = Field(..., min_length=1, max_length=10)


class BatchResponse(BaseModel):
    """Single response in a batch."""
    status_code: int
    headers: Dict[str, str]
    body: Any


class BatchResult(BaseModel):
    """Batch API result."""
    data: List[BatchResponse]

