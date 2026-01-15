"""
Rules API endpoints.

Rules allow automating workflows in Asana by defining triggers and actions
that execute automatically when certain conditions are met.
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


class RuleModel:
    def __init__(self, gid: str, name: str, project_gid: str,
                 trigger: dict = None, action: dict = None, enabled: bool = True):
        self.gid = gid
        self.resource_type = "rule"
        self.name = name
        self.project_gid = project_gid
        self.trigger = trigger or {}
        self.action = action or {}
        self.enabled = enabled
        self.created_at = datetime.utcnow()

    def to_response(self):
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "name": self.name,
            "project": {"gid": self.project_gid, "resource_type": "project"},
            "trigger": self.trigger,
            "action": self.action,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


_rules = {}


@router.get("")
async def get_rules(
    project: str = Query(..., description="Project GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get rules in a project.
    
    Returns all automation rules defined in the specified project.
    Rules automate workflows by executing actions when triggers fire.
    """
    rules = [r for r in _rules.values() if r.project_gid == project]
    
    parser = OptFieldsParser(params.opt_fields)
    rule_responses = [parser.filter(r.to_response()) for r in rules]
    
    paginated = paginate(
        rule_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/rules",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }

