"""
Reactions API endpoints.

Reactions allow users to respond to stories (comments) with emoji reactions,
similar to reactions in other collaboration tools.
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


class ReactionModel:
    def __init__(self, gid: str, story_gid: str, user_gid: str, emoji: str):
        self.gid = gid
        self.resource_type = "reaction"
        self.story_gid = story_gid
        self.user_gid = user_gid
        self.emoji = emoji
        self.created_at = datetime.utcnow()

    def to_response(self):
        return {
            "gid": self.gid,
            "resource_type": self.resource_type,
            "emoji": self.emoji,
            "user": {"gid": self.user_gid, "resource_type": "user"},
        }


_reactions = {}


@router.get("")
async def get_reactions(
    story: str = Query(..., description="Story GID to get reactions for"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get reactions on a story.
    
    Returns all reactions (emoji responses) on the specified story/comment.
    """
    reactions = [r for r in _reactions.values() if r.story_gid == story]
    
    parser = OptFieldsParser(params.opt_fields)
    reaction_responses = [parser.filter(r.to_response()) for r in reactions]
    
    paginated = paginate(
        reaction_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/reactions",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }

