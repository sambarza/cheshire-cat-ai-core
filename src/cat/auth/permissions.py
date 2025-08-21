from enum import Enum
from typing import Dict, List

from fastapi import Depends

from cat.utils import BaseModelDict


class AuthResource(str, Enum):
    STATUS = "STATUS"
    MEMORY = "MEMORY"
    CONVERSATION = "CONVERSATION"
    SETTINGS = "SETTINGS"
    LLM = "LLM"
    EMBEDDER = "EMBEDDER"
    AUTH_HANDLER = "AUTH_HANDLER"
    USERS = "USERS"
    UPLOAD = "UPLOAD"
    PLUGINS = "PLUGINS"
    STATIC = "STATIC"


class AuthPermission(str, Enum):
    WRITE = "WRITE"
    EDIT = "EDIT"
    LIST = "LIST"
    READ = "READ"
    DELETE = "DELETE"


def get_full_permissions() -> Dict[AuthResource, List[AuthPermission]]:
    """
    Returns all available resources and permissions.
    """
    perms = {}
    for res in AuthResource:
        perms[res.name] = [p.name for p in AuthPermission]
    return perms


def get_base_permissions() -> Dict[AuthResource, List[AuthPermission]]:
    """
    Returns the default permissions for new users (chat only!).
    """
    return {
        AuthResource.STATUS: [
            AuthPermission.READ
        ],
        AuthResource.MEMORY: [
            AuthPermission.READ,
            AuthPermission.LIST
        ],
        AuthResource.CONVERSATION: [
            AuthPermission.WRITE,
            AuthPermission.EDIT,
            AuthPermission.LIST,
            AuthPermission.READ,
            AuthPermission.DELETE
        ],
        AuthResource.STATIC: [
            AuthPermission.READ
        ],
    }


class AuthUserInfo(BaseModelDict):
    """
    Class to represent token content after the token has been decoded.
    Will be creted by AuthHandler(s) to standardize their output.
    Core will use this object to retrieve or create a StrayCat (session)
    """

    # TODOAUTH: id & username can be confused when is time to retrieve or create a StrayCat
    # (id should be used)
    id: str
    name: str

    # permissions
    permissions: Dict[AuthResource, List[AuthPermission]] | Dict[str, List[str]] = get_base_permissions()

    # only put in here what you are comfortable to pass plugins:
    # - profile data
    # - custom attributes
    # - roles
    extra: BaseModelDict = BaseModelDict()




from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
#@router.post("/token2")
#async def login( schema=Depends(oauth2_scheme)):
#   return {"access_token": "PORCA MADONNA", "token_type": "bearer"}


def check_permissions(resource: AuthResource | str, permission: AuthPermission | str):
    """
    Helper function to inject a StrayCat into endpoints after checking for required permissions.

    Parameters
    ----------
    resource: AuthResource | str
        The resource that the user must have permission for.
    permission: AuthPermission | str
        The permission that the user must have for the resource.

    Returns
    ----------
    cat: StrayCat | None
        User session object if auth is successfull, None otherwise.
    """

    # import here to avoid circular imports
    from cat.auth.connection import HTTPAuth

    return Depends(HTTPAuth(
        # in case strings are passed, we do not force to the enum, to allow custom permissions
        # (which in any case are to be matched in the endpoint)
        resource = resource, 
        permission = permission,
    ))
    
