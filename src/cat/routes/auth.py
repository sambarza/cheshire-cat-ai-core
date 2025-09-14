from typing import Dict, List

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

from cat.env import get_env
from cat.looking_glass.stray_cat import StrayCat
from cat.auth.permissions import AuthPermission, AuthResource, get_full_permissions, check_permissions

router = APIRouter()

# TODOAUTH TODOV2 /logout endpoint
# TODOAUTH TODOV2 /token/refresh


@router.get("/available-permissions")
async def get_available_permissions(
    cat: StrayCat = check_permissions(AuthResource.STATUS, AuthPermission.READ),
) -> Dict[AuthResource, List[AuthPermission]]:
    """Returns all available resources and permissions. Can be extended via plugins."""
    return get_full_permissions()


@router.get("/auth-handlers")
async def get_auth_handlers(r: Request) -> List[str]:
    """Returns all available auth handlers for OAuth2. Redirect the user to /auth/login/{auth_handler} to start the Oauth flow."""
    return list(r.app.state.ccat.auth_handlers.keys())


@router.get("/auth/login/{auth_handler}")
async def login(r: Request, auth_handler: str) -> RedirectResponse:
    if auth_handler not in r.app.state.ccat.auth_handlers.keys():
        return HTTPException(status_code=404, detail=f"Auth Handler {auth_handler} not found.")
    
    # start OAuth flow
    return RedirectResponse(
        url="https://example.com"
    )


