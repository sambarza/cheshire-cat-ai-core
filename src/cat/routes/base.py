from fastapi import APIRouter, Body
from typing import Dict
import tomli

from cat.auth.permissions import AuthPermission, AuthResource, check_permissions
from cat.convo.messages import ChatRequest, ChatResponse
from cat.utils import BaseModelDict
from cat.log import log

router = APIRouter()

class StatusResponse(BaseModelDict):
    status: str
    version: str

# server status
@router.get("/status")
async def status(
    cat=check_permissions(AuthResource.STATUS, AuthPermission.READ),
) -> StatusResponse:
    """Server status"""
    with open("pyproject.toml", "rb") as f:
        project_toml = tomli.load(f)["project"]

    return StatusResponse(
        status = "We're all mad here, dear!",
        version =  project_toml["version"]
    )


@router.post("/chat")
async def chat(
    chat_request: ChatRequest,
    cat=check_permissions(AuthResource.CONVERSATION, AuthPermission.WRITE),
) -> ChatResponse:
    
    return await cat.run(chat_request, True)