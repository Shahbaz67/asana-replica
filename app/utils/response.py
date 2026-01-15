from typing import Optional, Any, Dict, List, Union
from pydantic import BaseModel


class AsanaResponse(BaseModel):
    """Standard Asana API response wrapper."""
    data: Any


class AsanaListResponse(BaseModel):
    """Asana API response wrapper for lists with pagination."""
    data: List[Any]
    next_page: Optional[Dict[str, str]] = None


class AsanaErrorDetail(BaseModel):
    """Detail of an error in Asana format."""
    message: str
    help: Optional[str] = None
    phrase: Optional[str] = None


class AsanaErrorResponse(BaseModel):
    """Asana API error response."""
    errors: List[AsanaErrorDetail]


def wrap_response(data: Any) -> Dict[str, Any]:
    """Wrap data in Asana response format."""
    return {"data": data}


def wrap_list_response(
    data: List[Any],
    next_page: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Wrap list data in Asana response format with pagination."""
    response = {"data": data}
    if next_page:
        response["next_page"] = next_page
    return response


def error_response(
    message: str,
    help_text: Optional[str] = None,
    phrase: Optional[str] = None,
) -> Dict[str, Any]:
    """Create an error response in Asana format."""
    return {
        "errors": [
            {
                "message": message,
                "help": help_text or "Please check your request and try again.",
                "phrase": phrase or "error",
            }
        ]
    }


