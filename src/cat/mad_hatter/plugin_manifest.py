from typing import Dict
from pydantic import BaseModel


class PluginManifest(BaseModel):
    id: str
    name: str = None
    version: str = "0.0.0"
    thumb: str = None
    tags: str = None
    description: str = (
        "Description not found for this plugin."
        "Please create a plugin.json manifest"
        " in the plugin folder."
    )
    author_name: str = None
    author_url: str = None
    plugin_url: str = None
    min_cat_version: str = None
    max_cat_version: str = None
    local_info: Dict = {} # store here installed plugin info

