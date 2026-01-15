"""
Budgets API endpoints.

Budgets allow tracking and managing financial allocations for projects
and portfolios in Asana.
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


class BudgetModel:
    def __init__(self, gid: str, name: str, amount: float, currency_code: str,
                 project_gid: str = None, portfolio_gid: str = None,
                 time_period_gid: str = None):
        self.gid = gid
        self.resource_type = "budget"
        self.name = name
        self.amount = amount
        self.currency_code = currency_code
        self.project_gid = project_gid
        self.portfolio_gid = portfolio_gid
        self.time_period_gid = time_period_gid
        self.spent_amount = 0.0
        self.created_at = datetime.utcnow()

    def to_response(self):
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "amount": self.amount,
            "currency_code": self.currency_code,
            "spent_amount": self.spent_amount,
            "remaining_amount": self.amount - self.spent_amount,
            "project": {"gid": self.project_gid, "resource_type": "project"} if self.project_gid else None,
            "portfolio": {"gid": self.portfolio_gid, "resource_type": "portfolio"} if self.portfolio_gid else None,
            "time_period": {"gid": self.time_period_gid, "resource_type": "time_period"} if self.time_period_gid else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


_budgets = {}


@router.get("")
async def get_budgets(
    project: Optional[str] = Query(None, description="Filter by project GID"),
    portfolio: Optional[str] = Query(None, description="Filter by portfolio GID"),
    time_period: Optional[str] = Query(None, description="Filter by time period GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get multiple budgets.
    
    Returns all budgets, optionally filtered by project, portfolio, or time period.
    """
    budgets = list(_budgets.values())
    
    if project:
        budgets = [b for b in budgets if b.project_gid == project]
    if portfolio:
        budgets = [b for b in budgets if b.portfolio_gid == portfolio]
    if time_period:
        budgets = [b for b in budgets if b.time_period_gid == time_period]
    
    parser = OptFieldsParser(params.opt_fields)
    budget_responses = [parser.filter(b.to_response()) for b in budgets]
    
    paginated = paginate(
        budget_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/budgets",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_budget(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new budget.
    
    Creates a new budget for tracking financial allocations.
    """
    budget_data = data.get("data", {})
    
    name = budget_data.get("name")
    if not name:
        raise ValidationError("name is required")
    
    amount = budget_data.get("amount")
    if amount is None:
        raise ValidationError("amount is required")
    
    currency_code = budget_data.get("currency_code", "USD")
    
    budget = BudgetModel(
        gid=generate_gid(),
        name=name,
        amount=amount,
        currency_code=currency_code,
        project_gid=budget_data.get("project"),
        portfolio_gid=budget_data.get("portfolio"),
        time_period_gid=budget_data.get("time_period"),
    )
    
    _budgets[budget.gid] = budget
    
    return wrap_response(budget.to_response())


@router.get("/{budget_gid}")
async def get_budget(
    budget_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a single budget by GID.
    
    Returns the complete budget record including spent and remaining amounts.
    """
    budget = _budgets.get(budget_gid)
    
    if not budget:
        raise NotFoundError("Budget", budget_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(budget.to_response()))


@router.put("/{budget_gid}")
async def update_budget(
    budget_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a budget.
    
    Updates the budget with new values for name, amount, or currency.
    """
    budget = _budgets.get(budget_gid)
    
    if not budget:
        raise NotFoundError("Budget", budget_gid)
    
    update_data = data.get("data", {})
    
    if "name" in update_data:
        budget.name = update_data["name"]
    if "amount" in update_data:
        budget.amount = update_data["amount"]
    if "currency_code" in update_data:
        budget.currency_code = update_data["currency_code"]
    if "spent_amount" in update_data:
        budget.spent_amount = update_data["spent_amount"]
    
    return wrap_response(budget.to_response())


@router.delete("/{budget_gid}")
async def delete_budget(
    budget_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a budget.
    
    Permanently removes the specified budget from the system.
    """
    if budget_gid not in _budgets:
        raise NotFoundError("Budget", budget_gid)
    
    del _budgets[budget_gid]
    
    return wrap_response({})

