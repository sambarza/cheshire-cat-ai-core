from typing import Any, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, Body
from cat.auth.permissions import AuthPermission, AuthResource, check_permissions
from cat.db import models


router = APIRouter()

class Setting(BaseModel):
    name: str
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


@router.put("/{name}")
async def put_setting(
    name: str,
    value: Any = Body(...),
    cat=check_permissions(AuthResource.SETTING, AuthPermission.WRITE),
) -> Setting:
    """Upsert a setting in the database."""
    if name == "" or value == "":
        raise HTTPException(
            status_code=400,
            detail=f"name or value ar None"
        )

    await models.Setting.set(name, value)
    return Setting(name=name, value=value)


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

    # delete
    await models.Setting.delete(name)
