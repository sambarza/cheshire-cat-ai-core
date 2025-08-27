# Helper classes for connection handling
# Credential extraction from ws / http connections is not delegated to the custom auth handlers,
#  to have a standard auth interface.

from abc import ABC, abstractmethod
from typing import AsyncGenerator
from urllib.parse import urlencode

from fastapi import (
    Request,
    WebSocket,
    HTTPException,
    WebSocketException,
    Depends
)
from fastapi.requests import HTTPConnection
from fastapi.security.oauth2 import OAuth2PasswordBearer

from cat.auth.permissions import (
    AuthPermission,
    AuthResource,
    AuthUserInfo,
)
from cat.looking_glass.stray_cat import StrayCat


class BaseAuth(ABC):

    def __init__(
            self,
            resource: AuthResource | str,
            permission: AuthPermission | str,
        ):

        self.resource = resource
        self.permission = permission

    @abstractmethod
    async def __call__(self, *args, **kwargs) -> AsyncGenerator[StrayCat, None]:
        pass

    @abstractmethod
    def not_allowed(self, connection: HTTPConnection):
        pass

    async def authorize(
        self,
        connection: HTTPConnection,
        credential: str | None,
        user_id: str | None
    ) -> AsyncGenerator[StrayCat | None, None]:
        
        # get protocol from Starlette request
        protocol = connection.scope.get('type')
        
        auth_handlers = [
            # try to get user from auth_handler
            connection.app.state.ccat.custom_auth_handler,
            # try to get user from local idp
            connection.app.state.ccat.core_auth_handler,
        ]
        for ah in auth_handlers:
            user: AuthUserInfo = ah.authorize_user_from_credential(
                protocol, credential, self.resource, self.permission, user_id
            )
            if user:
                # create new StrayCat
                cat = StrayCat(user)
                
                # StrayCat is passed to the endpoint
                yield cat

                # save working memory and delete StrayCat after endpoint execution
                cat.update_working_memory_cache()
                del cat
                return

        # if no StrayCat was obtained, raise exception
        self.not_allowed(connection)

# necessary for login in the swagger, only http
bearer_extractor = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    refreshUrl=None,
    auto_error=False
)

class HTTPAuth(BaseAuth):

    async def __call__(
        self,
        connection: Request,
        credential = Depends(bearer_extractor), # this mess for the damn swagger
    ) -> AsyncGenerator[StrayCat | None, None]:
        
        # and that's why I hate async stuff
        async for stray in self.authorize(
            connection,
            credential,
            connection.headers.get("user_id")
        ):
            yield stray

    def not_allowed(self, connection: Request):
        raise HTTPException(status_code=403, detail={"error": "Invalid Credentials"})
        

class WebsocketAuth(BaseAuth):

    async def __call__(
        self,
        connection: WebSocket,
    ) -> AsyncGenerator[StrayCat | None, None]:
        
        async for stray in self.authorize(
            connection,
            connection.query_params.get("token"),
            connection.path_params.get("user_id")
        ):
            yield stray
        
    def not_allowed(self, connection: WebSocket):
        raise WebSocketException(code=1004, reason="Invalid Credentials")

    
# TODOV2: get rid of this
class CoreFrontendAuth(BaseAuth):

    async def __call__(
        self,
        connection: Request,
    ) -> AsyncGenerator[StrayCat | None, None]:
        
        async for stray in self.authorize(
            connection,
            connection.cookies.get("ccat_user_token"),
            connection.path_params.get("user_id")
        ):
            yield stray
    
    def not_allowed(self, connection: Request):
        referer_query = urlencode({"referer": connection.url.path})
        raise HTTPException(
            status_code=307,
            headers={
                "Location": f"/auth/login?{referer_query}"
            }
        )