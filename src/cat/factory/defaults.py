
from langchain_core.language_models.llms import LLM # TODOV2 should be BaseChatLLM
from langchain_core.embeddings import FakeEmbeddings


class LLMDefault(LLM):
    @property
    def _llm_type(self):
        return ""

    def _call(self, prompt, stop=None):
        return "You did not configure a Language Model. Do it in the settings!"

    async def _acall(self, prompt, stop=None):
        return "You did not configure a Language Model. Do it in the settings!"
    

# removed dumb embedder to uninstall sklearn. Random embeddings is good
class EmbedderDefault(FakeEmbeddings):
    def __init__(self, *args, **kwargs):
        kwargs["size"] = 128
        super().__init__(*args, **kwargs)