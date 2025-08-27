from typing import Type
from pydantic import BaseModel, ConfigDict

from cat.mad_hatter.mad_hatter import MadHatter
from cat.factory.defaults import AuthHandlerDefault, BaseAuthHandler


class AuthHandlerSettings(BaseModel):
    _pyclass: Type[BaseAuthHandler] = None

    @classmethod
    def get_auth_handler_from_config(cls, config):
        if (
            cls._pyclass is None
            or issubclass(cls._pyclass.default, BaseAuthHandler) is False
        ):
            raise Exception(
                "AuthHandler configuration class has self._pyclass==None. Should be a valid AuthHandler class"
            )
        return cls._pyclass.default(**config)


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


def get_allowed_auth_handler_strategies():
    list_auth_handler_default = [
        AuthHandlerDefault
    ]

    mad_hatter_instance = MadHatter()
    list_auth_handler = mad_hatter_instance.execute_hook(
        "factory_allowed_auth_handlers", list_auth_handler_default, cat=None
    )

    return list_auth_handler


def get_auth_handlers_schemas():
    AUTH_HANDLER_SCHEMAS = {}
    for config_class in get_allowed_auth_handler_strategies():
        schema = config_class.model_json_schema()
        schema["auhrizatorName"] = schema["title"]
        AUTH_HANDLER_SCHEMAS[schema["title"]] = schema

    return AUTH_HANDLER_SCHEMAS


def get_auth_handler_from_name(name):
    list_auth_handler = get_allowed_auth_handler_strategies()
    for auth_handler in list_auth_handler:
        if auth_handler.__name__ == name:
            return auth_handler
    return None
