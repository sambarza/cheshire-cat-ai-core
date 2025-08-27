
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import FakeEmbeddings

from cat.factory.base import BaseAuthHandler
from cat.auth.permissions import AuthUserInfo


class LLMDefault(BaseChatModel):
    @property
    def _llm_type(self):
        return ""

    def _call(self, *args, **kwargs):
        return "You did not configure a Language Model. Do it in the settings!"

    async def _acall(self, *args, **kwargs):
        return "You did not configure a Language Model. Do it in the settings!"
    

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