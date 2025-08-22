
from importlib.metadata import metadata
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from cat.utils import get_base_path


def get_openapi_configuration_function(cheshire_cat_api: FastAPI):
    # Configure openAPI schema for swagger and redoc
    def custom_openapi():
        if cheshire_cat_api.openapi_schema:
            return cheshire_cat_api.openapi_schema

        meta = metadata("cheshire-cat-ai")

        openapi_schema = get_openapi(
            title=f"Cheshire Cat AI - {meta.get("version")} 🐈",
            version=meta.get("version", "unknown"),
            description=meta.get("Summary"),
            routes=cheshire_cat_api.routes,
            
        )

        cheshire_cat_api.openapi_schema = openapi_schema
        return cheshire_cat_api.openapi_schema

    return custom_openapi
