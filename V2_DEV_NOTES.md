
# Version 2 dev notes

- Most core functionality has been moved to plugins so it can be easily extended, deactivated or totally replaced. See `cat/mad_hatter/core_plugins` to find them.

- All websocket methods (`send_ws_message`, `send_chat_message`, `send_notification`, `send_error`) must be awaited as they are now async:

    ```python
        await send_ws_message(msg)
    ```
- `before_agent_starts` hook now has no argument aside `cat`, as all context/agent_input is directly stored and inserted into prompt based on the content of working memory
- `cat.llm` got a deep refactoring and has many options XXXXXX