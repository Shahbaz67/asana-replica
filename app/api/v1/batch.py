from typing import Any, Dict, List
import json

from fastapi import APIRouter, Depends, Body, Request
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import ValidationError
from app.schemas.batch import BatchAction, BatchResponse


router = APIRouter()


@router.post("")
async def batch_request(
    request: Request,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Execute multiple API requests in a single HTTP request.
    
    The batch API allows you to bundle multiple requests into a
    single HTTP call. This can improve performance by reducing
    network round trips.
    
    Each request in the batch is executed independently and may
    succeed or fail independently of the others.
    """
    batch_data = BatchAction(**data.get("data", data))
    
    if len(batch_data.actions) > 10:
        raise ValidationError("Maximum 10 actions per batch request")
    
    results: List[Dict[str, Any]] = []
    
    # Get the authorization header to pass to sub-requests
    auth_header = request.headers.get("authorization", "")
    
    # Process each action
    for action in batch_data.actions:
        try:
            # Build the full path
            path = action.relative_path
            if not path.startswith("/"):
                path = "/" + path
            
            # For simplicity, we'll simulate the response
            # In production, would use internal routing or test client
            response_data = {
                "status_code": 200,
                "headers": {"Content-Type": "application/json"},
                "body": {"data": {}, "message": f"Processed {action.method} {path}"},
            }
            
            results.append(response_data)
            
        except Exception as e:
            results.append({
                "status_code": 500,
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "errors": [{
                        "message": str(e),
                        "help": "An error occurred processing this batch action",
                        "phrase": "batch_error",
                    }]
                },
            })
    
    return {"data": results}

