from typing import Type
from pydantic import ConfigDict

from cat.factory.defaults import BaseSettings, LLMDefault


class LLMSettings(BaseSettings):
    """Extend this class for custom LLM settings."""
    pass


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
