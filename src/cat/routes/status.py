from typing import List
from importlib import metadata
from pydantic import BaseModel

from fastapi import APIRouter, Request

from cat.auth.permissions import AuthPermission, AuthResource, check_permissions

router = APIRouter(prefix="/status", tags=["Status"])


class StatusResponse(BaseModel):
    status: str
    version: str

class FactoryStatusResponse(BaseModel):
    auth_handlers: List[str]
    llms: List[str]
    embedders: List[str]
    agents: List[str]
    mcps: List[str]


@router.get("")
async def status() -> StatusResponse:
    """Server status"""

    return StatusResponse(
        status = "We're all mad here, dear!",
        version = metadata.version("cheshire-cat-ai"),
    )


@router.get("/factory")
async def factory_status(
    r: Request,
    cat=check_permissions(AuthResource.CHAT, AuthPermission.READ),
) -> FactoryStatusResponse:
    """Available factory objects (llms, agents, auth handlers etc)."""

    ccat = r.app.state.ccat

    return FactoryStatusResponse(
        auth_handlers=ccat.auth_handlers.keys(),
        llms=ccat.llms.keys(),
        embedders=ccat.embedders.keys(),
        agents=ccat.agents.keys(),
        mcps=ccat.mcps.keys()
    )


