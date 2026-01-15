from typing import Optional, List, Any, TypeVar, Generic
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T")


class NextPage(BaseModel):
    """Pagination info for next page."""
    offset: str
    path: str
    uri: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    data: List[Any]
    next_page: Optional[NextPage] = None


def paginate(
    items: List[Any],
    offset: Optional[str] = None,
    limit: int = settings.DEFAULT_PAGE_SIZE,
    base_path: str = "",
) -> PaginatedResponse:
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        offset: Offset token for pagination
        limit: Maximum items per page
        base_path: Base path for generating next page URI
    
    Returns:
        PaginatedResponse with data and next_page info
    """
    # Ensure limit is within bounds
    limit = min(limit, settings.MAX_PAGE_SIZE)
    
    # Parse offset as integer index
    start_idx = 0
    if offset:
        try:
            start_idx = int(offset)
        except ValueError:
            start_idx = 0
    
    # Get paginated items
    end_idx = start_idx + limit
    paginated_items = items[start_idx:end_idx]
    
    # Check if there are more items
    has_more = end_idx < len(items)
    
    next_page = None
    if has_more:
        next_offset = str(end_idx)
        next_page = NextPage(
            offset=next_offset,
            path=f"{base_path}?limit={limit}&offset={next_offset}",
            uri=f"{base_path}?limit={limit}&offset={next_offset}",
        )
    
    return PaginatedResponse(data=paginated_items, next_page=next_page)


class Pagination(BaseModel):
    """Query parameters for pagination."""
    limit: int = settings.DEFAULT_PAGE_SIZE
    offset: Optional[str] = None
    
    def apply(self, items: List[Any], base_path: str = "") -> PaginatedResponse:
        """Apply pagination to items."""
        return paginate(items, self.offset, self.limit, base_path)

