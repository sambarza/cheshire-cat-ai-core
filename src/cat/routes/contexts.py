from datetime import datetime
from pydantic import BaseModel

from cat.convo.messages import ChatContext
from cat.auth.permissions import AuthResource
from cat.db.models import ContextDB
from .crud import create_crud

class ContextModelCreateUpdate(BaseModel):
    title: str
    body: ChatContext = ChatContext()

class ContextModelSelect(ContextModelCreateUpdate):
    id: str
    title: str
    updated_at: datetime
    chats: None | list = None

router = create_crud(
    db_model=ContextDB,
    prefix="/contexts",
    tag="Contexts",
    auth_resource=AuthResource.CHAT,
    select_schema=ContextModelSelect,
    create_schema=ContextModelCreateUpdate,
    update_schema=ContextModelCreateUpdate,
    restrict_by_user_id=True
)

