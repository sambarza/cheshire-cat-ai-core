from contextlib import asynccontextmanager
from scalar_fastapi import get_scalar_api_reference

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from cat.log import log
from cat.env import get_env
from cat.routes import (
    base,
    auth,
    settings,
    plugins
)
from cat.routes.websocket import websocket
from cat.routes.static import admin, static
from cat.routes.openapi import get_openapi_configuration_function
from cat.looking_glass.cheshire_cat import CheshireCat


@asynccontextmanager
async def lifespan(app: FastAPI):

    #       ^._.^
    #
    # loads Cat and plugins
    # Every endpoint can access the cat instance via request.app.state.ccat
    # - Not using middleware because I can't make it work with both http and websocket;
    # - Not using Depends because it only supports callables (not instances)
    # - Starlette allows this: https://www.starlette.io/applications/#storing-state-on-the-app-instance
    ccat = CheshireCat()
    await ccat.bootstrap(app)
    
    # set reference to the cat in fastapi state
    app.state.ccat = ccat

    # startup message with admin, public and swagger addresses
    log.welcome()

    # mcp client requires an async context manager itself
    async with ccat.mcp:
        #await ccat.mcp.list_tools() # force initialization
        yield


def custom_generate_unique_id(route: APIRoute):
    return f"{route.name}"


# REST API
cheshire_cat_api = FastAPI(
    lifespan=lifespan,
    generate_unique_id_function=custom_generate_unique_id,
    #openapi_url=None,
    docs_url=None,
    redoc_url=None,
    title="Cheshire Cat AI",
    license_info={
        "name": "GPL-3",
        "url": "https://www.gnu.org/licenses/gpl-3.0.en.html",
    },
)

# Configures the CORS middleware for the FastAPI app
cors_enabled = get_env("CCAT_CORS_ENABLED")
if cors_enabled == "true":
    cors_allowed_origins_str = get_env("CCAT_CORS_ALLOWED_ORIGINS")
    origins = cors_allowed_origins_str.split(",") if cors_allowed_origins_str else ["*"]
    cheshire_cat_api.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add routers to the middleware stack.
cheshire_cat_api.include_router(base.router, tags=["Home"])
cheshire_cat_api.include_router(auth.router, tags=["User Auth"], prefix="/auth")
cheshire_cat_api.include_router(settings.router, tags=["Settings"], prefix="/settings")
cheshire_cat_api.include_router(plugins.router, tags=["Plugins"], prefix="/plugins")
cheshire_cat_api.include_router(websocket.router, tags=["Websocket"])
cheshire_cat_api.include_router(static.router, tags=["Static Files"])

# mount static files
# this cannot be done via fastapi.APIrouter:
# https://github.com/tiangolo/fastapi/discussions/9070

# admin single page app (static build)
# TODOV2: should it be under static?
admin.mount(cheshire_cat_api)

# TODOV2: take away
static.mount(cheshire_cat_api)


# error handling
@cheshire_cat_api.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": exc.errors()},
    )


@cheshire_cat_api.get("/docs", include_in_schema=False)
async def scalar_docs():
    cheshire_cat_api.openapi = get_openapi_configuration_function(cheshire_cat_api)
    return get_scalar_api_reference(
        openapi_url="/openapi.json",
        title=cheshire_cat_api.title,
        scalar_favicon_url="https://cheshirecat.ai/wp-content/uploads/2023/10/Logo-Cheshire-Cat.svg",
    )
