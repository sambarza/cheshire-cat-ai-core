from typing import Optional

from cat.experimental.form import CatForm
from cat.utils import BaseModelDict


class WorkingMemory(BaseModelDict):
    """
    Represents the volatile memory of a cat, functioning similarly to a dictionary to store temporary custom data.

    Attributes
    ----------
    active_form : Optional[CatForm], default=None
        An optional reference to a CatForm currently in use.
    recall_query : str, default=""
        A string that stores the last recall query.
    episodic_memories : List
        A list for storing episodic memories.
    declarative_memories : List
        A list for storing declarative memories.
    procedural_memories : List
        A list for storing procedural memories.

    TODOV2: give examples on how to use working memory

    """

    ######### TODOV2 TAKE AWAY ########
    active_form: Optional[CatForm] = None
    recall_query: str = ""
    ######### TAKE AWAY ########
    


