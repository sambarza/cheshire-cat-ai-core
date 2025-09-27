import aiofiles
import mimetypes
from copy import deepcopy
from typing import Dict, List
from pydantic import BaseModel, ValidationError
from fastapi import Body, APIRouter, HTTPException, UploadFile
from cat.log import log
from cat.mad_hatter.registry import registry_search_plugins, registry_download_plugin
from cat.auth.permissions import AuthPermission, AuthResource, check_permissions
from cat.mad_hatter.plugin_manifest import PluginManifest

router = APIRouter()


# GET plugins
@router.get("")
async def get_available_plugins(
    query: str = None,
    cat=check_permissions(AuthResource.PLUGIN, AuthPermission.LIST),
    # author: str = None, to be activated in case of more granular search
    # tag: str = None, to be activated in case of more granular search
) -> List[PluginManifest]:
    """List available plugins"""

    # retrieve plugins from official repo
    registry_plugins = await registry_search_plugins(query)
    # index registry plugins by url
    registry_plugins_index = {}
    for p in registry_plugins:
        registry_plugins_index[p.id] = p

    # get active plugins
    active_plugins = await cat.mad_hatter.get_active_plugins()

    # list installed plugins' manifest
    installed_plugins = []
    for p in cat.mad_hatter.plugins.values():
        # get manifest
        manifest: PluginManifest = deepcopy(
            p.manifest
        )  # we make a copy to avoid modifying the plugin obj
        manifest.local_info["active"] = p.id in active_plugins

        # do not show already installed plugins among registry plugins
        r = registry_plugins_index.pop(manifest.plugin_url, None)
        
        manifest.local_info["upgrade"] = None
        # filter by query
        plugin_text = manifest.model_dump_json()
        if (query is None) or (query.lower() in plugin_text):
            if r is not None:
                if r.version is not None and r.version != p.manifest.version:
                    manifest["upgrade"] = r["version"]
            installed_plugins.append(manifest)

    return installed_plugins + registry_plugins


@router.get("/{id}")
async def get_plugin_details(
    id: str,
    cat=check_permissions(AuthResource.PLUGIN, AuthPermission.READ),
) -> PluginManifest:
    """Returns information on a single plugin"""

    if not cat.mad_hatter.plugin_exists(id):
        raise HTTPException(status_code=404, detail="Plugin not found")

    active_plugins = await cat.mad_hatter.get_active_plugins()

    plugin = cat.mad_hatter.plugins[id]

    # get manifest and active True/False. We make a copy to avoid modifying the original obj
    plugin_info = deepcopy(plugin.manifest)
    plugin_info.local_info["active"] = id in active_plugins

    return plugin_info


@router.post("/zip")
async def install_plugin(
    file: UploadFile,
    cat=check_permissions(AuthResource.PLUGIN, AuthPermission.WRITE),
) -> PluginManifest:
    """Install a new plugin from a zip file"""

    admitted_mime_types = ["application/zip", "application/x-tar"]
    content_type = mimetypes.guess_type(file.filename)[0]
    if content_type not in admitted_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f'MIME type `{file.content_type}` not supported. Admitted types: {", ".join(admitted_mime_types)}'
        )

    log.info(f"Uploading {content_type} plugin {file.filename}")
    plugin_archive_path = f"/tmp/{file.filename}"
    async with aiofiles.open(plugin_archive_path, "wb+") as f:
        content = await file.read()
        await f.write(content)
    manifest = await cat.mad_hatter.install_plugin(plugin_archive_path)
    return manifest


class PluginRegistryUpload(BaseModel):
    url: str

@router.post("/registry")
async def install_plugin_from_registry(
    payload: PluginRegistryUpload,
    cat=check_permissions(AuthResource.PLUGIN, AuthPermission.WRITE),
) -> PluginManifest:
    """Install a new plugin from registry"""

    # download zip from registry
    try:
        tmp_plugin_path = await registry_download_plugin(payload.url)
        manifest = await cat.mad_hatter.install_plugin(tmp_plugin_path)
    except Exception as e:
        log.error("Could not download plugin form registry")
        raise HTTPException(status_code=500, detail="Could not download plugin form registry")

    return manifest


@router.put("/{id}/toggle", status_code=200)
async def toggle_plugin(
    id: str,
    cat=check_permissions(AuthResource.PLUGIN, AuthPermission.WRITE),
):
    """Enable or disable a single plugin"""

    # check if plugin exists
    if not cat.mad_hatter.plugin_exists(id):
        raise HTTPException(status_code=404, detail="Plugin not found")

    try:
        # toggle plugin
        await cat.mad_hatter.toggle_plugin(id)
    except Exception as e:
        log.error(f"Could not toggle plugin {id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/settings")
async def get_plugin_settings(
    id: str,
    cat=check_permissions(AuthResource.PLUGIN, AuthPermission.READ),
) -> Dict:
    """Returns the settings of a specific plugin"""

    if not cat.mad_hatter.plugin_exists(id):
        raise HTTPException(status_code=404, detail="Plugin not found")

    try:
        settings = cat.mad_hatter.plugins[id].load_settings()
        schema = cat.mad_hatter.plugins[id].settings_schema()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if schema["properties"] == {}:
        schema = {}

    return {"id": id, "value": settings, "schema": schema}


@router.put("/{id}/settings")
async def upsert_plugin_settings(
    id: str,
    payload: Dict = Body({"setting_a": "some value", "setting_b": "another value"}),
    cat=check_permissions(AuthResource.PLUGIN, AuthPermission.EDIT),
) -> Dict:
    """Updates the settings of a specific plugin"""

    if not cat.mad_hatter.plugin_exists(id):
        raise HTTPException(status_code=404, detail="Plugin not found")

    # Get the plugin object
    plugin = cat.mad_hatter.plugins[id]

    try:
        # Load the plugin settings Pydantic model
        PluginSettingsModel = plugin.settings_model()
        # Validate the settings
        PluginSettingsModel.model_validate(payload)
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail="\n".join(list(map((lambda x: x["msg"]), e.errors()))), # TODOV2: can be raw JSON
        )

    final_settings = plugin.save_settings(payload)

    return {"id": id, "value": final_settings}


@router.delete("/{id}")
async def delete_plugin(
    id: str,
    cat=check_permissions(AuthResource.PLUGIN, AuthPermission.DELETE),
) -> Dict:
    """Physically remove plugin."""

    try:
        # remove folder, hooks and tools
        await cat.mad_hatter.uninstall_plugin(id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
