from typing import List, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from cat.convo.messages import ChatContext, Message
from cat.auth.permissions import AuthResource
from cat.db.models import ContextDB, ChatDB
from .crud import create_crud


class RelatedChat(BaseModel):
    id: UUID
    title: str
    body: List[Message]
    updated_at: datetime

class ContextModelCreateUpdate(BaseModel):
    title: str = "Context {}"
    body: ChatContext = ChatContext()

class ContextModelSelect(ContextModelCreateUpdate):
    id: UUID
    title: str
    updated_at: datetime
    #chats: List[RelatedChat] | None = None

    model_config = ConfigDict(
        extra="allow"
    )

router = create_crud(
    db_model=ContextDB,
    prefix="/contexts",
    tag="Contexts",
    auth_resource=AuthResource.CHAT,
    select_schema=ContextModelSelect,
    create_schema=ContextModelCreateUpdate,
    update_schema=ContextModelCreateUpdate,
    restrict_by_user_id=True,
)

