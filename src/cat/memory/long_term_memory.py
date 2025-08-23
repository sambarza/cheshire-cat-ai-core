from typing import List

from .memory_item import MemoryItem


class LongTermMemory:
    """Cat's non-volatile memory.

    This is an abstract class to interface with memory/retrieval systems offered by plugins.

    """

    # TODOV2: subscribe to embedder changes via a new hook

    async def store(self, cat, item=None):
        """Store something in long term memory"""
        return # TODOV2

    async def recall(self, cat, query=None) -> List[MemoryItem]:
        """Recall something from long term memory"""

        # log.critical(await cat.embedder.aembed_query("meow"))

        # TODOV2 cat.mad_hatter.execute_hook([])

        # TODOV2: do validation here, so all contents are indeed MemoryItem objs
        
        return [] 
    
