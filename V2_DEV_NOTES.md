
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
- input and output data structure have changed, but by keeping active the core_plugin `legacy_v1` old clients should still work (make a PR if you find bugs)
- you have now in `cat.chat_request` an object of type `ChatRequest`, containing user input and convo history, and in `cat.chat_response` an object of type `ChatResponse`.  
`cat.chat_response` is available since the beginning of the message flow. This is to avoid patterns in which devs stored in working memory stuff to be added later on in the final response via `before_cat_send_message`. Now you can store output data directly in `cat.chat_response` and the client will receive that data.  
Both `cat.chat_request` and `cat.chat_response` are cleared at each message. Use `cat.working_memory` to store arbitrary information across the whole conversation.


## TODO

- MCP support
- update plugins so they attach to hooks exposed by core and provide their own hooks for other plugins
- statelessness is paramount to avoid side effects and scalability. Just working_memory should be saved, as a simple JSON or in a DB. Plugins will deal with long term memories


## Questions

- should core plugins hooks have priority 0 so they go first?
- should all hooks be able to return a ChatResponse and interrupt the flow with the direct final response?