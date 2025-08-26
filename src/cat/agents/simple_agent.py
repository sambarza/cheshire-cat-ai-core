import time
from uuid import uuid4

from cat.agents.base_agent import BaseAgent, AgentOutput, LLMAction
from cat.log import log

class SimpleAgent(BaseAgent):
    """The default agent being run if no other were selected.
        Handles one tool call per conversation turn.
    """

    name = "simple"

    async def execute(self) -> AgentOutput:

        llm_out = await self.cat.llm(
            await self.get_system_prompt(),
            messages=self.cat.chat_request.messages,
            tools=await self.get_tools(),
            stream=self.cat.chat_request.stream,
            execution_name=f"{self.name.upper()} AGENT"
        )

        from numpy import random
        if random.random() > 0.5:
            a = 9/0

        if type(llm_out) is str:
            # simple string message
            return AgentOutput(output=llm_out)
        elif type(llm_out) is LLMAction:
            # LLM has chosen a tool, run it to get the output
            for t in await self.get_tools():
                if t.name == llm_out.name:
                    # update the action with an output, actually executing the tool
                    llm_out = await t.execute(self.cat, llm_out)
                    # TODOV2: update message list with a tool call message

            agent_output = AgentOutput(
                output=llm_out.output,
                actions=[llm_out]
            )

            # give back the output
            return agent_output
        else:
            return AgentOutput()
    
