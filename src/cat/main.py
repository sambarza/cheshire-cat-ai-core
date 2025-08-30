import os
import shutil
import uvicorn
import debugpy
from dotenv import load_dotenv

from cat.env import get_env
from cat.utils import get_base_path, get_project_path, get_plugins_path


def scaffold():
    scaffold_path = os.path.join(get_base_path(), "scaffold")
    for folder in os.listdir(scaffold_path):
        origin = os.path.join(scaffold_path, folder)
        destination = os.path.join(get_project_path(), folder)
        if not os.path.exists(destination):
            shutil.copytree(origin, destination)

    
# RUN!
def main():

    # load env variables
    load_dotenv()
    # TODOV2: make sure this works also when distributed as a package

    # scaffold dev project with minimal folders (cat is used as a package)
    scaffold()

    # debugging utilities, to deactivate put `DEBUG=false` in .env
    debug_config = {}
    if get_env("CCAT_DEBUG") == "true":
        debug_config = {
            "reload": True,
            "reload_dirs": [
                get_base_path(),
                get_plugins_path()
            ],
            "reload_includes": [
                "plugin.json"
            ]
        }

        # expose port to attach debuggers (only in debug mode)
        debugpy.listen(("localhost", 5678))

    # uvicorn running behind an https proxy
    proxy_pass_config = {}
    if get_env("CCAT_HTTPS_PROXY_MODE") in ("1", "true"):
        proxy_pass_config = {
            "proxy_headers": True,
            "forwarded_allow_ips": get_env("CCAT_CORS_FORWARDED_ALLOW_IPS"),
        }

    uvicorn.run(
        "cat.startup:cheshire_cat_api",
        host="0.0.0.0",
        port=int(get_env("CCAT_CORE_PORT")),
        use_colors=True,
        log_level=get_env("CCAT_LOG_LEVEL").lower(),
        **debug_config,
        **proxy_pass_config,
    )

if __name__ == "__main__":
    main()
