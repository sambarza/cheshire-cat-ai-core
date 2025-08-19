from langchain_core.callbacks.base import BaseCallbackHandler

class NewTokenHandler(BaseCallbackHandler):
    def __init__(self, cat):
        # cat could be an instance of CheshireCat or StrayCat
        self.cat = cat

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        await self.cat.send_ws_message(token, msg_type="chat_token")


