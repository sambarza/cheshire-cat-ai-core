from typing import List, Literal

from cat.looking_glass import prompts
from cat.utils import BaseModelDict


class MessageContent(BaseModelDict):
    type: Literal["text", "image", "file", "tool_call", "json"] # TODOV2: to review
    text: str = ""
    image: str | None = None
    file: bytes | None = None # ?
    tool_call: dict | None = None # Maybe for rich media types, specific objects with mime_type
    json: dict | None = None

    def langchainfy(self):
        if self.type == "text":
            return self.text
        # TODOV2: support images


class Message(BaseModelDict):
    """Single message exchanged between user and assistant, part of a conversation."""

    role: Literal["user", "assistant"]
    content : MessageContent

    def langchainfy(self):
        if self.content.type == "text":
            return {
                "role": self.role,
                "content": self.content.langchainfy()
            }
    
    @staticmethod
    def delangchainfy(langchain_output):
        
        if len(langchain_output.content) > 0:
            return Message(
                role="assistant",
                content=MessageContent(
                    type="text",
                    text=langchain_output.content
                )
            )
    
        if len(langchain_output.tool_calls) > 0:
            return Message(
                role="assistant",
                content=MessageContent(
                    type="tool_call",
                    tool_call=langchain_output.tool_calls[0] # can it output more than one?
                )
            )
        


class ChatRequest(BaseModelDict):

    agent: str = "simple" # name of the agent to run. If None, the default one will be
    model: str = "vendor:model" # e.g. "openai:gpt-5". If None, default LLM will be picked up
    stream: bool = True # whether to stream tokens or not
    instructions: str = prompts.MAIN_PROMPT_PREFIX
    mcp_resources: List[str] = [] # should be a list of URIs
    # TODOV2: openai has also `tools` here, in the format { "type": "tool_name" }
    messages: List[Message] = [
        Message(
            role="user",
            content=MessageContent(
                type="text",
                text="Meow"
            )
        )
    ]
    # TODOV2: not sure how the client sends context other than MCP, messages and instructions?
    # TODOV2: should this object be immutable?


class ChatResponse(BaseModelDict):
    
    user_id: str # TODOV2: do we need the user_id here? Force and test it cannot be changed
    text: str
