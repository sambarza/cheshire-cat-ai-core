from cat.mad_hatter.decorators import hook

# TODOV2 types
# catmesg.why.model_interactions: List[LLMModelInteraction | EmbedderModelInteraction]


# TODOV2 done doing recall
# keep track of embedder model usage
#cat.working_memory.model_interactions.append(
#    EmbedderModelInteraction(
#        prompt=[recall_query],
#        source=utils.get_caller_info(skip=1),
#        reply=recall_query_embedding, # TODO: should we avoid storing the embedding?
#        input_tokens=len(tiktoken.get_encoding("cl100k_base").encode(recall_query)),
#    )
#)


# TODOV2 handlers
# add to hook `llm_callbacks` (revise name)
# ModelInteractionHandler(cat, utils.get_caller_info(skip=1))
@hook
def llm_callbacks(callbacks, cat):
    return callbacks # TODOV2 append the handlers


# TODOV2 was attached to working memory
# working_memory.model_interactions: List[ModelInteraction] = []
