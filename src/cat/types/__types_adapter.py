from mcp.types import Resource
from mcp.types import TextContent
from mcp.types import ImageContent
from mcp.types import AudioContent
from mcp.types import ResourceLink
from mcp.types import EmbeddedResource

class AdapterResource(Resource):
    pass

class AdapterTextContent(TextContent):
    pass

AdapterContentBlock = TextContent | ImageContent | AudioContent | ResourceLink | EmbeddedResource