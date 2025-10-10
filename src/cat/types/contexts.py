from typing import List
from pydantic import BaseModel

from cat.looking_glass import prompts
from .__types_adapter import Resource


class Context(BaseModel):
    instructions: str = prompts.MAIN_PROMPT_PREFIX
    resources: List[Resource] = []
    # TODOV2: should also tools be supported here?