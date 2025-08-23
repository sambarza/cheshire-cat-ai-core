from fastapi.staticfiles import StaticFiles

from cat import utils


def mount(cheshire_cat_api):

    # static files folder available to plugins
    cheshire_cat_api.mount(
        "/static",
        StaticFiles(directory=utils.get_static_path()),
        name="static"
    )

    # internal static files folder
    core_static_dir = utils.get_base_path() + "/routes/static/core_static_folder"
    cheshire_cat_api.mount(
        "/core-static",
        StaticFiles(directory=core_static_dir),
        name="core-static",
    )
