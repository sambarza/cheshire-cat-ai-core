
from typing import List, Type
from pydantic import ConfigDict

from langchain_core.embeddings import FakeEmbeddings

from cat.mad_hatter.decorators import hook
from cat.factory.embedder import EmbedderSettings


class EmbedderTestConfig(EmbedderSettings):
    """Fake embedder for testing purposes."""

    size: int
    _pyclass: Type = FakeEmbeddings


@hook
def factory_allowed_embedders(allowed, cat) -> List:
    return allowed + [ EmbedderTestConfig ]
