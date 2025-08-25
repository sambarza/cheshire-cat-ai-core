
from fastmcp import FastMCP, Client
from fastmcp.resources import TextResource
from mcp.types import Tool


######################
# TODOV2: must be loaded from DB
mcp_servers_config = {
    "mcpServers": {
        "meta-mcp": {
            "url": "bzzz"
        },
    }
}
#######################

# Create in memory server for testing, otherwise tests get slow
server = FastMCP("TestInMemoryServer")

@server.tool
async def add(a: int, b: int) -> int:
    return a + b

@server.prompt
def explain_topic(topic: str, language: str) -> str:
    return f"Can you explain {topic} in {language}?"

@server.resource("resource://welcome-message")
def get_resource() -> str:
    return "This is a welcoming resource"


mcp_servers_config = server # TODO: hiding the real config for now


# using a wrapper class in case adjustments are needed
class MCPClient(Client):
    # TODOV2: keep client alive in case of disconnection (encapsulate!)
    async def list_tools(self) -> list[Tool]:
        return await super().list_tools()

