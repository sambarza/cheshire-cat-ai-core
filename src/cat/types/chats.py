from typing import List
from pydantic import BaseModel

from mcp.types import Resource, TextContent

from cat.looking_glass import prompts
from .messages import Message

class Context(BaseModel):
    instructions: str = prompts.MAIN_PROMPT_PREFIX
    resources: List[Resource] = []
    # TODOV2: should also tools be supported here?

class ChatRequest(BaseModel):

    agent: str = "default" # name of the agent to run.
    model: str = "default" # e.g. "openai:gpt-5"
    stream: bool = True # whether to stream tokens or not
    context: Context = Context()
    messages: List[Message] = [
        Message(
            role="user",
            content=TextContent(
                type="text",
                text="Meow"
            )
        )
    ]
    # TODOV2: not sure how the client sends context other than MCP, messages and instructions?
    # TODOV2: should this object be immutable?


class ChatResponse(BaseModel):
    messages: List[Message]