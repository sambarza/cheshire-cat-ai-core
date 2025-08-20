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



def callback_to_async_generator(func_with_callback, message_request):
    queue = asyncio.Queue()

    async def gen():
        while True:
            msg = await queue.get()
            if msg is None:  # End of stream signal
                break
            yield msg
            queue.task_done()

    async def message_callback(msg):
        # Put each token immediately
        await queue.put(msg)

    async def runner():
        # Run the callback-driven function directly and await each emission
        await func_with_callback(message_request, message_callback=message_callback)
        await queue.put(None)  # Signal completion

    # Run the producer in a background task so it produces while consumer yields
    asyncio.create_task(runner())

    return gen()



@router.post("/chat")
async def chat(
    chat_request: ChatRequest,
    cat=check_permissions(AuthResource.CONVERSATION, AuthPermission.WRITE),
) -> ChatResponse:
    
    if chat_request.stream:
        event_generator = callback_to_async_generator(cat, chat_request)

        async def event_stream():
            async for msg in event_generator:
                yield f"data: {json.dumps(msg)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    else:
        return await cat(chat_request)



@router.post("/sse")
async def sse(
    #chat_request: ChatRequest,
    cat=check_permissions(AuthResource.CONVERSATION, AuthPermission.READ),
):
    async def event_generator():
        for i in range(1, 11):
            event = {"number": i}
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(1)  # simulate delay

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# TODOV2: notifications should be under a GET endpoint with SSE (same as MCP)
