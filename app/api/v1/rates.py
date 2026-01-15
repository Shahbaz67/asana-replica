"""
Rates API endpoints.

Rates define the cost per hour or other unit for users on projects,
allowing for accurate cost tracking and budgeting.
"""
from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


class RateModel:
    def __init__(self, gid: str, user_gid: str, project_gid: str,
                 amount: float, currency_code: str = "USD",
                 rate_type: str = "hourly"):
        self.gid = gid
        self.resource_type = "rate"
        self.user_gid = user_gid
        self.project_gid = project_gid
        self.amount = amount
        self.currency_code = currency_code
        self.rate_type = rate_type
        self.created_at = datetime.utcnow()

    def to_response(self):
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "user": {"gid": self.user_gid, "resource_type": "user"},
            "project": {"gid": self.project_gid, "resource_type": "project"} if self.project_gid else None,
            "amount": self.amount,
            "currency_code": self.currency_code,
            "rate_type": self.rate_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


_rates = {}


@router.get("")
async def get_rates(
    project: Optional[str] = Query(None, description="Filter by project GID"),
    user: Optional[str] = Query(None, description="Filter by user GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get multiple rates.
    
    Returns all rates, optionally filtered by project or user.
    """
    rates = list(_rates.values())
    
    if project:
        rates = [r for r in rates if r.project_gid == project]
    if user:
        rates = [r for r in rates if r.user_gid == user]
    
    parser = OptFieldsParser(params.opt_fields)
    rate_responses = [parser.filter(r.to_response()) for r in rates]
    
    paginated = paginate(
        rate_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/rates",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_rate(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new rate.
    
    Creates a rate defining the cost per unit for a user on a project.
    """
    rate_data = data.get("data", {})
    
    user_gid = rate_data.get("user")
    if not user_gid:
        raise ValidationError("user is required")
    
    amount = rate_data.get("amount")
    if amount is None:
        raise ValidationError("amount is required")
    
    rate = RateModel(
        gid=generate_gid(),
        user_gid=user_gid,
        project_gid=rate_data.get("project"),
        amount=amount,
        currency_code=rate_data.get("currency_code", "USD"),
        rate_type=rate_data.get("rate_type", "hourly"),
    )
    
    _rates[rate.gid] = rate
    
    return wrap_response(rate.to_response())


@router.get("/{rate_gid}")
async def get_rate(
    rate_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a single rate by GID.
    
    Returns the complete rate record including amount and currency.
    """
    rate = _rates.get(rate_gid)
    
    if not rate:
        raise NotFoundError("Rate", rate_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(rate.to_response()))


@router.put("/{rate_gid}")
async def update_rate(
    rate_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a rate.
    
    Updates the rate with new amount, currency, or type.
    """
    rate = _rates.get(rate_gid)
    
    if not rate:
        raise NotFoundError("Rate", rate_gid)
    
    update_data = data.get("data", {})
    
    if "amount" in update_data:
        rate.amount = update_data["amount"]
    if "currency_code" in update_data:
        rate.currency_code = update_data["currency_code"]
    if "rate_type" in update_data:
        rate.rate_type = update_data["rate_type"]
    
    return wrap_response(rate.to_response())


@router.delete("/{rate_gid}")
async def delete_rate(
    rate_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a rate.
    
    Permanently removes the specified rate from the system.
    """
    if rate_gid not in _rates:
        raise NotFoundError("Rate", rate_gid)
    
    del _rates[rate_gid]
    
    return wrap_response({})

