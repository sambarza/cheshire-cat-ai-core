# Helper classes for connection handling
# Credential extraction from ws / http connections is not delegated to the custom auth handlers,
#  to have a standard auth interface.

from abc import ABC, abstractmethod
from typing import Tuple, AsyncGenerator
from urllib.parse import urlencode

from fastapi import (
    Request,
    WebSocket,
    HTTPException,
    WebSocketException,
)
from fastapi.requests import HTTPConnection

from cat.auth.permissions import (
    AuthPermission,
    AuthResource,
    AuthUserInfo,
)
from cat.looking_glass.stray_cat import StrayCat
from cat.log import log


class BaseAuth(ABC):

    def __init__(
            self,
            resource: AuthResource | str,
            permission: AuthPermission | str
        ):
        
        self.resource = resource
        self.permission = permission

    async def __call__(
        self,
        connection: HTTPConnection # Request | WebSocket,
    ) -> AsyncGenerator[StrayCat, None]:

        # get protocol from Starlette request
        protocol = connection.scope.get('type')
        # extract credentials (user_id, token_or_key) from connection
        user_id, credential = self.extract_credentials(connection)
        auth_handlers = [
            # try to get user from auth_handler
            connection.app.state.ccat.custom_auth_handler,
            # try to get user from local idp
            connection.app.state.ccat.core_auth_handler,
        ]
        for ah in auth_handlers:
            user: AuthUserInfo = ah.authorize_user_from_credential(
                protocol, credential, self.resource, self.permission, user_id=user_id
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

    @abstractmethod
    def extract_credentials(self, connection: Request | WebSocket) -> Tuple[str] | Tuple[None]:
        pass

    @abstractmethod
    def not_allowed(self, connection: Request | WebSocket):
        pass
        

class Auth(BaseAuth):

    def extract_credentials(self, connection: Request | WebSocket) -> Tuple[str] | Tuple[None]:
        """
        Extract user_id and token/key from headers
        """

        if isinstance(connection, WebSocket):
            user_id = connection.path_params.get("user_id", "user")
            token = connection.query_params.get("token", None)

        elif isinstance(connection, Request):
            user_id = connection.headers.get("user_id", "user")
            token = connection.headers.get("Authorization", None)
            if token:
                if "Bearer " in token:
                    token = token.replace("Bearer ", "")
                else:
                    token = None
        else:
            user_id = None
            token = None

        return user_id, token


    def not_allowed(self, connection: Request | WebSocket):
        if isinstance(connection, Request):
            raise HTTPException(status_code=403, detail={"error": "Invalid Credentials"})
        elif isinstance(connection, WebSocket):
            raise WebSocketException(code=1004, reason="Invalid Credentials")
        else:
            raise Exception("Invalid Credentials")
    

# TODOV2: get rid of this
class CoreFrontendAuth(Auth):

    def extract_credentials(self, connection: Request) -> Tuple[str, str] | None:
        """
        Extract user_id from cookie
        """

        token = connection.cookies.get("ccat_user_token", None)

        # core webapps cannot be accessed without a cookie
        if token is None or token == "":
            self.not_allowed(connection)

        return "user", token
    
    def not_allowed(self, connection: Request):
        referer_query = urlencode({"referer": connection.url.path})
        raise HTTPException(
            status_code=307,
            headers={
                "Location": f"/auth/login?{referer_query}"
            }
        )