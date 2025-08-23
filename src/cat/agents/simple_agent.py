
from cat.agents import BaseAgent, AgentOutput

class SimpleAgent(BaseAgent):

    name = "simple"

    def get_prompt(self, cat) -> str:

        # obtain prompt parts from plugins
        # TODOV2: give better naming to these hooks
        prompt_prefix = cat.mad_hatter.execute_hook(
            "agent_prompt_prefix",
            cat.chat_request.instructions,
            cat=cat
        )
        prompt_suffix = cat.mad_hatter.execute_hook(
            "agent_prompt_suffix", "", cat=cat
        )

        return prompt_prefix + prompt_suffix


    async def execute(self, cat) -> AgentOutput:

        res = await cat.llm(
            self.get_prompt(cat),
            messages=cat.chat_request.messages,
            stream=cat.chat_request.stream,
            execution_name="PROMPT"
        )

        return AgentOutput(output=res)
    
