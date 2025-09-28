from typing import Any, Dict
from cat.factory.defaults import (
    AuthHandlerDefault, LLMDefault, EmbedderDefault, AgentDefault
)
from cat.utils import BaseModelDict


class FactoryCategory(BaseModelDict):
    default: Any
    objects: Dict[str, Any] = {}


class Factory:

    def __init__(self):

        self.categories = {
            "auth_handler" : FactoryCategory(
                default = AuthHandlerDefault()
            ),
            "llm" : FactoryCategory(
                default = LLMDefault()
            ),
            "embedder" : FactoryCategory(
                default = EmbedderDefault()
            ),
            "agent" : FactoryCategory(
                default = AgentDefault()
            ),
        }

    async def load_objects(self, mad_hatter):
        """Collect objects instantiated by plugins (llms, embedders, auth handlers, agents)."""

        for category_name, category in self.categories.items():
            category.objects = mad_hatter.execute_hook(
                f"factory_allowed_{category_name}s", {}, cat=None
            )
            # TODO: should add type checks

            if len(category.objects) == 0:
                category.objects = {
                    "default": category.default
                }

    def get_objects(self, category_name: str):
        return self.categories[category_name].objects

    def get_default(self, category_name: str):
        return self.categories[category_name].default


