from typing import Any, Optional
from datetime import date

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.models.task import Task
from app.models.time_tracking import TimeTrackingEntry
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("")
async def get_time_tracking_entries(
    task: str = Query(..., description="Task GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get time tracking entries for a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task))
    if not result.scalar_one_or_none():
        raise NotFoundError("Task", task)
    
    result = await db.execute(
        select(TimeTrackingEntry)
        .where(TimeTrackingEntry.task_gid == task)
        .order_by(TimeTrackingEntry.entered_on.desc())
    )
    entries = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    entry_responses = [parser.filter(e.to_response()) for e in entries]
    
    paginated = paginate(
        entry_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/time_tracking_entries",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_time_tracking_entry(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a time tracking entry.
    """
    entry_data = data.get("data", {})
    
    task_gid = entry_data.get("task")
    if not task_gid:
        raise ValidationError("task is required")
    
    # Verify task exists
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Task", task_gid)
    
    duration_minutes = entry_data.get("duration_minutes")
    if duration_minutes is None:
        raise ValidationError("duration_minutes is required")
    
    entered_on = entry_data.get("entered_on")
    if entered_on:
        try:
            entered_on = date.fromisoformat(entered_on)
        except ValueError:
            raise ValidationError("Invalid date format for entered_on")
    else:
        entered_on = date.today()
    
    entry = TimeTrackingEntry(
        gid=generate_gid(),
        task_gid=task_gid,
        duration_minutes=duration_minutes,
        entered_on=entered_on,
    )
    db.add(entry)
    await db.commit()
    
    return wrap_response(entry.to_response())


@router.get("/{time_tracking_entry_gid}")
async def get_time_tracking_entry(
    time_tracking_entry_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a time tracking entry by GID.
    """
    result = await db.execute(
        select(TimeTrackingEntry).where(TimeTrackingEntry.gid == time_tracking_entry_gid)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise NotFoundError("TimeTrackingEntry", time_tracking_entry_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(entry.to_response()))


@router.put("/{time_tracking_entry_gid}")
async def update_time_tracking_entry(
    time_tracking_entry_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a time tracking entry.
    """
    result = await db.execute(
        select(TimeTrackingEntry).where(TimeTrackingEntry.gid == time_tracking_entry_gid)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise NotFoundError("TimeTrackingEntry", time_tracking_entry_gid)
    
    update_data = data.get("data", {})
    
    if "duration_minutes" in update_data:
        entry.duration_minutes = update_data["duration_minutes"]
    
    if "entered_on" in update_data:
        try:
            entry.entered_on = date.fromisoformat(update_data["entered_on"])
        except ValueError:
            raise ValidationError("Invalid date format for entered_on")
    
    await db.commit()
    await db.refresh(entry)
    
    return wrap_response(entry.to_response())


@router.delete("/{time_tracking_entry_gid}")
async def delete_time_tracking_entry(
    time_tracking_entry_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a time tracking entry.
    """
    result = await db.execute(
        select(TimeTrackingEntry).where(TimeTrackingEntry.gid == time_tracking_entry_gid)
    )
    entry = result.scalar_one_or_none()
    
    if not entry:
        raise NotFoundError("TimeTrackingEntry", time_tracking_entry_gid)
    
    await db.delete(entry)
    await db.commit()
    
    return wrap_response({})


@router.get("/tasks/{task_gid}/time_tracking_entries")
async def get_time_tracking_entries_for_task(
    task_gid: str,
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get time tracking entries for a task.
    
    Returns all time tracking entries associated with the specified task.
    Alternative endpoint path matching Asana API structure.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Task", task_gid)
    
    result = await db.execute(
        select(TimeTrackingEntry)
        .where(TimeTrackingEntry.task_gid == task_gid)
        .order_by(TimeTrackingEntry.entered_on.desc())
    )
    entries = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    entry_responses = [parser.filter(e.to_response()) for e in entries]
    
    paginated = paginate(
        entry_responses,
        offset=params.offset,
        limit=params.limit,
        base_path=f"/tasks/{task_gid}/time_tracking_entries",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


