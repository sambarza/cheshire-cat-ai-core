from typing import List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from cat.convo.messages import ChatContext, Message
from cat.auth.permissions import AuthResource
from cat.db.models import ContextDB
from .crud import create_crud

class ContextCreateUpdate(ChatContext):
    name: str = "A Context"

class ContextSelectBase(ContextCreateUpdate):
    id: UUID
    updated_at: datetime

class ContextSelect(ContextSelectBase):
    chat_ids: List[UUID]

class RelatedChat(BaseModel):
    id: UUID
    name: str
    messages: List[Message]
    updated_at: datetime

class ContextSelectExpanded(ContextSelectBase):
    chats: List[RelatedChat] = []


router = create_crud(
    db_model=ContextDB,
    prefix="/contexts",
    tag="Contexts",
    auth_resource=AuthResource.CHAT,
    select_schema=ContextSelect | ContextSelectExpanded,
    create_schema=ContextCreateUpdate,
    update_schema=ContextCreateUpdate,
    restrict_by_user_id=True,
)

