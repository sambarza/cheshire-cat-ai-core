from typing import Dict
from uuid import UUID
from pydantic import BaseModel, HttpUrl

from cat.auth.permissions import AuthResource
from cat.db.models import ConnectorDB
from ..common.crud import create_crud
from ..common.schemas import CRUDSelect, CRUDUpdate
from .registry import router as registry_router


class TokenSecret(BaseModel):
    token: str
    refresh: str

class KeySecret(BaseModel):
    key: str

class Connector(BaseModel):
    url: HttpUrl

class ConnectorSelect(CRUDSelect, Connector):
    active: bool = True
    manifest: Dict = {}

class ConnectorCreateUpdate(CRUDUpdate, Connector):
    secret: TokenSecret | KeySecret

router = create_crud(
    db_model=ConnectorDB,
    prefix="/connectors",
    tag="MCP Servers",
    auth_resource=AuthResource.CONNECTOR,
    restrict_by_user_id=True,
    select_schema=ConnectorSelect,
    create_schema=ConnectorCreateUpdate,
    update_schema=ConnectorCreateUpdate
)

@router.put("/{id}/toggle")
async def toggle():
    return "todo"

# add registry router
router.include_router(registry_router)

