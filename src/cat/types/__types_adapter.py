from mcp import types as mcp_types
from pydantic import field_serializer, BaseModel

class Resource(mcp_types.Resource):
    @field_serializer("uri")
    def serialize_uri(self, uri):
        return str(self.uri)

class TextContent(mcp_types.TextContent):
    pass

class ImageContent(mcp_types.ImageContent):
    pass

class AudioContent(mcp_types.AudioContent):
    pass

class ResourceLink(mcp_types.ResourceLink):
    pass

class EmbeddedResource(mcp_types.EmbeddedResource):
    pass

ContentBlock = TextContent | ImageContent | AudioContent | ResourceLink | EmbeddedResource