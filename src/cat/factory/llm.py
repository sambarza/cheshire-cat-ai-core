

from typing import Type
from pydantic import BaseModel, ConfigDict

from cat.mad_hatter.mad_hatter import MadHatter
from cat.factory.defaults import LLMDefault


# Base class to manage LLM configuration.
class LLMSettings(BaseModel):
    # class instantiating the model
    _pyclass: Type | None = None

    # This is related to pydantic, because "model_*" attributes are protected.
    # We deactivate the protection because langchain relies on several "model_*" named attributes
    model_config = ConfigDict(protected_namespaces=())

    # instantiate an LLM from configuration
    @classmethod
    def get_llm_from_config(cls, config):
        if cls._pyclass is None:
            raise Exception(
                "Language model configuration class has self._pyclass==None. Should be a valid LLM class"
            )
        return cls._pyclass.default(**config)


class LLMDefaultConfig(LLMSettings):
    _pyclass: Type = LLMDefault

    model_config = ConfigDict(
        json_schema_extra={
            "humanReadableName": "Default Language Model",
            "description": "A dumb LLM just telling that the Cat is not configured. "
            "There will be a nice LLM here once consumer hardware allows it.",
            "link": "",
        }
    )


def get_allowed_language_models():
    mad_hatter = MadHatter()
    list_llms_default = [ LLMDefaultConfig ]
    return mad_hatter.execute_hook(
        "factory_allowed_llms", list_llms_default, cat=None
    )

def get_llm_from_name(name_llm: str):
    """Find the llm adapter class by name"""
    for cls in get_allowed_language_models():
        if cls.__name__ == name_llm:
            return cls
    return None


def get_llms_schemas():
    # LLM_SCHEMAS contains metadata to let any client know
    # which fields are required to create the language model.
    LLM_SCHEMAS = {}
    for config_class in get_allowed_language_models():
        schema = config_class.model_json_schema()
        # useful for clients in order to call the correct config endpoints
        schema["languageModelName"] = schema["title"]
        LLM_SCHEMAS[schema["title"]] = schema

    return LLM_SCHEMAS
