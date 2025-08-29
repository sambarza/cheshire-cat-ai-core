from typing import Dict, List
from fastapi import Request, APIRouter, Body, HTTPException
from pydantic import BaseModel

from cat.auth.permissions import AuthPermission, AuthResource, check_permissions
from cat.db import crud, models
from cat.log import log


router = APIRouter()

# llm type and config are saved in settings table under this category
FACTORY_CATEGORY = "llm"

# llm selected configuration is saved under this name
FACTORY_SELECTED_NAME = f"{FACTORY_CATEGORY}_selected"

class FactorySettings(BaseModel):
    name: str
    value: dict
    schema: dict

class FactorySettingsList(BaseModel):
    settings: List[FactorySettings]
    selected_configuration: str

# get configured LLMs and configuration schemas
@router.get("/settings")
async def get_settings(
    request: Request,
    cat=check_permissions(AuthResource.LLM, AuthPermission.LIST), # TODOV2: should be dynamic
) -> FactorySettingsList:
    """Get the list of the Large Language Models"""  # TODOV2: should be dynamic

    factory = request.app.state.ccat.factory
    SCHEMAS = await factory.get_schemas(FACTORY_CATEGORY)

    # get selected LLM, if any
    selected = crud.get_setting_by_name(name=FACTORY_SELECTED_NAME)
    if selected is not None:
        selected = selected["value"]["name"]

    saved_settings = crud.get_settings_by_category(category=FACTORY_CATEGORY)
    saved_settings = {s["name"]: s for s in saved_settings}

    settings = []
    for class_name, schema in SCHEMAS.items():
        if class_name in saved_settings:
            saved_setting = saved_settings[class_name]["value"]
        else:
            saved_setting = {}

        settings.append(
            FactorySettings(
                name=class_name,
                value=saved_setting,
                schema=schema,
            )
        )

    return FactorySettingsList(
        settings=settings,
        selected_configuration=selected,
    )


# get LLM settings and its schema
@router.get("/settings/{className}")
def get_llm_settings(
    request: Request,
    className: str,
    cat=check_permissions(AuthResource.LLM, AuthPermission.READ),
) -> FactorySettings:
    """Get settings and schema of the specified Large Language Model"""
    
    factory = request.app.state.ccat.factory
    SCHEMAS = factory.get_schemas()

    # check that languageModelName is a valid name
    allowed_configurations = list(LLM_SCHEMAS.keys())
    if languageModelName not in allowed_configurations:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"{languageModelName} not supported. Must be one of {allowed_configurations}"
            },
        )

    setting = crud.get_setting_by_name(name=languageModelName)
    schema = LLM_SCHEMAS[languageModelName]

    if setting is None:
        setting = {}
    else:
        setting = setting["value"]

    return {"name": languageModelName, "value": setting, "schema": schema}


@router.put("/settings/{languageModelName}")
def upsert_llm_setting(
    request: Request,
    languageModelName: str,
    payload: Dict = Body({"openai_api_key": "your-key-here"}),
    cat=check_permissions(AuthResource.LLM, AuthPermission.EDIT),
) -> Dict:
    """Upsert the Large Language Model setting"""
    
    factory = request.app.state.ccat.factory
    LLM_SCHEMAS = factory.get_schemas()
    

    # check that languageModelName is a valid name
    allowed_configurations = list(LLM_SCHEMAS.keys())
    if languageModelName not in allowed_configurations:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"{languageModelName} not supported. Must be one of {allowed_configurations}"
            },
        )

    # create the setting and upsert it
    final_setting = crud.upsert_setting_by_name(
        models.Setting(name=languageModelName, category=FACTORY_CATEGORY, value=payload)
    )

    crud.upsert_setting_by_name(
        models.Setting(
            name=FACTORY_SELECTED_NAME,
            category=LLM_SELECTED_CATEGORY,
            value={"name": languageModelName},
        )
    )

    status = {"name": languageModelName, "value": final_setting["value"]}

    ccat = request.app.state.ccat
    # reload llm and embedder of the cat
    ccat.load_natural_language()

    return status
