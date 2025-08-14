from langchain.callbacks.base import BaseCallbackHandler

class NewTokenHandler(BaseCallbackHandler):
    def __init__(self, cat):
        # cat could be an instance of CheshireCat or StrayCat
        self.cat = cat

    # TODOV2: callback works but ws tokens are flushed all at once
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        await self.cat.send_ws_message(token, msg_type="chat_token")


