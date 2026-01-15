from typing import Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func

from app.api.deps import get_db, TaskQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.section import Section
from app.models.task import Task, TaskProject, TaskTag, TaskDependency, TaskFollower
from app.models.tag import Tag
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskDuplicateRequest,
    SetParentRequest, AddProjectRequest, RemoveProjectRequest,
    AddTagRequest, RemoveTagRequest,
    AddFollowersRequest, RemoveFollowersRequest,
    AddDependenciesRequest, RemoveDependenciesRequest,
    AddDependentsRequest, RemoveDependentsRequest,
)
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("")
async def get_tasks(
    params: TaskQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get multiple tasks with various filters.
    """
    query = select(Task)
    
    if params.project:
        query = (
            query.join(TaskProject, Task.gid == TaskProject.task_gid)
            .where(TaskProject.project_gid == params.project)
        )
    
    if params.section:
        query = query.where(Task.section_gid == params.section)
    
    if params.assignee:
        query = query.where(Task.assignee_gid == params.assignee)
    
    query = query.order_by(Task.created_at.desc())
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    task_responses = [parser.filter(t.to_response()) for t in tasks]
    
    paginated = paginate(
        task_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/tasks",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_task(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new task.
    """
    task_data = TaskCreate(**data.get("data", {}))
    
    task = Task(
        gid=generate_gid(),
        name=task_data.name,
        notes=task_data.notes,
        html_notes=task_data.html_notes,
        resource_subtype=task_data.resource_subtype,
        assignee_gid=task_data.assignee,
        due_on=task_data.due_on,
        due_at=task_data.due_at,
        start_on=task_data.start_on,
        start_at=task_data.start_at,
        parent_gid=task_data.parent,
    )
    db.add(task)
    await db.flush()
    
    # Add to projects
    if task_data.projects:
        for project_gid in task_data.projects:
            task_project = TaskProject(
                gid=generate_gid(),
                task_gid=task.gid,
                project_gid=project_gid,
            )
            db.add(task_project)
    
    # Add tags
    if task_data.tags:
        for tag_gid in task_data.tags:
            task_tag = TaskTag(
                gid=generate_gid(),
                task_gid=task.gid,
                tag_gid=tag_gid,
            )
            db.add(task_tag)
    
    # Add followers
    if task_data.followers:
        for user_gid in task_data.followers:
            follower = TaskFollower(
                gid=generate_gid(),
                task_gid=task.gid,
                user_gid=user_gid,
            )
            db.add(follower)
    
    # Always add creator as follower
    creator_follower = TaskFollower(
        gid=generate_gid(),
        task_gid=task.gid,
    )
    db.add(creator_follower)
    
    # Update parent task's subtask count
    if task_data.parent:
        result = await db.execute(select(Task).where(Task.gid == task_data.parent))
        parent = result.scalar_one_or_none()
        if parent:
            parent.num_subtasks += 1
    
    await db.commit()
    
    return wrap_response(task.to_response())


@router.get("/search")
async def search_tasks(
    workspace: str = Query(..., description="Workspace GID"),
    text: Optional[str] = Query(None),
    assignee_any: Optional[str] = Query(None),
    projects_any: Optional[str] = Query(None),
    tags_any: Optional[str] = Query(None),
    completed: Optional[bool] = Query(None),
    is_subtask: Optional[bool] = Query(None),
    sort_by: str = Query("modified_at"),
    sort_ascending: bool = Query(False),
    limit: int = Query(20),
    offset: Optional[str] = Query(None),
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Search for tasks in a workspace.
    """
    # Start with tasks in projects within the workspace
    query = (
        select(Task)
        .distinct()
        .join(TaskProject, Task.gid == TaskProject.task_gid)
        .join(Project, TaskProject.project_gid == Project.gid)
        .where(Project.workspace_gid == workspace)
    )
    
    if text:
        query = query.where(
            or_(
                Task.name.ilike(f"%{text}%"),
                Task.notes.ilike(f"%{text}%"),
            )
        )
    
    if assignee_any:
        assignee_gids = [a.strip() for a in assignee_any.split(",")]
        query = query.where(Task.assignee_gid.in_(assignee_gids))
    
    if projects_any:
        project_gids = [p.strip() for p in projects_any.split(",")]
        query = query.where(TaskProject.project_gid.in_(project_gids))
    
    if tags_any:
        tag_gids = [t.strip() for t in tags_any.split(",")]
        query = (
            query.join(TaskTag, Task.gid == TaskTag.task_gid)
            .where(TaskTag.tag_gid.in_(tag_gids))
        )
    
    if completed is not None:
        query = query.where(Task.completed == completed)
    
    if is_subtask is not None:
        if is_subtask:
            query = query.where(Task.parent_gid.isnot(None))
        else:
            query = query.where(Task.parent_gid.is_(None))
    
    # Sorting
    sort_column = getattr(Task, sort_by, Task.modified_at)
    if sort_ascending:
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    parser = OptFieldsParser(opt_fields)
    task_responses = [parser.filter(t.to_response()) for t in tasks]
    
    paginated = paginate(
        task_responses,
        offset=offset,
        limit=limit,
        base_path="/tasks/search",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.get("/{task_gid}")
async def get_task(
    task_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a task by GID.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    parser = OptFieldsParser(opt_fields)
    response = task.to_response()
    
    # Add projects
    if parser.has_field("projects"):
        result = await db.execute(
            select(TaskProject).where(TaskProject.task_gid == task_gid)
        )
        task_projects = result.scalars().all()
        response["projects"] = [
            {"gid": tp.project_gid, "resource_type": "project"}
            for tp in task_projects
        ]
    
    # Add tags
    if parser.has_field("tags"):
        result = await db.execute(
            select(TaskTag).where(TaskTag.task_gid == task_gid)
        )
        task_tags = result.scalars().all()
        response["tags"] = [
            {"gid": tt.tag_gid, "resource_type": "tag"}
            for tt in task_tags
        ]
    
    # Add followers
    if parser.has_field("followers"):
        result = await db.execute(
            select(TaskFollower).where(TaskFollower.task_gid == task_gid)
        )
        followers = result.scalars().all()
        response["followers"] = [
            {"gid": f.user_gid, "resource_type": "user"}
            for f in followers
        ]
    
    return wrap_response(parser.filter(response))


@router.put("/{task_gid}")
async def update_task(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    update_data = TaskUpdate(**data.get("data", {}))
    
    for field, value in update_data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(task, field, value)
    
    if update_data.completed and not task.completed_at:
        task.completed_at = datetime.utcnow()
    elif update_data.completed is False:
        task.completed_at = None
    
    await db.commit()
    await db.refresh(task)
    
    return wrap_response(task.to_response())


@router.delete("/{task_gid}")
async def delete_task(
    task_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    # Update parent's subtask count
    if task.parent_gid:
        result = await db.execute(select(Task).where(Task.gid == task.parent_gid))
        parent = result.scalar_one_or_none()
        if parent and parent.num_subtasks > 0:
            parent.num_subtasks -= 1
    
    await db.delete(task)
    await db.commit()
    
    return wrap_response({})


@router.post("/{task_gid}/duplicate")
async def duplicate_task(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Duplicate a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    dup_data = TaskDuplicateRequest(**data.get("data", {}))
    include = dup_data.include or []
    
    new_task = Task(
        gid=generate_gid(),
        name=dup_data.name,
        notes=task.notes if "notes" in include else None,
        html_notes=task.html_notes if "notes" in include else None,
        resource_subtype=task.resource_subtype,
        assignee_gid=task.assignee_gid if "assignee" in include else None,
        due_on=task.due_on if "dates" in include else None,
        due_at=task.due_at if "dates" in include else None,
        start_on=task.start_on if "dates" in include else None,
        parent_gid=task.parent_gid if "parent" in include else None,
    )
    db.add(new_task)
    await db.flush()
    
    # Copy projects
    if "projects" in include:
        result = await db.execute(
            select(TaskProject).where(TaskProject.task_gid == task_gid)
        )
        for tp in result.scalars().all():
            new_tp = TaskProject(
                gid=generate_gid(),
                task_gid=new_task.gid,
                project_gid=tp.project_gid,
                section_gid=tp.section_gid,
            )
            db.add(new_tp)
    
    # Copy tags
    if "tags" in include:
        result = await db.execute(
            select(TaskTag).where(TaskTag.task_gid == task_gid)
        )
        for tt in result.scalars().all():
            new_tt = TaskTag(
                gid=generate_gid(),
                task_gid=new_task.gid,
                tag_gid=tt.tag_gid,
            )
            db.add(new_tt)
    
    await db.commit()
    
    # Return job response
    from app.models.job import Job
    job = Job(
        gid=generate_gid(),
        resource_subtype="duplicate_task",
        status="succeeded",
        new_task_gid=new_task.gid,
    )
    db.add(job)
    await db.commit()
    
    return wrap_response(job.to_response())


@router.get("/{task_gid}/subtasks")
async def get_subtasks(
    task_gid: str,
    limit: int = Query(20),
    offset: Optional[str] = Query(None),
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get subtasks of a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Task", task_gid)
    
    result = await db.execute(
        select(Task)
        .where(Task.parent_gid == task_gid)
        .order_by(Task.order)
    )
    subtasks = result.scalars().all()
    
    parser = OptFieldsParser(opt_fields)
    subtask_responses = [parser.filter(t.to_response()) for t in subtasks]
    
    paginated = paginate(
        subtask_responses,
        offset=offset,
        limit=limit,
        base_path=f"/tasks/{task_gid}/subtasks",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("/{task_gid}/subtasks")
async def create_subtask(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a subtask.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    parent = result.scalar_one_or_none()
    
    if not parent:
        raise NotFoundError("Task", task_gid)
    
    task_data = data.get("data", {})
    task_data["parent"] = task_gid
    
    return await create_task({"data": task_data}, db)


@router.post("/{task_gid}/setParent")
async def set_parent(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Set the parent of a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    request_data = SetParentRequest(**data.get("data", {}))
    new_parent_gid = request_data.parent
    
    # Update old parent's subtask count
    if task.parent_gid:
        result = await db.execute(select(Task).where(Task.gid == task.parent_gid))
        old_parent = result.scalar_one_or_none()
        if old_parent and old_parent.num_subtasks > 0:
            old_parent.num_subtasks -= 1
    
    # Update new parent's subtask count
    result = await db.execute(select(Task).where(Task.gid == new_parent_gid))
    new_parent = result.scalar_one_or_none()
    if not new_parent:
        raise NotFoundError("Task", new_parent_gid)
    
    new_parent.num_subtasks += 1
    task.parent_gid = new_parent_gid
    
    await db.commit()
    await db.refresh(task)
    
    return wrap_response(task.to_response())


@router.get("/{task_gid}/dependencies")
async def get_dependencies(
    task_gid: str,
    limit: int = Query(20),
    offset: Optional[str] = Query(None),
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get dependencies of a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Task", task_gid)
    
    result = await db.execute(
        select(Task)
        .join(TaskDependency, Task.gid == TaskDependency.depends_on_gid)
        .where(TaskDependency.task_gid == task_gid)
    )
    dependencies = result.scalars().all()
    
    parser = OptFieldsParser(opt_fields)
    dep_responses = [parser.filter(t.to_response()) for t in dependencies]
    
    paginated = paginate(
        dep_responses,
        offset=offset,
        limit=limit,
        base_path=f"/tasks/{task_gid}/dependencies",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("/{task_gid}/addDependencies")
async def add_dependencies(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add dependencies to a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    dep_str = data.get("data", {}).get("dependencies", "")
    dep_gids = [d.strip() for d in dep_str.split(",") if d.strip()]
    
    for dep_gid in dep_gids:
        # Check if dependency already exists
        result = await db.execute(
            select(TaskDependency)
            .where(TaskDependency.task_gid == task_gid)
            .where(TaskDependency.depends_on_gid == dep_gid)
        )
        if not result.scalar_one_or_none():
            dependency = TaskDependency(
                gid=generate_gid(),
                task_gid=task_gid,
                depends_on_gid=dep_gid,
            )
            db.add(dependency)
    
    await db.commit()
    
    # Return dependencies
    result = await db.execute(
        select(Task)
        .join(TaskDependency, Task.gid == TaskDependency.depends_on_gid)
        .where(TaskDependency.task_gid == task_gid)
    )
    dependencies = result.scalars().all()
    
    return {
        "data": [t.to_response() for t in dependencies]
    }


@router.post("/{task_gid}/removeDependencies")
async def remove_dependencies(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove dependencies from a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    dep_str = data.get("data", {}).get("dependencies", "")
    dep_gids = [d.strip() for d in dep_str.split(",") if d.strip()]
    
    for dep_gid in dep_gids:
        result = await db.execute(
            select(TaskDependency)
            .where(TaskDependency.task_gid == task_gid)
            .where(TaskDependency.depends_on_gid == dep_gid)
        )
        dependency = result.scalar_one_or_none()
        if dependency:
            await db.delete(dependency)
    
    await db.commit()
    
    return {"data": []}


@router.get("/{task_gid}/dependents")
async def get_dependents(
    task_gid: str,
    limit: int = Query(20),
    offset: Optional[str] = Query(None),
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get tasks that depend on this task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Task", task_gid)
    
    result = await db.execute(
        select(Task)
        .join(TaskDependency, Task.gid == TaskDependency.task_gid)
        .where(TaskDependency.depends_on_gid == task_gid)
    )
    dependents = result.scalars().all()
    
    parser = OptFieldsParser(opt_fields)
    dep_responses = [parser.filter(t.to_response()) for t in dependents]
    
    paginated = paginate(
        dep_responses,
        offset=offset,
        limit=limit,
        base_path=f"/tasks/{task_gid}/dependents",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("/{task_gid}/addProject")
async def add_task_to_project(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a task to a project.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    request_data = AddProjectRequest(**data.get("data", {}))
    
    # Check if already in project
    result = await db.execute(
        select(TaskProject)
        .where(TaskProject.task_gid == task_gid)
        .where(TaskProject.project_gid == request_data.project)
    )
    if not result.scalar_one_or_none():
        task_project = TaskProject(
            gid=generate_gid(),
            task_gid=task_gid,
            project_gid=request_data.project,
            section_gid=request_data.section,
        )
        db.add(task_project)
        await db.commit()
    
    return wrap_response(task.to_response())


@router.post("/{task_gid}/removeProject")
async def remove_task_from_project(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove a task from a project.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    request_data = RemoveProjectRequest(**data.get("data", {}))
    
    result = await db.execute(
        select(TaskProject)
        .where(TaskProject.task_gid == task_gid)
        .where(TaskProject.project_gid == request_data.project)
    )
    task_project = result.scalar_one_or_none()
    
    if task_project:
        await db.delete(task_project)
        await db.commit()
    
    return wrap_response(task.to_response())


@router.post("/{task_gid}/addTag")
async def add_tag_to_task(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a tag to a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    request_data = AddTagRequest(**data.get("data", {}))
    
    # Check if already tagged
    result = await db.execute(
        select(TaskTag)
        .where(TaskTag.task_gid == task_gid)
        .where(TaskTag.tag_gid == request_data.tag)
    )
    if not result.scalar_one_or_none():
        task_tag = TaskTag(
            gid=generate_gid(),
            task_gid=task_gid,
            tag_gid=request_data.tag,
        )
        db.add(task_tag)
        await db.commit()
    
    return wrap_response(task.to_response())


@router.post("/{task_gid}/removeTag")
async def remove_tag_from_task(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove a tag from a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    request_data = RemoveTagRequest(**data.get("data", {}))
    
    result = await db.execute(
        select(TaskTag)
        .where(TaskTag.task_gid == task_gid)
        .where(TaskTag.tag_gid == request_data.tag)
    )
    task_tag = result.scalar_one_or_none()
    
    if task_tag:
        await db.delete(task_tag)
        await db.commit()
    
    return wrap_response(task.to_response())


@router.post("/{task_gid}/addFollowers")
async def add_followers_to_task(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add followers to a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    followers_str = data.get("data", {}).get("followers", "")
    follower_gids = [f.strip() for f in followers_str.split(",") if f.strip()]
    
    for user_gid in follower_gids:
        result = await db.execute(
            select(TaskFollower)
            .where(TaskFollower.task_gid == task_gid)
            .where(TaskFollower.user_gid == user_gid)
        )
        if not result.scalar_one_or_none():
            follower = TaskFollower(
                gid=generate_gid(),
                task_gid=task_gid,
                user_gid=user_gid,
            )
            db.add(follower)
    
    await db.commit()
    
    return wrap_response(task.to_response())


@router.post("/{task_gid}/removeFollowers")
async def remove_followers_from_task(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove followers from a task.
    """
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_gid)
    
    followers_str = data.get("data", {}).get("followers", "")
    follower_gids = [f.strip() for f in followers_str.split(",") if f.strip()]
    
    for user_gid in follower_gids:
        result = await db.execute(
            select(TaskFollower)
            .where(TaskFollower.task_gid == task_gid)
            .where(TaskFollower.user_gid == user_gid)
        )
        follower = result.scalar_one_or_none()
        if follower:
            await db.delete(follower)
    
    await db.commit()
    
    return wrap_response(task.to_response())


@router.get("/{task_gid}/stories")
async def get_task_stories(
    task_gid: str,
    limit: int = Query(20),
    offset: Optional[str] = Query(None),
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get stories (comments and activity) on a task.
    """
    from app.models.story import Story
    
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Task", task_gid)
    
    result = await db.execute(
        select(Story)
        .where(Story.target_gid == task_gid)
        .order_by(Story.created_at)
    )
    stories = result.scalars().all()
    
    parser = OptFieldsParser(opt_fields)
    story_responses = [parser.filter(s.to_response()) for s in stories]
    
    paginated = paginate(
        story_responses,
        offset=offset,
        limit=limit,
        base_path=f"/tasks/{task_gid}/stories",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("/{task_gid}/stories")
async def create_task_story(
    task_gid: str,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a comment on a task.
    """
    from app.models.story import Story
    from app.schemas.story import StoryCreate
    
    result = await db.execute(select(Task).where(Task.gid == task_gid))
    if not result.scalar_one_or_none():
        raise NotFoundError("Task", task_gid)
    
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
        target_gid=task_gid,
    )
    db.add(story)
    await db.commit()
    
    return wrap_response(story.to_response())

