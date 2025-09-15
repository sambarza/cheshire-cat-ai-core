
from typing import Type

from cat.mad_hatter.mad_hatter import MadHatter
from cat.factory.defaults import (
    AuthHandlerDefault, LLMDefault, EmbedderDefault, AgentDefault
)


# this class so slim can easily be methods in CheshireCat
class Factory:

    def __init__(self, mad_hatter):
        self.mad_hatter = mad_hatter

    category_defaults = {
        "auth_handler" : AuthHandlerDefault(),
        "llm"          : LLMDefault(),
        "embedder"     : EmbedderDefault(),
        "agent"        : AgentDefault(),
    }


    async def load_objects(self, category: str):
        """Collect objects instantiated by plugins (llms, embedders, auth handlers)."""

        if category not in self.category_defaults.keys():
            raise Exception(f"Category '{category}' is not supported by Factory")

        objects_dict = self.mad_hatter_instance.execute_hook(
            f"factory_allowed_{category}s", {}, cat=None
        )
        if len(objects_dict) == 0:
            objects_dict = {
                "default": self.category_defaults[category]
            }
            
        return objects_dict
    

    def get_default(self, category: str):
        if category not in self.category_defaults.keys():
            raise Exception(f"Category '{category}' is not supported by Factory")
        return self.category_defaults[category]


