import os
from fastapi import APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from cat import utils

router = APIRouter()


# TODOV2: should this route be protected?
@router.get("/static/{file_path:path}")
async def serve_static(file_path):
    static_dir = utils.get_static_path()
    full_path = os.path.join(static_dir, file_path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        return FileResponse(full_path)
    else:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "File not found"
            }
        )


# TODOV2: take away
def mount(cheshire_cat_api):

    # internal static files folder
    core_static_dir = utils.get_base_path() + "/routes/static/core_static_folder"
    cheshire_cat_api.mount(
        "/core-static",
        StaticFiles(directory=core_static_dir),
        name="core-static",
    )
