from typing import List
from pydantic import BaseModel

from mcp.types import TextContent

from .messages import Message
from .contexts import Context

class ChatRequest(BaseModel):

    agent: str = "default" # name of the agent to run.
    model: str = "default" # e.g. "openai:gpt-5"
    embedder: str = "default"
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
    stream: bool = True # whether to stream tokens or not
    # TODOV2: should this object be immutable?


class ChatResponse(BaseModel):
    messages: List[Message]