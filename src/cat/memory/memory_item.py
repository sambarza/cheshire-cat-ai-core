from typing import Any, Dict
from cat.utils import BaseModelDict

# Not sure about this, totally to see
class MemoryItem(BaseModelDict):
    user_id: str
    prompt_section: str = "context"
    content: Any
    metadata: Dict = {}

    @property
    def page_content(self):
        return self.content
    
    @page_content.setter
    def page_content(self, new):
        self.content = new
    # TODOV2: test properties so the MemoryItem is compatible with langchain Document (retrocompatibility)

    def promptify(self):
        """Decide how the MemoryItem is serialized as a string to be inserted into the prompt"""
        return str(self.content)