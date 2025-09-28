import sys
from uuid import uuid4

from cat.db.models import SettingDB
from cat.factory.factory import Factory
from cat.protocols.model_context.client import MCPClients
from cat.log import log
from cat.mad_hatter.mad_hatter import MadHatter


class CheshireCat:
    """The Cheshire Cat.

    This is the main class that manages the whole AI application.
    It contains references to all the main modules and is responsible for the bootstrapping of the application.

    In most cases you will not need to interact with this class directly, but rather with class `StrayCat` which will be available in your plugin's hooks, tools and endpoints.

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

            # ensure core DB settings
            await self.populate_db()

            # instantiate MadHatter and trigger first discovery
            self.mad_hatter = MadHatter()
            await self.mad_hatter.find_plugins()

            # init Factory
            self.factory = Factory(self.mad_hatter)

            # init MCP client(s)
            self.mcp_clients = MCPClients()

            # allows plugins to do something before cat components are loaded
            self.mad_hatter.execute_hook("before_cat_bootstrap", cat=self)

            # load AuthHandlers
            self.auth_handlers = await self.factory.load_objects("auth_handler")

            # load LLM and embedder
            self.llms = await self.factory.load_objects("llm")
            self.embedders = await self.factory.load_objects("embedder")
            
            # load Agents
            self.agents = await self.factory.load_objects("agent")

            # allows plugins to do something after the cat bootstrap is complete
            self.mad_hatter.execute_hook("after_cat_bootstrap", cat=self)
        except Exception:
            log.error("Error during CheshireCat bootstrap. Exiting.")
            sys.exit()

    async def populate_db(self):
        """Force minimal settings into core DB."""

        initial_settings = {
            "active_plugins": [],
            "installation_id": [str(uuid4())],
        }

        for name, value in initial_settings.items():
            setting = await SettingDB.get_or_none(name=name)
            if setting is None:
                setting = SettingDB(name=name, value=value)
                await setting.save()
    
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


