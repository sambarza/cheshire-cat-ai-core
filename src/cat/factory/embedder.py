from typing import Type
from pydantic import ConfigDict

from cat.factory.defaults import BaseSettings, EmbedderDefault


class EmbedderSettings(BaseSettings):
    """Extend this class for custom Embedder settings."""
    pass


class EmbedderDefaultConfig(EmbedderSettings):
    _pyclass: Type = EmbedderDefault

    model_config = ConfigDict(
        json_schema_extra={
            "humanReadableName": "Test Embedder",
            "description": "Default embedder. It just outputs random numbers.",
            "link": "",
        }
    )