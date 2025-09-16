from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from typing import Literal
from pytz import utc
import jwt
from jwt.exceptions import InvalidTokenError

from cat.auth.permissions import (
    AuthPermission, AuthResource, AuthUserInfo, get_full_permissions
)
from cat.env import get_env
from cat.log import log

class BaseAuthHandler(ABC):  # TODOAUTH: pydantic model?
    """
    Base class to build custom Auth systems.
    """

    async def authorize_user_from_credential(
        self,
        credential: str,
        auth_resource: AuthResource,
        auth_permission: AuthPermission,
    ) -> AuthUserInfo | None:

        if credential is None:
            return None

        if self.is_jwt(credential):
            # JSON Web Token auth
            return self.authorize_user_from_jwt(
                credential, auth_resource, auth_permission
            )
        else:
            # API_KEY auth
            return self.authorize_user_from_key(
                credential, auth_resource, auth_permission
            )
        
    def is_jwt(self, token: str) -> bool:
        """
        Returns whether a given string is a JWT.
        """
        try:
            # Decode the JWT without verification to check its structure
            jwt.decode(token, options={"verify_signature": False})
            return True
        except InvalidTokenError:
            return False

    def issue_jwt(self, user: AuthUserInfo) -> str | None:
        
        # TODOAUTH: expiration with timezone needs to be tested
        # using seconds for easier testing
        expire_delta_in_seconds = float(get_env("CCAT_JWT_EXPIRE_MINUTES")) * 60
        expires = datetime.now(utc) + timedelta(seconds=expire_delta_in_seconds)

        jwt_content = {
            "sub": user.id,                      # Subject (the user ID)
            "username": user.name,               # Username
            "permissions": user.permissions,     # User permissions
            "extra": user.extra,                 # Additional information
            "exp": expires                       # Expiry date as a Unix timestamp
        }
        return jwt.encode(
            jwt_content,
            get_env("CCAT_JWT_SECRET"),
            algorithm=get_env("CCAT_JWT_ALGORITHM"),
        )
    
    @abstractmethod
    async def authorize_user_from_jwt(
        self,
        token: str,
        auth_resource: AuthResource,
        auth_permission: AuthPermission
    ) -> AuthUserInfo | None:
        pass

    @abstractmethod
    async def authorize_user_from_key(
        self,
        api_key: str,
        auth_resource: AuthResource,
        auth_permission: AuthPermission
    ) -> AuthUserInfo | None:
        pass