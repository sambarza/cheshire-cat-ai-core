from typing import List, Literal

from cat.looking_glass import prompts
from cat.utils import BaseModelDict


class ChatMessageContent(BaseModelDict):

    type: Literal["input_text", "input_image", "input_file"] # TODOV2: by OpenAI, maybe better use the Ollama spec
    text: str | None
    image_url: str | None = None
    file_url: str | None = None


class ChatMessage(BaseModelDict):

    role: Literal["user", "assistant"]
    content : ChatMessageContent

    def langchainfy(self):
        # TODOV2: support images
        return {
            "role": self.role,
            "content": self.content.text
        }


class ChatRequest(BaseModelDict):

    agent: str = "simple" # name of the agent to run. If None, the default one will be
    model: str = "vendor:model" # e.g. "openai:gpt-5". If None, default LLM will be picked up
    stream: bool = True # whether to stream tokens or not
    instructions: str | None = prompts.MAIN_PROMPT_PREFIX
    mcp_resources: List[str] = [] # should be a list of URIs
    # TODOV2: openai has also `tools` here, in the format { "type": "tool_name" }
    messages: List[ChatMessage] = [
        ChatMessage(
            role="user",
            content=ChatMessageContent(
                type="input_text",
                text="Meow"
            )
        )
    ]
    # TODOV2: not sure how the client sends context other than MCP, messages and instructions?


class ChatResponse(BaseModelDict):
    
    user_id: str # TODOV2: do we need the user_id here? Force and test it cannot be changed
    text: str
