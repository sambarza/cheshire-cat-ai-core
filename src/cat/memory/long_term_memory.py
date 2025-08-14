from cat.log import log


class LongTermMemory:
    """Cat's non-volatile memory.

    This is an abstract class to interface with memory/retrieval systems offered by plugins.

    """

    async def store(self, cat, item=None):
        """Store something in long term memory"""
        return # TODOV2

        user_message_text = cat.working_memory.user_message_json.text
        doc = Document(
            page_content=user_message_text,
            metadata={"source": self.user_id, "when": time.time()},
        )
        doc = self.mad_hatter.execute_hook(
            "before_cat_stores_episodic_memory", doc, cat=self
        )
        # store user message in episodic memory
        # TODO: vectorize and store also conversation chunks
        #   (not raw dialog, but summarization)
        user_message_embedding = self.embedder.embed_documents([user_message_text])
        _ = self.memory.vectors.episodic.add_point(
            doc.page_content,
            user_message_embedding[0],
            doc.metadata,
        )

    async def recall(self, cat, query=None):
        """Recall something from long term memory"""
        return [] # TODOV2 cat.mad_hatter.execute_hook([])
    
    async def recall_relevant_memories_to_working_memory(self, cat, query=None):
        """Retrieve context from memory.

        The method retrieves the relevant memories from the vector collections that are given as context to the LLM.
        Recalled memories are stored in the working memory.

        Parameters
        ----------
        query : str, optional
            The query used to make a similarity search in the Cat's vector memories.  
            If not provided, the query will be derived from the last user's message.

        Examples
        --------
        Recall memories from custom query
        >>> cat.recall_relevant_memories_to_working_memory(query="What was written on the bottle?")

        Notes
        -----
        The user's message is used as a query to make a similarity search in the Cat's vector memories.
        Five hooks allow to customize the recall pipeline before and after it is done.

        See Also
        --------
        cat_recall_query
        before_cat_recalls_memories
        before_cat_recalls_episodic_memories
        before_cat_recalls_declarative_memories
        before_cat_recalls_procedural_memories
        after_cat_recalls_memories
        """

        recall_query = query

        if query is None:
            # If query is not provided, use the user's message as the query
            recall_query = cat.working_memory.user_message_json.text

        # We may want to search in memory
        recall_query = cat.mad_hatter.execute_hook(
            "cat_recall_query", recall_query, cat=cat
        )
        log.info(f"Recall query: '{recall_query}'")

        # Embed recall query
        recall_query_embedding = cat.embedder.embed_query(recall_query)
        cat.working_memory.recall_query = recall_query



        # hook to do something before recall begins
        cat.mad_hatter.execute_hook("before_cat_recalls_memories", cat=cat)

        # Setting default recall configs for each memory
        # TODO: can these data structures become instances of a RecallSettings class?
        default_episodic_recall_config = {
            "embedding": recall_query_embedding,
            "k": 3,
            "threshold": 0.7,
            "metadata": {"source": cat.user_id},
        }

        default_declarative_recall_config = {
            "embedding": recall_query_embedding,
            "k": 3,
            "threshold": 0.7,
            "metadata": {},
        }

        default_procedural_recall_config = {
            "embedding": recall_query_embedding,
            "k": 3,
            "threshold": 0.7,
            "metadata": {},
        }

        # hooks to change recall configs for each memory
        recall_configs = [
            cat.mad_hatter.execute_hook(
                "before_cat_recalls_episodic_memories",
                default_episodic_recall_config,
                cat=cat,
            ),
            cat.mad_hatter.execute_hook(
                "before_cat_recalls_declarative_memories",
                default_declarative_recall_config,
                cat=cat,
            ),
            cat.mad_hatter.execute_hook(
                "before_cat_recalls_procedural_memories",
                default_procedural_recall_config,
                cat=cat,
            ),
        ]

        memory_types = cat.memory.vectors.collections.keys()

        for config, memory_type in zip(recall_configs, memory_types):
            memory_key = f"{memory_type}_memories"

            # recall relevant memories for collection
            vector_memory = getattr(cat.memory.vectors, memory_type)
            memories = vector_memory.recall_memories_from_embedding(**config)

            setattr(
                cat.working_memory, memory_key, memories
            )  # self.working_memory.procedural_memories = ...

        # hook to modify/enrich retrieved memories
        cat.mad_hatter.execute_hook("after_cat_recalls_memories", cat=self)

