from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.core.exceptions import NotFoundError
from app.models.job import Job
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response


router = APIRouter()


@router.get("/{job_gid}")
async def get_job(
    job_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a job by GID.
    
    Jobs represent asynchronous operations in Asana. When you perform
    an operation that takes time (like duplicating a project), Asana
    returns a job that you can poll to check on the status.
    
    Job statuses:
    - not_started: The job has been queued but not started
    - in_progress: The job is currently running
    - succeeded: The job completed successfully
    - failed: The job failed
    """
    result = await db.execute(select(Job).where(Job.gid == job_gid))
    job = result.scalar_one_or_none()
    
    if not job:
        raise NotFoundError("Job", job_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(job.to_response()))


