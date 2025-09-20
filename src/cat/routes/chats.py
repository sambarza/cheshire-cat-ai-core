from typing import List, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from cat.auth.permissions import AuthResource
from cat.convo.messages import Message, ChatContext
from cat.db.models import ChatDB, ContextDB
from .crud import create_crud

class Chat(BaseModel):
    name: str = "A Chat"
    messages: List[Message] = []

class ChatCreateUpdate(Chat):
    context_id: UUID # TODOV2: validate context_id against the DB

class ChatSelectBase(Chat):
    id: UUID
    updated_at: datetime

class ChatSelect(ChatSelectBase):
    context_id: UUID

class RelatedContext(BaseModel):
    id: UUID
    name: str
    resources: List[str]
    instructions: str
    updated_at: datetime

class ChatSelectExpanded(ChatSelectBase):
    context: RelatedContext

router = create_crud(
    db_model=ChatDB,
    prefix="/chats",
    tag="Chats",
    auth_resource=AuthResource.CHAT,
    select_schema=ChatSelect | ChatSelectExpanded,
    create_schema=ChatCreateUpdate,
    update_schema=ChatCreateUpdate,
    restrict_by_user_id=True,
)

