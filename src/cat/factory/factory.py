
from typing import Type

from cat.mad_hatter.mad_hatter import MadHatter
from cat.db import crud
from cat.log import log
from cat.factory.auth_handler import AuthHandlerDefaultConfig
from cat.factory.llm import LLMDefaultConfig
from cat.factory.embedder import EmbedderDefaultConfig


class Factory:

    slug_defaults = {
        "auth_handler" : AuthHandlerDefaultConfig,
        "llm"          : LLMDefaultConfig,
        "embedder"     : EmbedderDefaultConfig
    }


    async def instantiate_object_from_slug(
            self,
            slug: str
    ):
        """Instantiate actual object from the config/settings class name.
        The flow is:
            -> string "ConfigClass"
            -> actual class ConfigClass and config data stored in DB
            -> actual Class to instantiate taken from ConfigClass._pyclass (points to final class)
            -> object derived from ConfigClass._pyclass(config)
        """

        if slug not in self.slug_defaults.keys():
            raise Exception(f"Slug: '{slug}' is not supported by the Factory")

        # Get config for this class from DB
        config_class_name = crud.get_setting_by_name(name=f"{slug}_selected")
        config_class_name = config_class_name["value"]["name"]
        config = crud.get_setting_by_name(name=config_class_name)
        config = config["value"]

        # Get the actual Config class
        ConfigClass: Type = await self.get_config_class(slug, config_class_name)
        
        # Instantiate final configured object
        try:
            obj = ConfigClass.get_object_from_config(config)
        except Exception:
            raise Exception(f"Error during factory {ConfigClass._pyclass} instantiation")

        return obj
    

    async def get_allowed_setting_classes(self, slug):

        mad_hatter_instance = MadHatter()
        classes_list = [
            self.slug_defaults[slug]
        ]
        classes_list = mad_hatter_instance.execute_hook(
            f"factory_allowed_{slug}s", classes_list, cat=None
        )
        return classes_list


    async def get_schemas(self, slug):
        schemas = {}
        for config_class in await self.get_allowed_setting_classes(slug):
            schema = config_class.model_json_schema()
            schema["auhrizatorName"] = schema["title"]
            schemas[schema["title"]] = schema

        return schemas


    async def get_config_class(self, slug, class_name) -> Type | None:
        classes = await self.get_allowed_setting_classes(slug)
        for c in classes:
            if c.__name__ == class_name:
                return c
        return None


