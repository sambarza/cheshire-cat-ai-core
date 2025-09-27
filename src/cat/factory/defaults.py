
import jwt
from uuid import uuid5, NAMESPACE_DNS

from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.embeddings import FakeEmbeddings

from cat.env import get_env
from cat.log import log
from cat.types.messages import Message
from cat.auth.base_auth_handler import BaseAuthHandler
from cat.auth.permissions import (
    AuthUserInfo, AuthPermission, AuthResource, get_full_permissions
)


class LLMDefault(SimpleChatModel):
    """Defaul LLM, replying a constant string. Used before a proper one is added."""

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
    """Defaul embedder, spits out random vectors. Used before a proper one is added."""

    def __init__(self, *args, **kwargs):
        kwargs["size"] = 128
        super().__init__(*args, **kwargs)


class AuthHandlerDefault(BaseAuthHandler):
    """Defaul auth handler, based on environment variables."""

    def authorize_user_from_jwt(
        self,
        token: str,
        auth_resource: AuthResource,
        auth_permission: AuthPermission
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
        # if nothing is returned, request shall not pass

    def authorize_user_from_key(
            self,
            key: str,
            auth_resource: AuthResource,
            auth_permission: AuthPermission,
    ) -> AuthUserInfo | None: 
        
        ########## tmp #######
        return AuthUserInfo(
                id=str(uuid5(NAMESPACE_DNS, "admin")),
                name="admin",
                permissions=get_full_permissions()
            )
        ######################

        # allow access with full permissions
        if key == get_env("CCAT_API_KEY"):
            username = get_env("CCAT_ADMIN_CREDENTIALS").split(":")[0]
            return AuthUserInfo(
                id=str(uuid5(NAMESPACE_DNS, username)),
                name=username,
                permissions=get_full_permissions()
            )
        # if nothing is returned, request shall not pass
    

class AgentDefault:

    async def execute(self, cat):

        for i in range(6): # TODOV2: not sure
            llm_mex: Message = await cat.llm(
                # delegate prompt construction to plugins
                await cat.get_system_prompt(),
                # pass conversation messages
                messages=cat.chat_request.messages + cat.chat_response.messages,
                # pass tools (both internal and MCP)
                tools=await cat.list_tools(),
                # whether to stream or not
                stream=cat.chat_request.stream,
                # give a name to LLM execution for logging purposes
                # TODOV2: log should be done via langchain handlers
                execution_name="DEFAULT AGENT"
            )

            cat.chat_response.messages.append(llm_mex)
            
            if len(llm_mex.tool_calls) == 0:
                # No tool calls, exit
                return
            else:
                # LLM has chosen to use tools, run them
                # TODOV2: tools may require explicit user permission
                # TODOV2: tools may return an artifact, resource or elicitation
                for tool_call in llm_mex.tool_calls:
                    # actually executing the tool
                    tool_message = await cat.call_tool(tool_call)
                    # append tool request and tool output messages
                    cat.chat_response.messages.append(tool_message)

                    # if t.return_direct: TODO recover return_direct