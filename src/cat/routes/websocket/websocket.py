
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from cat.auth.permissions import AuthPermission, AuthResource
from cat.auth.connection import WebsocketAuth
from cat.log import log

router = APIRouter()


@router.websocket("/ws")
@router.websocket("/ws/{user_id}") # TODOV2: remove, because the user is taken form the jwt
async def websocket_endpoint(
    websocket: WebSocket,
    cat=Depends(WebsocketAuth(AuthResource.CHAT, AuthPermission.EDIT)), # check_permissions only for http
):
    await websocket.accept()

    # TODOV2: support both legacy {"type": "chat_token", "content": "token"} and AGUI

    try:
        while True:

            # Receive the next message from WebSocket.
            user_message = await websocket.receive_json()

            # http endpoints may have been called while waiting for a message
            cat.load_working_memory_from_cache()

            async for msg in cat.run(user_message):
                await websocket.send_json(msg)

    except WebSocketDisconnect:
        log.info(f"WebSocket connection closed for user {cat.user_id}")
    except Exception:
        log.error("Error in websocket loop")