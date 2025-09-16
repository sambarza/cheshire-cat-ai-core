from typing import Dict, List
from pydantic import BaseModel

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

from cat.env import get_env
from cat.looking_glass.stray_cat import StrayCat
from cat.auth.permissions import (
    AuthUserInfo,
    AuthPermission, AuthResource,
    get_full_permissions, check_permissions
)
from cat import utils

router = APIRouter()

# TODOAUTH TODOV2 /logout endpoint
# TODOAUTH TODOV2 /token/refresh


@router.get("/available-permissions")
async def get_available_permissions(
    cat: StrayCat = check_permissions(AuthResource.STATUS, AuthPermission.READ),
) -> Dict[AuthResource, List[AuthPermission]]:
    """Returns all available resources and permissions. Can be extended via plugins."""
    return get_full_permissions()


class AuthHandlerInfo(BaseModel):
    name: str
    login_url: str

@router.get("/handlers")
async def get_auth_handlers(r: Request) -> List[AuthHandlerInfo]:
    """Returns all available auth handlers for OAuth2. Redirect the user to /auth/login/{auth_handler} to start the Oauth flow."""
    
    ahs = []
    for name in r.app.state.ccat.auth_handlers.keys():
        ahs.append(
            AuthHandlerInfo(
                name=name,
                login_url=f"{utils.get_base_url()}/login/{name}"
            )
        )
    
    return ahs


@router.get("/login/{name}")
async def login(r: Request, name: str) -> RedirectResponse:
    if name not in r.app.state.ccat.auth_handlers.keys():
        return HTTPException(status_code=404, detail=f"Auth Handler {name} not found.")
    
    # start OAuth flow
    return RedirectResponse(
        url="https://example.com"
    )

@router.get("/me")
async def get_user_info(
    cat: StrayCat = check_permissions(AuthResource.STATUS, AuthPermission.READ),
) -> AuthUserInfo:
    """Returns user information."""
    return cat.user_data.model_dump()

