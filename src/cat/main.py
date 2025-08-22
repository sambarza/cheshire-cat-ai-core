import os
import shutil
import uvicorn

from cat.env import get_env
from cat.utils import get_base_path, get_project_path


def scaffold():

    scaffold_path = os.path.join(get_base_path(), "scaffold")

    for folder in os.listdir(scaffold_path):
        origin = os.path.join(scaffold_path, folder)
        destination = os.path.join(get_project_path(), folder)
        if not os.path.exists(destination):
            shutil.copytree(origin, destination)

    
# RUN!
def main():

    # scaffold dev project (cat is used as a package)
    scaffold()

    # debugging utilities, to deactivate put `DEBUG=false` in .env
    debug_config = {}
    if get_env("CCAT_DEBUG") == "true":
        debug_config = {
            "reload": True,
            "reload_includes": ["plugin.json"],
            "reload_excludes": ["*test_*.*", "*mock_*.*"],
            # TODOV2: watcher looks into .venv, something sketchy
            # TODOV2: there should be a reload in production
            #         to allow uv sync with plugins dependencies (it does not restart the interpreter)
        }
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
