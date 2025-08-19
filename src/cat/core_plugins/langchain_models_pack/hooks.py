

from cat.mad_hatter.decorators import hook

from .embedders import configs as embedders_configs
from .llms import configs as llms_configs

# TODOV2: make discovery automatic by checking class type

@hook
def factory_allowed_embedders(configs, cat):
    
    return configs + [
        embedders_configs.EmbedderQdrantFastEmbedConfig,
        embedders_configs.EmbedderOllamaConfig,
        embedders_configs.EmbedderOpenAIConfig,
        embedders_configs.EmbedderOpenAICompatibleConfig,
        embedders_configs.EmbedderAzureOpenAIConfig,
        embedders_configs.EmbedderGeminiChatConfig,
    ]

@hook
def factory_allowed_llms(configs, cat):
    return configs + [
        llms_configs.LLMOllamaConfig,
        llms_configs.LLMOpenAICompatibleConfig,
        llms_configs.LLMOpenAIChatConfig,
        llms_configs.LLMGeminiChatConfig,
        llms_configs.LLMAnthropicChatConfig,
    ]