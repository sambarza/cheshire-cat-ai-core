from cat.log import log


class LongTermMemory:
    """Cat's non-volatile memory.

    This is an abstract class to interface with memory/retrieval systems offered by plugins.

    """

    # TODOV2: subscribe to embedder changes via a new hook

    async def store(self, cat, item=None):
        """Store something in long term memory"""
        return # TODOV2

    async def recall(self, cat, query=None):
        """Recall something from long term memory"""

        # log.critical(await cat.embedder.aembed_query("meow"))

        return [] # TODOV2 cat.mad_hatter.execute_hook([])
    


