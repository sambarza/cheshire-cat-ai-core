
from cat.looking_glass import prompts
from cat.looking_glass.callbacks import NewTokenHandler
from cat.agents import BaseAgent, AgentOutput
from cat import utils


class MemoryAgent(BaseAgent):

    async def execute(self, cat) -> AgentOutput:

        # obtain prompt parts from plugins
        prompt_prefix = cat.mad_hatter.execute_hook(
            "agent_prompt_prefix", prompts.MAIN_PROMPT_PREFIX, cat=cat
        )
        prompt_suffix = cat.mad_hatter.execute_hook(
            "agent_prompt_suffix", prompts.MAIN_PROMPT_SUFFIX, cat=cat
        )

        res = await cat.llm(
            prompt_prefix + prompt_suffix,
            messages=cat.chat_request.messages,
            stream=cat.chat_request.stream,
            execution_name="MAIN PROMPT"
        )

        return AgentOutput(output=res)
    
