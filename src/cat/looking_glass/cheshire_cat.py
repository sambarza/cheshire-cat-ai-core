from typing import List, Dict
from typing_extensions import Protocol

from cat.factory.auth_handler import get_auth_handler_from_name
import cat.factory.auth_handler as auth_handlers
from cat.db import crud, models
from cat.protocols.model_context.client import MCPClient, mcp_servers_config
from cat.factory.llm import LLMDefaultConfig, get_llm_from_name
from cat.factory.embedder import EmbedderDefaultConfig, get_embedder_from_name
from cat.memory.long_term_memory import LongTermMemory
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
        Yet to be written.

    """

    # will be called at first instantiation in fastapi lifespan
    def bootstrap(self, fastapi_app):
        """Cat initialization.

        At init time the Cat executes the bootstrap, loading all main componetns and components added by plugins.
        """

        # bootstrap the Cat! ^._.^

        self.fastapi_app = fastapi_app # reference to the FastAPI object

        # init MCP client
        # not sure this is better here or as a wide availbel singleton (like the db)
        self.mcp = MCPClient(mcp_servers_config)

        # long term memory
        self.load_memory()

        # load AuthHandler
        self.load_auth()
        
        # instantiate MadHatter (loads all plugins' hooks and tools)
        self.load_mad_hatter()

        # allows plugins to do something before cat components are loaded
        self.mad_hatter.execute_hook("before_cat_bootstrap", cat=self)

        # load LLM and embedder
        self.load_natural_language()

        # Cache for sessions / working memories et al.
        self.cache = CacheManager().cache

        # allows plugins to do something after the cat bootstrap is complete
        self.mad_hatter.execute_hook("after_cat_bootstrap", cat=self)

    def load_mad_hatter(self):
        self.mad_hatter = MadHatter()
        # TODOV2: get rid of this on_finish callback somehow
        self.mad_hatter.on_finish_plugins_sync_callback = self.on_finish_plugins_sync_callback
        self.on_finish_plugins_sync_callback() # only for the first time called manually

    def load_memory(self):
            # TODOV2: LTM should run hooks and should subscribe to embedder and mad_hatter hooks
            self.memory = LongTermMemory()

    def load_natural_language(self):
        """Load Natural Language related objects.

        The method exposes in the Cat all the NLP related stuff. Specifically, it sets the language models
        (LLM and Embedder).

        Warnings
        --------
        When using small Language Models it is suggested to turn off the memories and make the main prompt smaller
        to prevent them to fail.

        See Also
        --------
        agent_prompt_prefix
        """
        # LLM and embedder
        self._llm = self.load_language_model()
        self.embedder = self.load_language_embedder()

    def load_language_model(self):
        """Large Language Model (LLM) selection at bootstrap time.

        Returns
        -------
        llm : BaseLanguageModel
            Langchain `BaseLanguageModel` instance of the selected model.

        Notes
        -----
        Bootstrapping is the process of loading the main Cat components and plugins.
        """
        
        selected_llm = crud.get_setting_by_name(name="llm_selected")

        if selected_llm is None:
            # Return default LLM
            # TODOV2: set it with default in the db (also other factories)
            #           so the endpoint gives always a configuration available
            return LLMDefaultConfig.get_llm_from_config({})

        # Get LLM factory class
        selected_llm_class = selected_llm["value"]["name"]
        FactoryClass = get_llm_from_name(selected_llm_class)
        # TODOV2: lowercase both class

        # Obtain configuration and instantiate LLM
        selected_llm_config = crud.get_setting_by_name(name=selected_llm_class)
        try:
            llm = FactoryClass.get_llm_from_config(selected_llm_config["value"])
            return llm
        except Exception:
            log.error("Error during LLM instantiation")
            return LLMDefaultConfig.get_llm_from_config({})

    def load_language_embedder(self):
        """Hook into the  embedder selection.

        Allows to modify how the Cat selects the embedder at bootstrap time.

        Parameters
        ----------
        cat: CheshireCat
            Cheshire Cat instance.

        Returns
        -------
        embedder : Embeddings
            Selected embedder model.
        """
        # Embedding LLM

        selected_embedder = crud.get_setting_by_name(name="embedder_selected")

        if selected_embedder is None:
            # return default embedder
            return EmbedderDefaultConfig.get_embedder_from_config({})

        # Get Embedder factory class
        selected_embedder_class = selected_embedder["value"]["name"]
        FactoryClass = get_embedder_from_name(selected_embedder_class)

        # obtain configuration and instantiate Embedder
        selected_embedder_config = crud.get_setting_by_name(
            name=selected_embedder_class
        )

        try:
            embedder = FactoryClass.get_embedder_from_config(
                selected_embedder_config["value"]
            )
        except Exception:
            log.error("Error during Embedder instantiation")
            return EmbedderDefaultConfig.get_embedder_from_config({})
        return embedder

    def load_auth(self):

        # Custom auth_handler # TODOAUTH: change the name to custom_auth
        selected_auth_handler = crud.get_setting_by_name(name="auth_handler_selected")

        # if no auth_handler is saved, use default one and save to db
        if selected_auth_handler is None:
            # create the auth settings
            crud.upsert_setting_by_name(
                models.Setting(
                    name="CoreOnlyAuthConfig", category="auth_handler_factory", value={}
                )
            )
            crud.upsert_setting_by_name(
                models.Setting(
                    name="auth_handler_selected",
                    category="auth_handler_factory",
                    value={"name": "CoreOnlyAuthConfig"},
                )
            )

            # reload from db
            selected_auth_handler = crud.get_setting_by_name(
                name="auth_handler_selected"
            )

        # get AuthHandler factory class
        selected_auth_handler_class = selected_auth_handler["value"]["name"]
        FactoryClass = get_auth_handler_from_name(selected_auth_handler_class)

        # obtain configuration and instantiate AuthHandler
        selected_auth_handler_config = crud.get_setting_by_name(
            name=selected_auth_handler_class
        )
        try:
            auth_handler = FactoryClass.get_auth_handler_from_config(
                selected_auth_handler_config["value"]
            )
        except Exception:
            log.error("Error during AuthHandler instantiation")

            auth_handler = (
                auth_handlers.AuthHandlerDefaultConfig.get_auth_handler_from_config({})
            )

        self.auth_handler = auth_handler


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


