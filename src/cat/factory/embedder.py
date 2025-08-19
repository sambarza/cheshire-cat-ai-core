from typing import Type, List
from pydantic import BaseModel, ConfigDict

from cat.mad_hatter.mad_hatter import MadHatter
from cat.factory.defaults import EmbedderDefault


# Base class to manage LLM configuration.
class EmbedderSettings(BaseModel):
    # class instantiating the embedder
    _pyclass: Type | None = None

    # This is related to pydantic, because "model_*" attributes are protected.
    # We deactivate the protection because langchain relies on several "model_*" named attributes
    model_config = ConfigDict(protected_namespaces=())

    # instantiate an Embedder from configuration
    @classmethod
    def get_embedder_from_config(cls, config):
        if cls._pyclass is None:
            raise Exception(
                "Embedder configuration class has self._pyclass==None. Should be a valid Embedder class"
            )
        return cls._pyclass.default(**config)


class EmbedderDefaultConfig(EmbedderSettings):
    size: int = 128
    _pyclass: Type = EmbedderDefault

    model_config = ConfigDict(
        json_schema_extra={
            "humanReadableName": "Test Embedder",
            "description": "Default embedder. It just outputs random numbers.",
            "link": "",
        }
    )


def get_allowed_embedder_models() -> List[EmbedderSettings]:
    mad_hatter_instance = MadHatter()
    list_embedder_default = [ EmbedderDefaultConfig ]
    return mad_hatter_instance.execute_hook(
        "factory_allowed_embedders", list_embedder_default, cat=None
    )


def get_embedder_from_name(name_embedder: str):
    """Find the llm adapter class by name"""
    for cls in get_allowed_embedder_models():
        if cls.__name__ == name_embedder:
            return cls
    return None


def get_embedders_schemas():
    # EMBEDDER_SCHEMAS contains metadata to let any client know which fields are required to create the language embedder.
    EMBEDDER_SCHEMAS = {}
    for config_class in get_allowed_embedder_models():
        schema = config_class.model_json_schema()
        # useful for clients in order to call the correct config endpoints
        schema["languageEmbedderName"] = schema["title"]
        EMBEDDER_SCHEMAS[schema["title"]] = schema

    return EMBEDDER_SCHEMAS
