import os
import tomli
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from cat.utils import get_base_path


def get_openapi_configuration_function(cheshire_cat_api: FastAPI):
    # Configure openAPI schema for swagger and redoc
    def custom_openapi():
        if cheshire_cat_api.openapi_schema:
            return cheshire_cat_api.openapi_schema

        toml_path = os.path.join(get_base_path(), "..", "..", "pyproject.toml")
        with open(toml_path, "rb") as f:
            project_toml = tomli.load(f)["project"]

        openapi_schema = get_openapi(
            title=f"Cheshire Cat AI - {project_toml["version"]} 🐈",
            version=project_toml["version"],
            description=project_toml["description"],
            routes=cheshire_cat_api.routes,
            
        )

        # Image should be an url and it's mostly used for redoc
        openapi_schema["info"]["x-logo"] = {
            "url": "https://cheshirecat.ai/wp-content/uploads/2023/10/Logo-Cheshire-Cat.svg"  # TODO: update with logo
        }

        cheshire_cat_api.openapi_schema = openapi_schema
        return cheshire_cat_api.openapi_schema

    return custom_openapi
