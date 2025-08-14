
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