from cachetools import TTLCache
from fastmcp.client import Client

from cat.log import log


class MCPClient(Client):
    """Cat MCP client is scoped by user_id and does not keep a live connection to servers.
        We use caches waiting for the protocol to become stateless.
    """

    def __init__(self, user_id):

        # TODO: get addresses / tokens / api keys from DB
        config = {
            "mcpServers": {
                "my": {
                    "url": "http://localhost:8000/mcp"
                },
                "my2": {
                    "url": "http://localhost:8001/mcp"
                }
            }
        }

        super().__init__(config)

        self.cached_tools = None
        self.cached_resources = None
        self.cached_prompts = None
        # TODO: invalidate caches? when MCP server notifies

    async def list_tools(self):
        if self.cached_tools:
            return self.cached_tools
        
        try:
            async with self:
                tools = await super().list_tools()
        except Exception:
            log.error(f"Error during MCP client init")
            return []
        
        self.cached_tools = tools
        log.warning(self.cached_tools)
        return tools


class MCPClients():
    """Keep a cache of user scoped MCP clients"""

    def __init__(self):
        self.clients = TTLCache(maxsize=1000, ttl=60*10)
    
    def __getitem__(self, user_id):
        if user_id not in self.clients:
            self.clients[user_id] = MCPClient(user_id)
        return self.clients[user_id]