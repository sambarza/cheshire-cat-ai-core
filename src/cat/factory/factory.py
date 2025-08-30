
from typing import Type

from cat.mad_hatter.mad_hatter import MadHatter
from cat.db import crud
from cat.log import log
from cat.factory.defaults import (
    AuthHandlerDefault, LLMDefault, EmbedderDefault
)


class Factory:

    category_defaults = {
        "auth_handler" : AuthHandlerDefault(),
        "llm"          : LLMDefault(),
        "embedder"     : EmbedderDefault()
    }


    async def load_objects(self, category: str):
        """Collect objects instantiated by plugins (llms, embedders, auth handlers)."""

        if category not in self.category_defaults.keys():
            raise Exception(f"Category '{category}' is not supported by Factory")

        mad_hatter_instance = MadHatter()
        objects_dict = mad_hatter_instance.execute_hook(
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


