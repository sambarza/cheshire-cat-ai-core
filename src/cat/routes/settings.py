from typing import Any, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, Body
from cat.auth.permissions import AuthPermission, AuthResource, check_permissions
from cat.db import models


router = APIRouter()

class Setting(BaseModel):
    name: str
    value: Any

class SettingUpdate(BaseModel):
    value: Any


@router.get("/")
async def get_settings(
    cat=check_permissions(AuthResource.SETTING, AuthPermission.LIST),
)-> List[Setting]:
    """Get the entire list of settings available in the database"""

    settings = await models.Setting.get_all()
    return settings


@router.get("/{name}")
async def get_setting(
    name: str, cat=check_permissions(AuthResource.SETTING, AuthPermission.READ)
) -> Setting:
    """Get the a specific setting from the database"""

    setting_value = await models.Setting.get(name)
    if setting_value is None:
        raise HTTPException(
            status_code=404,
            detail="Not found."
        )
    
    return Setting(name=name, value=setting_value)


@router.post("")
async def new_setting(
    setting: Setting = Body(...),
    cat=check_permissions(AuthResource.SETTING, AuthPermission.WRITE),
) -> Setting:
    """Create new setting in the database."""
    if setting.name == "" or setting.value == "":
        raise HTTPException(
            status_code=400,
            detail=f"name or value are None"
        )

    await models.Setting.set(setting.name, setting.value)
    return setting


@router.put("/{name}")
async def edit_setting(
    name: str,
    setting: SettingUpdate = Body(...),
    cat=check_permissions(AuthResource.SETTING, AuthPermission.EDIT),
) -> Setting:
    """Update a setting in the database."""
    if name == "" or setting.value == "":
        raise HTTPException(
            status_code=400,
            detail=f"name or value are None"
        )
    
    prev_value = await models.Setting.get(name)
    if prev_value is None:
        raise HTTPException(
            status_code=404,
            detail=f"Not found"
        )

    await models.Setting.set(name, setting.value)
    return Setting(name=name, value=setting.value)


@router.delete("/{name}")
async def delete_setting(
    name: str,
    cat=check_permissions(AuthResource.SETTING, AuthPermission.DELETE),
):
    """Delete a specific setting in the database"""

    # does the setting exist?
    setting = await models.Setting.get(name)
    if setting is None:
        raise HTTPException(
            status_code=404,
            detail=f"Not found."
        )

    await models.Setting.delete(name)
