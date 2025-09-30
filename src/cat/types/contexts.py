from typing import List
from pydantic import BaseModel, field_serializer
from mcp.types import Resource as MCPResource

from cat.looking_glass import prompts

class Resource(MCPResource):
    @field_serializer("uri")
    def serialize_uri(self, uri):
        return str(self.uri)

class Context(BaseModel):
    instructions: str = prompts.MAIN_PROMPT_PREFIX
    resources: List[Resource] = []
    # TODOV2: should also tools be supported here?