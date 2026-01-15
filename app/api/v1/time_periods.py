from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError
from app.models.time_period import TimePeriod
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("")
async def get_time_periods(
    workspace: str = Query(..., description="Workspace GID"),
    start_on: Optional[str] = Query(None, description="Filter by periods starting on or after this date"),
    end_on: Optional[str] = Query(None, description="Filter by periods ending on or before this date"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get time periods for a workspace.
    
    Time periods are used for goal tracking and can represent
    fiscal years, quarters, months, etc.
    """
    query = select(TimePeriod).where(TimePeriod.parent_gid == workspace)
    
    if start_on:
        from datetime import date
        try:
            start_date = date.fromisoformat(start_on)
            query = query.where(TimePeriod.start_on >= start_date)
        except ValueError:
            pass
    
    if end_on:
        from datetime import date
        try:
            end_date = date.fromisoformat(end_on)
            query = query.where(TimePeriod.end_on <= end_date)
        except ValueError:
            pass
    
    query = query.order_by(TimePeriod.start_on.desc())
    
    result = await db.execute(query)
    periods = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    period_responses = [parser.filter(p.to_response()) for p in periods]
    
    paginated = paginate(
        period_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/time_periods",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.get("/{time_period_gid}")
async def get_time_period(
    time_period_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a time period by GID.
    """
    result = await db.execute(
        select(TimePeriod).where(TimePeriod.gid == time_period_gid)
    )
    period = result.scalar_one_or_none()
    
    if not period:
        raise NotFoundError("TimePeriod", time_period_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(period.to_response()))


