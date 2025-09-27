from datetime import datetime
from cachetools import TTLCache
from fastmcp import FastMCP
from fastmcp.client import Client, StreamableHttpTransport
from fastmcp.tools import Tool
from fastmcp.prompts import Prompt
from fastmcp.resources import Resource


# Create in memory server for testing, otherwise tests get slow
server = FastMCP("TestInMemoryServer")

@server.tool
async def add(a: int, b: int) -> int:
    return a + b

@server.tool
async def get_the_time() -> str:
    return str(datetime.now())

@server.tool
async def get_the_timezone(city) -> str:
    return f"Time in {city} is {datetime.now()}"

@server.prompt
def explain_topic(topic: str, language: str) -> str:
    return f"Can you explain {topic} in {language}?"

@server.resource("resource://welcome-message")
def get_resource() -> str:
    return "This is a welcoming resource"


class MCPClient(Client):

    def __init__(self, user_id):

        # TODO: get tokens / api keys from DB
        super().__init__(
            transport=StreamableHttpTransport(url="http://localhost:8000/mcp")
        )

        self.cached_tools = None
        self.cached_resources = None
        self.cached_prompts = None
        # TODO: invalidate caches when MCP server notifies (should keep open connection)

    async def list_tools(self):
        if self.cached_tools:
            return self.cached_tools
        async with self:
            tools = await super().list_tools()
        
        self.cached_tools = tools
        return tools


class MCPClients():

    def __init__(self):
        self.clients = TTLCache(maxsize=100, ttl=60*10)
    
    def __getitem__(self, user_id):
        if user_id not in self.clients:
            self.clients[user_id] = MCPClient(user_id)
        return self.clients[user_id]
