from typing import List
from inspect import isclass

import json

from pydantic import BaseModel
from fastapi import APIRouter, Body, Request, HTTPException

from cat.auth import get_user, get_ccat
from cat.types import Message, Task, TaskResult
from cat.protocols.model_context.type_wrappers import TextContent, ToolCall as CatToolCall
from cat.protocols.agui.streaming import AGUIStream

from ag_ui.core import RunAgentInput

router = APIRouter(prefix="/agents", tags=["Agents"])

class AgentCard(BaseModel):
    slug: str
    name: str | None
    description: str | None
    plugin_id: str | None
    args_schema: dict | None = None


@router.get("")
async def list_agents(
    ccat=get_ccat(),
    _=get_user(),
) -> List[AgentCard]:
    """List all registered agents with full details."""

    agents = []
    for slug, Cls in ccat.factory.class_index.get("agents", {}).items():
        args_schema = None
        ArgsSchema = getattr(Cls, 'ArgsSchema', None)
        if ArgsSchema is not None and isclass(ArgsSchema) and issubclass(ArgsSchema, BaseModel):
            args_schema = ArgsSchema.model_json_schema()

        agents.append(AgentCard(
            slug=slug,
            name=Cls.name or Cls.__name__,
            description=Cls.description,
            plugin_id=Cls.plugin_id,
            args_schema=args_schema,
        ))
    return agents


@router.post("/{slug}/message")
async def agent_message(
    slug: str,
    http_request: Request,
    task: Task = Body(
        ...,
        openapi_examples={
            "simple": {
                "summary": "Simple text message",
                "value": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"type": "text", "text": "Meow!"}]
                        }
                    ],
                    "stream": False,
                }
            },
            "with_args": {
                "summary": "Message with agent args",
                "value": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"type": "text", "text": "Hello!"}]
                        }
                    ],
                    "args": {"temperature": 0.5},
                }
            }
        }
    ),
    _=get_user(),
    ccat=get_ccat(),
) -> TaskResult:
    """Send a message to a specific agent identified by its slug."""

    agent = await ccat.get(
        "agents",
        slug,
        request=http_request,
        raise_error=False
    )
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{slug}' not found."
        )

    if task.stream:
        return AGUIStream(agent, task).stream()
    else:
        return await agent(task)

@router.post("/{slug}/message_asgi")
async def agent_message_asgi(
    slug: str,
    input_data: RunAgentInput,
    http_request: Request,
    _=get_user(),
    ccat=get_ccat(),
) -> TaskResult:
    """Send a message to a specific agent identified by its slug."""

    task = translate_asgi_payload(input_data)

    agent = await ccat.get(
        "agents",
        slug,
        request=http_request,
        raise_error=False
    )
    if agent is None:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{slug}' not found."
        )

    if task.stream:
        return AGUIStream(agent, task).stream()
    else:
        return await agent(task)
    
def translate_asgi_payload(input_data: RunAgentInput) -> Task:
    """Translate an `ag_ui.core.RunAgentInput` into a `cat.types.Task`.

    Only map matching fields: messages (text blocks and tool calls). Other
    Task fields are left as defaults.

    Always set as stream
    """

    messages: list[Message] = []

    for m in input_data.messages:
        # role should already be one of: user, assistant, tool
        role = getattr(m, "role", "user")

        # build content blocks: map text fragments only
        content_blocks = []
        content = getattr(m, "content", None)
        if isinstance(content, str) or content is None:
            if content:
                content_blocks.append(TextContent(text=content))
        else:
            # content is a list of InputContent
            for c in content:
                ctype = getattr(c, "type", None)
                if ctype == "text":
                    text = getattr(c, "text", None)
                    if text:
                        content_blocks.append(TextContent(text=text))

        # map tool calls when present on assistant messages
        tool_calls_converted: list[CatToolCall] = []
        tc_list = getattr(m, "tool_calls", None)
        if tc_list:
            for tc in tc_list:
                # attempt to parse arguments string into dict
                args = {}
                func = getattr(tc, "function", None)
                arg_str = getattr(func, "arguments", None) if func is not None else None
                try:
                    if isinstance(arg_str, str) and arg_str:
                        args = json.loads(arg_str)
                except Exception:
                    args = {}

                name = getattr(func, "name", None) if func is not None else getattr(tc, "name", None)
                tool_calls_converted.append(CatToolCall(id=tc.id, name=name, args=args))

        msg = Message(
            role=role,
            content=content_blocks,
            tool_calls=tool_calls_converted or [],
        )

        # copy tool_call_id if present
        if getattr(m, "tool_call_id", None):
            msg.tool_call_id = m.tool_call_id

        messages.append(msg)

    return Task(messages=messages, stream=True)

    