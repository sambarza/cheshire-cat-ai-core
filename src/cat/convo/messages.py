from typing import List, Literal

from cat.utils import BaseModelDict


class ChatMessageContent(BaseModelDict):

    type: Literal["input_text", "input_image", "input_file"]
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

    model: str | None = None # e.g. "openai:gpt-5". If None, default LLM will be picked up
    stream: bool = True # whether to stream tokens or not
    instructions: str | None = None
    messages: List[ChatMessage] = [
        ChatMessage(
            role="user",
            content=ChatMessageContent(
                type="input_text",
                text="Meow"
            )
        )
    ]


class ChatResponse(BaseModelDict):
    
    user_id: str # TODOV2: do we need the user_id here? Force and test it cannot be changed
    text: str
