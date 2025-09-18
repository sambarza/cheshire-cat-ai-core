import time
from typing import Any, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, Body, Query
from sqlalchemy import select, update, delete, func, text, desc
from sqlalchemy.ext.asyncio import AsyncSession
from cat.auth.permissions import AuthPermission, AuthResource, check_permissions
from uuid import uuid4

from cat.convo.messages import Message, ChatContext
from cat.db.models import Chat as ChatDB
from cat.db import get_session

# TODOV2: add tests for this CRUD

router = APIRouter()


class Chat(BaseModel):
    id: str
    user_id: str
    context_id: str
    updated_at: int
    title: str
    messages: List[Message]


class ChatCreateUpdate(BaseModel):
    body: dict
    title: str


@router.get("")
async def get_chats(
    query: Optional[str] = Query(None, description="Search in the chats."),
    cat=check_permissions(AuthResource.CHAT, AuthPermission.LIST),
    db: AsyncSession = Depends(get_session),
) -> List[Chat]:
    """Get chats for a user."""

    stmt = select(ChatDB).where(ChatDB.user_id == cat.user_id)

    if query:
        # no vectors like in the 90s
        stmt = stmt.where(func.lower(func.cast(ChatDB.body, text)).ilike(f"%{query.lower()}%"))

    stmt = stmt.order_by(desc(ChatDB.updated_at)).limit(100)

    result = await db.execute(stmt)
    chats = result.scalars().all()
    return chats


@router.get("/{id}")
async def get_chat(
    id: str,
    cat=check_permissions(AuthResource.CHAT, AuthPermission.READ),
    db: AsyncSession = Depends(get_session),
) -> Chat:
    """Get a specific chat by id."""

    result = await db.execute(select(ChatDB).where(ChatDB.id == id))
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=404, detail="Not found.")

    return chat


@router.post("")
async def create_chat(
    data: ChatCreateUpdate = Body(...),
    cat=check_permissions(AuthResource.CHAT, AuthPermission.WRITE),
    db: AsyncSession = Depends(get_session),
) -> Chat:
    """Create a new chat."""

    if not data.title or not data.body:
        raise HTTPException(status_code=400, detail="title or body is missing")

    chat = ChatDB(
        id=str(uuid4()),
        user_id=cat.user_id,
        body=data.body,
        title=data.title,
        updated_at=int(time.time())
    )
    db.add(chat)
    return chat


@router.put("/{id}")
async def update_chat(
    id: str,
    data: ChatCreateUpdate = Body(...),
    cat=check_permissions(AuthResource.CHAT, AuthPermission.EDIT),
    db: AsyncSession = Depends(get_session),
) -> Chat:
    """Update a chat."""

    if not data.title or not data.body:
        raise HTTPException(status_code=400, detail="Title or body is missing")

    result = await db.execute(select(ChatDB).where(ChatDB.id == id))
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat.body = data.body
    chat.title = data.title
    chat.updated_at = int(time.time())

    return chat


@router.delete("/{id}")
async def delete_chat(
    id: str,
    cat=check_permissions(AuthResource.CHAT, AuthPermission.DELETE),
    db: AsyncSession = Depends(get_session),
):
    """Delete a specific chat"""

    result = await db.execute(select(ChatDB).where(ChatDB.id == id))
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=404, detail="Not found.")

    await db.delete(chat)
