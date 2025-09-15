import sys

from typing import List, Dict
from typing_extensions import Protocol

from cat.db.database import engine
from cat.db.models import Base
from cat.factory.factory import Factory
from cat.protocols.model_context.client import MCPClient, mcp_servers_config
from cat.log import log
from cat.mad_hatter.mad_hatter import MadHatter
from cat.cache.cache_manager import CacheManager


class Procedure(Protocol):
    name: str
    procedure_type: str  # "tool" or "form"

    # {
    #   "description": [],
    #   "start_examples": [],
    # }
    triggers_map: Dict[str, List[str]]


# main class
class CheshireCat:
    """The Cheshire Cat.

    This is the main class that manages the whole AI application.
    It contains references to all the main modules and is responsible for the bootstrapping of the application.

    In most cases you will not need to interact with this class directly, but rather with class `StrayCat` which will be available in your plugin's hooks, tools, forms end endpoints.

    Attributes
    ----------
    todo : list
        Help needed TODO
    """

    # will be called at first instantiation in fastapi lifespan
    async def bootstrap(self, fastapi_app):
        """Cat initialization.

        At init time the Cat executes the bootstrap, loading all main components and components added by plugins.
        """

        # bootstrap the Cat! ^._.^

        try:
            self.fastapi_app = fastapi_app # reference to the FastAPI object

            # init core DB
            async def init_db():
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

            # instantiate MadHatter (loads all plugins' hooks and tools) and trigger first discovery
            self.mad_hatter = MadHatter()
            await self.mad_hatter.find_plugins()

            # init Factory
            self.factory = Factory(self.mad_hatter)

            # init MCP client
            self.mcp = MCPClient(mcp_servers_config)

            # allows plugins to do something before cat components are loaded
            self.mad_hatter.execute_hook("before_cat_bootstrap", cat=self)

            # load AuthHandlers
            self.auth_handlers = await self.factory.load_objects("auth_handler")

            # load LLM and embedder
            self.llms = await self.factory.load_objects("llm")
            self.embedders = await self.factory.load_objects("embedder")
            
            # load Agents
            self.agents = await self.factory.load_objects("agent")

            # Cache for sessions / working memories et al.
            self.cache = CacheManager().cache

            # allows plugins to do something after the cat bootstrap is complete
            self.mad_hatter.execute_hook("after_cat_bootstrap", cat=self)
        except Exception:
            log.error("Error during CheshireCat bootstrap. Exiting.")
            sys.exit()

    
    async def execute_agent(self, slug, cat):
        """Execute an agent from its slug."""

        # prepare input to be passed to the agent.
        #   Info will be extracted from working memory
        # Note: agent_input works both as a dict and as an object
        # TODOV2: hook before_agent_starts is not active anymore
        #self.mad_hatter.execute_hook(
        #    "before_agent_starts", cat=cat
        #)

        # should we run the agent?
        # TODOV2: hook agent_fast_reply is not active anymore
        #agent_fast_reply = self.mad_hatter.execute_hook(
        #]    "agent_fast_reply", {}, cat=cat
        #)

        if slug not in self.agents.keys():
            log.warning(f"Agent {slug} not found. Running default agent")
            selected_agent = self.factory.get_default("agent")
        else:
            selected_agent = self.agents[slug]

        await selected_agent.execute(cat)


