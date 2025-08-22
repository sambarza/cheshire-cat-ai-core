import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from cat.auth.permissions import AuthPermission, AuthResource
from cat.auth.connection import WebsocketAuth
from cat.looking_glass.stray_cat import StrayCat
from cat.log import log

router = APIRouter()


@router.websocket("/ws")
@router.websocket("/ws/{user_id}") # TODOV2: remove, because the user is taken form the jwt
async def websocket_endpoint(
    websocket: WebSocket,
    cat=Depends(WebsocketAuth(AuthResource.CONVERSATION, AuthPermission.WRITE)), # check_permissions only for http
):
    await websocket.accept()

    try:
        while True:

            # Receive the next message from WebSocket.
            user_message = await websocket.receive_json()

            # http endpoints may have been called while waiting for a message
            cat.load_working_memory_from_cache()

            async for msg in cat.run(user_message):
                await websocket.send_json(msg)

    except Exception:
        log.error("Error in websocket loop")
        await websocket.close()




"""
    # Add the new WebSocket connection to the manager.
    websocket_manager = websocket.scope["app"].state.websocket_manager
    websocket_manager.add_connection(cat.user_id, websocket)

    try:
        # Process messages
        await handle_messages(websocket, cat)
    except WebSocketDisconnect:
        log.info(f"WebSocket connection closed for user {cat.user_id}")
    finally:

        # cat's working memory in this scope has not been updated
        cat.load_working_memory_from_cache()

        # Remove connection on disconnect
        websocket_manager.remove_connection(cat.user_id)
"""