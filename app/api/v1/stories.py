from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ForbiddenError
from app.core.security import generate_gid
from app.models.task import Task
from app.models.story import Story
from app.schemas.story import StoryCreate, StoryUpdate
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


# Note: The get_stories and create_story endpoints that take task as query param
# are defined at the end of this file


@router.get("/{story_gid}")
async def get_story(
    story_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a story by GID.
    """
    result = await db.execute(select(Story).where(Story.gid == story_gid))
    story = result.scalar_one_or_none()
    
    if not story:
        raise NotFoundError("Story", story_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(story.to_response()))


@router.put("/{story_gid}")
async def update_story(
    story_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a story (comment).
    """
    result = await db.execute(select(Story).where(Story.gid == story_gid))
    story = result.scalar_one_or_none()
    
    if not story:
        raise NotFoundError("Story", story_gid)
    
    # Only comments can be edited
    if story.resource_subtype != "comment":
        raise ForbiddenError("Only comments can be edited")
    
    update_data = StoryUpdate(**data.get("data", {}))
    
    if update_data.text is not None:
        story.text = update_data.text
        story.html_text = f"<body>{update_data.text}</body>"
        story.is_edited = True
    
    if update_data.is_pinned is not None:
        story.is_pinned = update_data.is_pinned
    
    await db.commit()
    await db.refresh(story)
    
    return wrap_response(story.to_response())


@router.delete("/{story_gid}")
async def delete_story(
    story_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a story (comment).
    """
    result = await db.execute(select(Story).where(Story.gid == story_gid))
    story = result.scalar_one_or_none()
    
    if not story:
        raise NotFoundError("Story", story_gid)
    
    # Only comments can be deleted
    if story.resource_subtype != "comment":
        raise ForbiddenError("Only comments can be deleted")
    
    await db.delete(story)
    await db.commit()
    
    return wrap_response({})


@router.get("")
async def get_stories(
    task: str = Query(..., description="Task GID to get stories for"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get stories for a task.
    
    Returns all stories (comments and activity) on the specified task.
    """
    result = await db.execute(select(Task).where(Task.gid == task))
    if not result.scalar_one_or_none():
        raise NotFoundError("Task", task)
    
    result = await db.execute(
        select(Story)
        .where(Story.target_gid == task)
        .order_by(Story.created_at)
    )
    stories = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    story_responses = [parser.filter(s.to_response()) for s in stories]
    
    paginated = paginate(
        story_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/stories",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_story(
    task: str = Query(..., description="Task GID to create story on"),
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a comment on a task.
    
    Creates a new comment story on the specified task.
    """
    from app.core.security import generate_gid
    
    result = await db.execute(select(Task).where(Task.gid == task))
    if not result.scalar_one_or_none():
        raise NotFoundError("Task", task)
    
    story_data = StoryCreate(**data.get("data", {}))
    
    story = Story(
        gid=generate_gid(),
        text=story_data.text,
        html_text=f"<body>{story_data.text}</body>",
        resource_subtype="comment",
        type="comment",
        source="api",
        is_pinned=story_data.is_pinned,
        sticker_name=story_data.sticker_name,
        target_gid=task,
    )
    db.add(story)
    await db.commit()
    
    return wrap_response(story.to_response())

