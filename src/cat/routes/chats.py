from typing import List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from cat.auth.permissions import AuthResource
from cat.convo.messages import Message, ChatContext
from cat.db.models import ChatDB, ContextDB
from .crud import create_crud


class ChatModelCreateUpdate(BaseModel):
    title: str
    body: List[Message] = []
    context_id: str # TODOV2: validate context_id against the DB


class ChatModelSelect(ChatModelCreateUpdate):
    id: UUID
    title: str
    updated_at: datetime
    #context: None | ChatContext = None

router = create_crud(
    db_model=ChatDB,
    prefix="/chats",
    tag="Chats",
    auth_resource=AuthResource.CHAT,
    select_schema=ChatModelSelect,
    create_schema=ChatModelCreateUpdate,
    update_schema=ChatModelCreateUpdate,
    restrict_by_user_id=True,
)

