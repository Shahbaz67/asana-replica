from typing import Any, Optional
import os
import uuid

from fastapi import APIRouter, Depends, Query, Body, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, CommonQueryParams
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import generate_gid
from app.models.task import Task
from app.models.attachment import Attachment
from app.schemas.attachment import AttachmentCreate
from app.utils.pagination import paginate
from app.utils.filters import OptFieldsParser
from app.utils.response import wrap_response
from app.config import settings


router = APIRouter()


@router.get("")
async def get_attachments(
    parent: str = Query(..., description="Parent task GID"),
    params: CommonQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get attachments for a task.
    """
    result = await db.execute(select(Task).where(Task.gid == parent))
    if not result.scalar_one_or_none():
        raise NotFoundError("Task", parent)
    
    result = await db.execute(
        select(Attachment)
        .where(Attachment.parent_gid == parent)
        .order_by(Attachment.created_at.desc())
    )
    attachments = result.scalars().all()
    
    parser = OptFieldsParser(params.opt_fields)
    attachment_responses = [parser.filter(a.to_response()) for a in attachments]
    
    paginated = paginate(
        attachment_responses,
        offset=params.offset,
        limit=params.limit,
        base_path="/attachments",
    )
    
    return {
        "data": paginated.data,
        "next_page": paginated.next_page.model_dump() if paginated.next_page else None,
    }


@router.post("")
async def create_attachment(
    parent: str = Query(..., description="Parent task GID"),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Query(None, description="URL for external attachment"),
    name: Optional[str] = Query(None, description="Name of the attachment"),
    resource_subtype: str = Query("asana", description="Type of attachment"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create an attachment on a task.
    """
    result = await db.execute(select(Task).where(Task.gid == parent))
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", parent)
    
    if file:
        # Handle file upload
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}{file_ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, file_name)
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Check file size
        contents = await file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise ValidationError(f"File size exceeds maximum of {settings.MAX_UPLOAD_SIZE} bytes")
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        attachment = Attachment(
            gid=generate_gid(),
            name=file.filename or name or "Attachment",
            resource_subtype="asana",
            host="asana",
            download_url=f"/uploads/{file_name}",
            view_url=f"/uploads/{file_name}",
            permanent_url=f"/uploads/{file_name}",
            size=len(contents),
            parent_gid=parent,
        )
    elif url:
        # Handle external URL attachment
        attachment = Attachment(
            gid=generate_gid(),
            name=name or url.split("/")[-1] or "External Attachment",
            resource_subtype=resource_subtype,
            host=resource_subtype if resource_subtype != "asana" else "external",
            download_url=url,
            view_url=url,
            permanent_url=url,
            parent_gid=parent,
        )
    else:
        raise ValidationError("Either file or url must be provided")
    
    db.add(attachment)
    await db.commit()
    
    return wrap_response(attachment.to_response())


@router.get("/{attachment_gid}")
async def get_attachment(
    attachment_gid: str,
    opt_fields: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get an attachment by GID.
    """
    result = await db.execute(select(Attachment).where(Attachment.gid == attachment_gid))
    attachment = result.scalar_one_or_none()
    
    if not attachment:
        raise NotFoundError("Attachment", attachment_gid)
    
    parser = OptFieldsParser(opt_fields)
    return wrap_response(parser.filter(attachment.to_response()))


@router.delete("/{attachment_gid}")
async def delete_attachment(
    attachment_gid: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete an attachment.
    """
    result = await db.execute(select(Attachment).where(Attachment.gid == attachment_gid))
    attachment = result.scalar_one_or_none()
    
    if not attachment:
        raise NotFoundError("Attachment", attachment_gid)
    
    # Delete file if it's a local attachment
    if attachment.host == "asana" and attachment.download_url:
        file_name = attachment.download_url.split("/")[-1]
        file_path = os.path.join(settings.UPLOAD_DIR, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    await db.delete(attachment)
    await db.commit()
    
    return wrap_response({})

