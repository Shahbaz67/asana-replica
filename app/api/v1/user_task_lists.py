from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.user_task_list import UserTaskList
from app.models.task import Task
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("/{user_task_list_gid}")
async def get_user_task_list(
    user_task_list_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a user task list by GID.
    
    A user task list represents the "My Tasks" list for a user in a
    specific workspace.
    """
    result = await db.execute(
        select(UserTaskList).where(UserTaskList.gid == user_task_list_gid)
    )
    task_list = result.scalar_one_or_none()
    
    if not task_list:
        raise NotFoundError("UserTaskList", user_task_list_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(task_list.to_response()))


@router.get("/{user_task_list_gid}/tasks")
async def get_user_task_list_tasks(
    user_task_list_gid: str,
    completed_since: Optional[str] = Query(None),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get tasks in a user's task list.
    
    Returns tasks assigned to the user in the workspace associated
    with this task list.
    """
    result = await db.execute(
        select(UserTaskList).where(UserTaskList.gid == user_task_list_gid)
    )
    task_list = result.scalar_one_or_none()
    
    if not task_list:
        raise NotFoundError("UserTaskList", user_task_list_gid)
    
    # Get tasks assigned to this user
    query = (
        select(Task)
        .where(Task.assignee_gid == task_list.owner_gid)
        .order_by(Task.created_at.desc())
    )
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    task_responses = [parser.filter(t.to_response()) for t in tasks]
    
    paginated = paginate(
        task_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/user_task_lists/{user_task_list_gid}/tasks",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


