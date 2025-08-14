
# Version 2 dev notes

- Most core functionality has been moved to plugins so it can be easily extended, deactivated or totally replaced. See `cat/mad_hatter/core_plugins` to find them.

- All websocket methods (`send_ws_message`, `send_chat_message`, `send_notification`, `send_error`) must be awaited as they are now async:

    ```python
        await send_ws_message(msg)
    ```