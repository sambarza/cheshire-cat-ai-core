
from typing import Dict

from cat.mad_hatter.decorators import endpoint
from cat.auth.permissions import check_permissions, AuthResource, AuthPermission
from cat.utils import BaseModelDict
from .convo import CatMessage

class LegacyHTTPUserMessage(BaseModelDict):
    text: str
    # image: str

# TODOV2: provide legacy support using CatMessage and history stored somewhere??? Or just drop it
@endpoint.post("/message", prefix="/ciao", tags=["Legacy"], response_model=CatMessage)
async def message_with_cat(
    payload: LegacyHTTPUserMessage,
    cat=check_permissions(AuthResource.CONVERSATION, AuthPermission.WRITE),
) -> Dict:
    """Get a response from the Cat"""
    user_message_json = {"user_id": cat.user_id, **payload} # TODOV2: impose user_id

    return await cat.run(user_message_json, True)