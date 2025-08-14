
# Version 2 dev notes

- All websocket methods (`send_ws_message`, `send_chat_message`, `send_notification`, `send_error`) must be awaited as they are now async:

    ```python
        await send_ws_message(msg)
    ```