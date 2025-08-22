import asyncio
from typing import Dict
import tomli
import json
import asyncio
from fastapi import APIRouter, Body, Request
from fastapi.responses import StreamingResponse

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
    
    if chat_request.stream:
        async def event_stream():
            async for msg in cat.run(chat_request):
                yield f"data: {json.dumps(msg)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    else:
        return await cat(chat_request)


# TODOV2: notifications should be under a GET endpoint with SSE
