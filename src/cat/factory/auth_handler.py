from typing import Type
from pydantic import ConfigDict


from cat.factory.defaults import BaseSettings, AuthHandlerDefault


class AuthHandlerSettings(BaseSettings):
    """Extend this class for custom AuthHandler settings."""
    pass


class AuthHandlerDefaultConfig(AuthHandlerSettings):

    _pyclass: Type = AuthHandlerDefault

    model_config = ConfigDict(
        json_schema_extra={
            "humanReadableName": "Default Auth Handler",
            "description": "Auth based on environment variables."
            "Set CCAT_ADMIN_CREDENTIALS and CCAT_API_KEY in your .env to change them.",
            "link": "",  # TODO link to auth docs
        }
    )