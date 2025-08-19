
from fastmcp import FastMCP, Client
from fastmcp.resources import TextResource


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

# Add a resource to the server - a simple text resource
welcome_resource = TextResource(
    uri="resource://welcome-message",
    name="Welcome Message",
    text="This is a welcoming resource",
    tags={"welcome", "info"}
)
server.add_resource(welcome_resource)



mcp_servers_config = server # TODO: hiding the real config for now


# using a wrapper class in case adjustments are needed
class MCPClient(Client):
    # TODOV2: keep client alive in case of disconnection (encapsulate!)
    pass

