import json
from typing import List
from importlib import metadata
from pydantic import BaseModel

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from cat.protocols.agui import encoder, events
from cat.auth.permissions import AuthPermission, AuthResource, check_permissions
from cat.types.chats import ChatRequest, ChatResponse
from cat.utils import BaseModelDict


router = APIRouter(prefix="/connectors/registry", tags=["MCP"])

REGISTRY_URL = "https://registry.modelcontextprotocol.io/v0/servers"

class Connector(BaseModel):
    status: str
    version: str
    llms: List[str]
    embedders: List[str]
    agents: List[str]

# server status
@router.get("")
async def get_list(
    cat=check_permissions(AuthResource.CONNECTOR, AuthPermission.LIST),
) -> List[Connector]:
    """MCP servers available in registry."""