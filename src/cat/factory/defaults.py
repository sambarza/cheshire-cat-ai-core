
import jwt
from typing import Type, Literal

from pydantic import BaseModel, ConfigDict

from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.embeddings import FakeEmbeddings
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from cat.env import get_env
from cat.log import log
from cat.auth.base_auth_handler import BaseAuthHandler
from cat.auth.permissions import (
    AuthUserInfo, AuthPermission, AuthResource, get_full_permissions
)


class BaseSettings(BaseModel):
    _pyclass: Type[BaseAuthHandler]

    # This is related to pydantic, because "model_*" attributes are protected.
    # We deactivate the protection because langchain relies on several "model_*" named attributes
    model_config = ConfigDict(protected_namespaces=())

    @classmethod
    def get_object_from_config(cls, config):
        if cls._pyclass is None:
            raise Exception(
                "Configuration class has self._pyclass==None."
            )
        return cls._pyclass.default(**config)


class LLMDefault(SimpleChatModel):
    @property
    def _llm_type(self):
        return ""

    def _call(self, *args, **kwargs):
        return "You did not configure a Language Model. Do it in the settings!"

    async def _acall(self, *args, **kwargs):
        return "You did not configure a Language Model. Do it in the settings!"
    
    def bind_tools(self, *args, **kwargs):
        return self
    

class EmbedderDefault(FakeEmbeddings):
    def __init__(self, *args, **kwargs):
        kwargs["size"] = 128
        super().__init__(*args, **kwargs)


class AuthHandlerDefault(BaseAuthHandler):
        
    def authorize_user_from_jwt(
        self, token: str, auth_resource: AuthResource, auth_permission: AuthPermission
    ) -> AuthUserInfo | None:
        try:
            # decode token
            payload = jwt.decode(
                token,
                get_env("CCAT_JWT_SECRET"),
                algorithms=[get_env("CCAT_JWT_ALGORITHM")],
            )

            return AuthUserInfo(
                id=payload["sub"],
                name=payload["username"],
                permissions=get_full_permissions()
            )

        except Exception:
            log.warning("Could not auth user from JWT")

        # do not pass
        return None

    def authorize_user_from_key(
            self,
            protocol: Literal["http", "websocket"],
            user_id: str,
            api_key: str,
            auth_resource: AuthResource,
            auth_permission: AuthPermission,
    ) -> AuthUserInfo | None: 

        # allow access with full permissions
        if api_key == get_env("CCAT_API_KEY"):
            return AuthUserInfo(
                id=user_id,
                name=user_id,
                permissions=get_full_permissions()
            )

        # No match -> deny access
        return None