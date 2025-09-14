import sys

from typing import List, Dict
from typing_extensions import Protocol

from cat.factory.factory import Factory
from cat.protocols.model_context.client import MCPClient, mcp_servers_config
from cat.log import log
from cat.mad_hatter.mad_hatter import MadHatter
from cat.utils import singleton
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
@singleton
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

            # instantiate MadHatter (loads all plugins' hooks and tools)
            self.load_mad_hatter()

            # init Factory
            self.factory = Factory()

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


    def load_mad_hatter(self):
        self.mad_hatter = MadHatter()
        # TODOV2: get rid of this on_finish callback somehow
        self.mad_hatter.on_finish_plugins_sync_callback = self.on_finish_plugins_sync_callback
        self.on_finish_plugins_sync_callback() # only for the first time called manually

    
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


    def build_embedded_procedures_hashes(self, embedded_procedures):
        hashes = {}
        for ep in embedded_procedures:
            metadata = ep.payload["metadata"]
            content = ep.payload["page_content"]
            source = metadata["source"]
            # there may be legacy points with no trigger_type
            trigger_type = metadata.get("trigger_type", "unsupported")

            p_hash = f"{source}.{trigger_type}.{content}"
            hashes[p_hash] = ep.id

        return hashes

    def build_active_procedures_hashes(self, active_procedures):
        hashes = {}
        for ap in active_procedures:
            for trigger_type, trigger_list in ap.triggers_map.items():
                for trigger_content in trigger_list:
                    p_hash = f"{ap.name}.{trigger_type}.{trigger_content}"
                    hashes[p_hash] = {
                        "obj": ap,
                        "source": ap.name,
                        "type": ap.procedure_type,
                        "trigger_type": trigger_type,
                        "content": trigger_content,
                    }
        return hashes

    def on_finish_plugins_sync_callback(self):
        self.activate_endpoints()
        #self.embed_procedures() # TODOV2: the whole on_finish function should not exist

    def activate_endpoints(self):
        for endpoint in self.mad_hatter.endpoints:
            if endpoint.plugin_id in self.mad_hatter.get_active_plugins():
                endpoint.activate(self.fastapi_app)


