from typing import Dict, List
from pydantic import BaseModel

from fastapi import APIRouter

from cat.env import get_env
from cat.looking_glass.stray_cat import StrayCat
from cat.auth.permissions import AuthPermission, AuthResource, get_full_permissions, check_permissions

router = APIRouter()

class JWTResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# TODOAUTH /logout endpoint
# TODOAUTH TODOV2 /token/refresh


@router.get("/available-permissions", response_model=Dict[AuthResource, List[AuthPermission]])
async def get_available_permissions(
    cat: StrayCat = check_permissions(AuthResource.AUTH_HANDLER, AuthPermission.LIST),
):
    """Returns all available resources and permissions. Can be extended via plugins."""
    return get_full_permissions()


