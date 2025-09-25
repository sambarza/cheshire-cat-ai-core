from typing import List
from uuid import UUID
from pydantic import BaseModel

from cat.convo.messages import Message, ChatContext
from cat.auth.permissions import AuthResource
from cat.db.models import ContextDB
from .common.crud import create_crud
from .common.schemas import CRUDSelect, CRUDUpdate

class ChatSelect(CRUDSelect):
    messages: List[Message]

class ContextCreateUpdate(CRUDUpdate, ChatContext):
    pass

class Context(CRUDSelect, ContextCreateUpdate):
    chats: List[ChatSelect] = []

router = create_crud(
    db_model=ContextDB,
    prefix="/contexts",
    tag="Contexts",
    auth_resource=AuthResource.CHAT,
    restrict_by_user_id=True,
    select_schema=Context,
    create_schema=ContextCreateUpdate,
    update_schema=ContextCreateUpdate
)

