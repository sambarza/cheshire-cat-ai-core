from typing import Any, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, Body
from cat.auth.permissions import AuthPermission, AuthResource, check_permissions
from cat.db.models import SettingDB


router = APIRouter(prefix="/settings", tags=["Settings"])

class Setting(BaseModel):
    name: str
    value: Any

class SettingUpdate(BaseModel):
    value: Any


@router.get("")
async def get_settings(
    cat=check_permissions(AuthResource.SETTING, AuthPermission.LIST),
)-> List[Setting]:
    """Get all the global settings available in the database"""

    settings = await SettingDB.all()
    return settings


@router.get("/{name}")
async def get_setting(
    name: str, cat=check_permissions(AuthResource.SETTING, AuthPermission.READ)
) -> Setting:
    """Get the a specific global setting from the database"""

    setting = await SettingDB.get_or_none(name=name)
    if setting is None:
        raise HTTPException(
            status_code=404,
            detail="Not found."
        )
    
    return setting


@router.post("")
async def new_setting(
    setting: Setting = Body(...),
    cat=check_permissions(AuthResource.SETTING, AuthPermission.WRITE),
) -> Setting:
    """Create new global setting in the database."""
    
    new_setting = SettingDB(**(setting.model_dump()))
    await new_setting.save()
    return new_setting


@router.put("/{name}")
async def edit_setting(
    name: str,
    setting: SettingUpdate = Body(...),
    cat=check_permissions(AuthResource.SETTING, AuthPermission.EDIT),
) -> Setting:
    """Update a global setting in the database."""
    
    # does the setting exist?
    old_setting = await SettingDB.get_or_none(name=name)
    if old_setting is None:
        raise HTTPException(
            status_code=404,
            detail=f"Not found."
        )
    
    old_setting.value = setting.value
    await old_setting.save()
    return old_setting


@router.delete("/{name}")
async def delete_setting(
    name: str,
    cat=check_permissions(AuthResource.SETTING, AuthPermission.DELETE),
):
    """Remove a global setting from the database"""

    # does the setting exist?
    setting = await SettingDB.get_or_none(name=name)
    if setting is None:
        raise HTTPException(
            status_code=404,
            detail=f"Not found."
        )
    
    await setting.delete()