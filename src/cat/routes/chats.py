from typing import List
from uuid import UUID
from pydantic import BaseModel

from cat.convo.messages import Message
from cat.auth.permissions import AuthResource
from cat.db.models import ChatDB
from .common.crud import create_crud
from .common.schemas import CRUDSelect, CRUDUpdate

# TODO: import from messages
class Context(CRUDSelect):
    instructions: str = "No instructions"
    resources: List[str] = []
    
class ChatCreateUpdate(CRUDUpdate):
    messages: List[Message] = []
    context_id: UUID

class Chat(CRUDSelect):
    messages: List[Message]
    context: Context

router = create_crud(
    db_model=ChatDB,
    prefix="/chats",
    tag="Chats",
    auth_resource=AuthResource.CHAT,
    restrict_by_user_id=True,
    select_schema=Chat,
    create_schema=ChatCreateUpdate,
    update_schema=ChatCreateUpdate
)

