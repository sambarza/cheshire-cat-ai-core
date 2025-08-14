
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

        context = cat.mad_hatter.execute_hook(
            "agent_context", {}, cat=cat
        )

        # ensure prompt variables and placeholders match
        sys_prompt = prompt_prefix + prompt_suffix
        context, sys_prompt = utils.match_prompt_variables(context, sys_prompt)

        # TODOV2: hydrate prompt


        res = await cat.llm(
            sys_prompt,
            prompt_variables=context,
            use_chat_history=True,
            stream=True,
            execution_name="MAIN PROMPT"
        )

        return AgentOutput(output=res)
    
