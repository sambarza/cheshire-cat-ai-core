
import json
from typing import List
from importlib import metadata

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from cat.protocols.agui import encoder, events
from cat.auth.permissions import AuthPermission, AuthResource, check_permissions
from cat.types.chats import ChatRequest, ChatResponse
from cat.utils import BaseModelDict


router = APIRouter()


class StatusResponse(BaseModelDict):
    status: str
    version: str
    llms: List[str]
    embedders: List[str]
    agents: List[str]

# server status
@router.get("/status")
async def status(
    r: Request,
    cat=check_permissions(AuthResource.STATUS, AuthPermission.READ),
) -> StatusResponse:
    """Server status"""

    ccat = r.app.state.ccat
    return StatusResponse(
        status = "We're all mad here, dear!",
        version = metadata.version("cheshire-cat-ai"),
        llms=ccat.llms.keys(),
        embedders=ccat.embedders.keys(),
        agents=ccat.agents.keys()
    )


@router.post("/chat") # TODOV2: change name
async def chat(
    chat_request: ChatRequest,
    cat=check_permissions(AuthResource.CHAT, AuthPermission.EDIT),
) -> ChatResponse:
    
    if chat_request.stream:
        async def event_stream():
            async for msg in cat.run(chat_request):
                yield f"data: {json.dumps(dict(msg))}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    else:
        return await cat(chat_request)


# TODOV2: notifications should be under a GET endpoint with SSE
