
from fastmcp import FastMCP, Client


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

mcp_servers_config = server # TODO: hiding the real config for now


# using a wrapper class in case adjustments are needed
class MCPClient(Client):
    # TODOV2: keep client alive in case of disconnection (encapsulate!)
    pass

