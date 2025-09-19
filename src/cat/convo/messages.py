from typing import List, Literal

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolCall,
    ToolMessage
)

from cat.looking_glass import prompts
from cat.utils import BaseModelDict


# TODOV2: maybe there sohuld be a small class for each content type? looks verbose
class MessageContent(BaseModelDict):
    type: Literal[
        "text", "image",
        "tool", "elicitation",
        "custom"
    ] # TODOV2: to review
    text: str = ""
    image: str | None = None
    tool: dict | None = None # output of a tool (not used for tool input, which is stored in assistant message under .tool_calls)
    elicitation : dict | None = None # json_schema for the input required
    custom: dict | None = None  # perfect for unpredicted creative utilization 
                                #   (i.e. state deltas, canvas, any json, or rich media)
                                #   Maybe for rich media types, specific objects with mime_type


class Message(BaseModelDict):
    """Single message exchanged between user and assistant, part of a conversation."""

    role: Literal["user", "assistant", "tool"]
    content : MessageContent

    # only populated if the LLM wants to use a tool (role "assistant")
    # role "tool" is only used for tool output, to update messages list
    tool_calls : List[dict] = [] 

    def langchainfy(self):
        if self.role == "user":
            return HumanMessage(
                content=self.content.text
            )
        elif self.role == "assistant":
            return AIMessage(
                content=self.content.text,
                tool_calls=self.tool_calls
            )
        elif self.role == "tool":
            return ToolMessage(
                content=self.content.tool["out"],
                tool_call_id=self.content.tool["in"]["id"],
                name=self.content.tool["in"]["name"]
            )
        else:
            raise Exception
    
    @classmethod
    def from_langchain(cls, langchain_msg):
        # assuming it is always an AIMessage
        tool_calls = []
        text = langchain_msg.content
        if hasattr(langchain_msg, "tool_calls") \
            and len(langchain_msg.tool_calls) > 0:
            
            tool_calls = langchain_msg.tool_calls
            # Otherwise empty
            text = str(langchain_msg.tool_calls)
            
        return cls(
            role="assistant",
            tool_calls=tool_calls,
            content=MessageContent(
                type="text", # assuming LLM output is text only
                text=text,
            )
        )

class ChatContext(BaseModelDict):
    instructions: str = prompts.MAIN_PROMPT_PREFIX
    resources: List[str] = []
    # TODOV2: should also tools be supported here?

class ChatRequest(BaseModelDict):

    agent: str = "default" # name of the agent to run.
    model: str = "default" # e.g. "openai:gpt-5"
    stream: bool = True # whether to stream tokens or not
    context: ChatContext = ChatContext()
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
    text: str = ""
