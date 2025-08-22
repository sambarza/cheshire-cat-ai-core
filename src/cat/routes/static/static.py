from fastapi.staticfiles import StaticFiles
#from fastapi import Request, HTTPException

from cat import utils


def mount(cheshire_cat_api):

    # static files folder available to plugins
    static_dir = utils.get_project_path() + "/static"
    cheshire_cat_api.mount(
        "/static/", StaticFiles(directory=static_dir), name="static"
    )

    # internal static files folder
    core_static_dir = utils.get_base_path() + "/routes/static/core_static_folder"
    cheshire_cat_api.mount(
        "/core-static/",
        StaticFiles(directory=core_static_dir),
        name="core-static",
    )
