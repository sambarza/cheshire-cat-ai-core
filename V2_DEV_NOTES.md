
# Version 2 dev notes

- Most core functionality has been moved to plugins so it can be easily extended or deactivated. Find them in `cat/core_plugins`.
- All websocket methods (`send_ws_message`, `send_chat_message`, `send_notification`, `send_error`) must be awaited as they are now async:

    ```python
        await send_ws_message(msg)
    ```
- `before_agent_starts` hook now has no argument aside `cat`, as all context/agent_input is directly stored and inserted into prompt based on the content of working memory (you can hook this via `agent_prompt_suffix`)
- `cat.llm` got a deep refactoring and has many options XXXXXX
- The cat vector memory can be completely deactivated, or some of it, and can be replaced/extended for example with a graph memory. See plugin `vector_memory`
- `StrayCat.working_memory.history` is not kept in RAM; history construction is delegated to plugins (so you can decide whether to keep it stored client side, cat side or another service side). Plugin `vector_memory` gives a good exapmle on how to do it.
- conversation history endpoints (GET and POST) have been deleted and there is a new CRUD for chat sessions in core plugin `XXXXXXX`. Convo history can also be passed via ws or http message.
- plugion can contain tests inside a folder names `tests`. This folder will be ignored by the cat at runtime but tests will be run by `pytest`
- it is now possible to have `@endpoint` with custom resource and permissions. They can be defined on the endpoint and must be matched by user permissions (which can be set via AuthHandler or users REST API)


## TODO

- MCP support
- update plugins so they attach to hooks exposed by core and provide their own hooks for other plugins


## Questions

- should core plugins hooks have priority 0 so they go first?