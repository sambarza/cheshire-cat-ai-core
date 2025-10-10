import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse

from cat.types import ChatRequest, ChatResponse
from cat.auth.permissions import AuthResource, AuthPermission, check_permissions

router = APIRouter(prefix="", tags=["Home"])

@router.post("/message")
async def message(
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
    
@router.get("/", include_in_schema=False)
async def frontend() -> RedirectResponse: # HTMLResponse
    return RedirectResponse(url="http://localhost:5173")