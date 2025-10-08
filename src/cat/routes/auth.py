from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

from cat.looking_glass.stray_cat import StrayCat
from cat.auth.permissions import (
    AuthUserInfo,
    AuthPermission, AuthResource,
    check_permissions
)


router = APIRouter(prefix="/auth", tags=["Auth"])

# TODOAUTH TODOV2 /logout endpoint
# TODOAUTH TODOV2 /token/refresh


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
    cat: StrayCat = check_permissions(AuthResource.CHAT, AuthPermission.READ),
) -> AuthUserInfo:
    """Returns user information."""
    return cat.user_data.model_dump()

