
from typing import List, Type
from pydantic import ConfigDict

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from cat.mad_hatter.decorators import hook
from cat.factory.llm import LLMSettings

class TestLLMConfig(LLMSettings):
    """Fake LLM for testing purposes."""

    responses: List[str] = ["I'm a fake LLM!"]

    _pyclass: Type = FakeListChatModel
    

@hook
def factory_allowed_llms(allowed, cat) -> List:
    allowed.append(TestLLMConfig)
    return allowed
