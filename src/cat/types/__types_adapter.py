from typing import Literal
from mcp import types as mcp_types
from pydantic import field_serializer, BaseModel

class Resource(mcp_types.Resource):
    @field_serializer("uri")
    def serialize_uri(self, uri):
        return str(self.uri)
    
ContentTypeLiteral = Literal[
    "text", "image", "audio", "resource_link", "resource"
]

class TextContent(mcp_types.TextContent):
    type: ContentTypeLiteral = "text"

class ImageContent(mcp_types.ImageContent):
    type: ContentTypeLiteral = "image"

class AudioContent(mcp_types.AudioContent):
    type: ContentTypeLiteral = "audio"

class ResourceLink(mcp_types.ResourceLink):
    type: ContentTypeLiteral = "resource_link"

class EmbeddedResource(mcp_types.EmbeddedResource):
    type: ContentTypeLiteral = "resource"

ContentBlock = TextContent | ImageContent | AudioContent | ResourceLink | EmbeddedResource