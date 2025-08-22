
# Version 2 dev notes

- Most core functionality has been moved to plugins so it can be easily extended or deactivated. Find them in `cat/core_plugins`.
- There are many changes and most plugins need to be adjusted (will provide a dedicated guide). The old admin still works with v2 via core plugin `legacy_v1`.
- All websocket methods (`send_ws_message`, `send_chat_message`, `send_notification`, `send_error`) must be awaited as they are now async:

    ```python
        await send_ws_message(msg)
    ```
- `before_agent_starts` hook now has no argument aside `cat`, as all context/agent_input is directly stored and inserted into prompt based on the content of working memory (you can hook this via `agent_prompt_suffix`)
- `cat.llm` got a deep refactoring and has many options XXXXXX
- The cat vector memory can be completely deactivated, or some of it, and can be replaced/extended for example with a graph memory. See plugin `qdrant_vector_memory`
- `StrayCat.working_memory.history` is not kept in RAM; history construction is delegated to plugins (so you can decide whether to keep it stored client side, cat side or another service side). Plugin `qdrant_vector_memory` gives a good exapmle on how to do it.
- conversation history endpoints (GET and POST) have been deleted and there is a new CRUD for chat sessions in core plugin `XXXXXXX`. Convo history can also be passed via ws or http message.
- plugion can contain tests inside a folder names `tests`. This folder will be ignored by the cat at runtime but tests will be run by `pytest`
- it is now possible to have `@endpoint` with custom resource and permissions. They can be defined on the endpoint and must be matched by user permissions (which can be set via AuthHandler or users REST API)
- input and output data structure have changed, but by keeping active the core_plugin `legacy_v1` old clients should still work (make a PR if you find bugs)
- you have now in `cat.chat_request` an object of type `ChatRequest`, containing user input and convo history, and in `cat.chat_response` an object of type `ChatResponse`.  
`cat.chat_response` is available since the beginning of the message flow. This is to avoid patterns in which devs stored in working memory stuff to be added later on in the final response via `before_cat_send_message`. Now you can store output data directly in `cat.chat_response` and the client will receive that data.  
Both `cat.chat_request` and `cat.chat_response` are cleared at each message. Use `cat.working_memory` to store arbitrary information across the whole conversation.
- `plugins`, `static` and `data` folders live now in the root folder of a project, and are automatically created at first launch. In this way the cat can be used as a simple python package. Docker compose installation is also simplified by opening a single volume. Core plugins stay inside the package, in `cat/core_plugins` and can be deactivated but not uninstalled (not sure about this).
- Due to difficulties in keeping up with langchain, core only depends on `langchain_core`. All LLM and embedder vendors are now packed in core_plugin `langchain_models_pack` so they are isolated and more easily maintained.
- We only support chat models, text-only or multimodal. Pure completion models are not supported anymore. If you need to use one, create your own LLM adapter and hook it via `factory_allowed_llms`
- Embedders are not automatically associated with the chosen LLM vendor. You will need to configure that yourself, The cat will notify you at every message if the embedder is not set.
- endpoint `/message` has been moved to core_plugin `legacy_v1`, so it is still available. The main http enbdpoint to chat with the cat is `/chat` and must receive a `ChatRequest` JSON, which is very similar to the format use by all major LLM/assistant vendors. The endpoint supports streaming
- Auth system semplifications (TODO review):
 - All endpoints, http and websocket, start close (except `/auth/token` and `/auth/login`)
 - You can now login into `/docs` using username and password
 - The default `CCAT_API_KEY` is `meow`.
 - The default `CCAT_JWT_SECRET` is `meow_jwt`
 - Both the key and the jwt must be sent via header `Authorization: Bearer xxx`.
 - `CCAT_API_KEY_WS` does not exist anymore.
 - If you are calling the cat machine-to-machine, use `CCAT_API_KEY`, for both http and ws. Websocket in a machine-to-machine settings supports headers, so you can follow the same schema (query parameter `?token=` is not supported anymore). TODO: still active just for dev v2
 - If you are calling the cat form an unsecure client (a browser), use *only* jwt auth.
 - You need to authenticate also to see `/docs` and there is a little form to do it in the page
 - TODO users crud


## TODO

- update core plugins so they attach to hooks exposed by core and provide their own hooks for other plugins
- statelessness is paramount to avoid side effects and scalability. Just working_memory and settings should be saved, as a simple JSON or in a DB. Plugins will deal with long term memories
- which DB to use internally? easiest route is to go `sql_alchemy` and ship with a default `sqlite`, that can be changed to a `postgres` for scalability and statelessness
- `qdrant_vector_memory` should deal with embedder changes, maybe reactivating the snapshot
- security must be always ON, also on a fresh installation, with a default jwt secret and API key. Pages in `/docs` should allow logging in
- model selection should be possible to do directly via message, i.e. `"model": "openai:gpt-5" or "ollama:qwen:7b"`. If model is not passed, a default model chosen by admin in the settings will be used. Admin still decides which models are available to end users. Still to determine how to adapt the permissions system to this.
- `StrayCat.__call_` should be an async generator using `yield` to send tokens and notifications. Those yielded result are then managed at the transport layer (websocket or http/streaming/sse). Cat internals should know absolutely nothing about network protocols.
- core plugins cannot really save settings in their own path (package is not editable). Maybe ship core_plugins in standard plugins folder?

## Questions

- should core plugins be shipped in an internal folder in the external plugins?
- should core plugins hooks have priority 0 so they go first?
- should all hooks be able to return a ChatResponse and interrupt the flow with the direct final response?
- should core_plugins be present in `./plugins`
- new plugins with custom requirements may not work as expected (need a restart).
- should we ship a small LLM and embedder via llama.cpp or other lightweight runner?
- as there are docker and pyPI releases, makes no sense to have a `develop` branch
- move settings out of plugins?

## Installation

- contributor:
  ```bash
  git clone ....
  uv run cat
  ```

- user:
  ```bash
  uv init --bare mycat
  cd mycat
  uv add cheshire-cat-ai
  uv run cat
  ```

- action:
 ```bash
 uv sync
 uv build
 uv publish --token={TOKEN}
 ```