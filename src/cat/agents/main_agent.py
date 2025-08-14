from typing import List, Tuple
from langchain.docstore.document import Document

from cat.mad_hatter.mad_hatter import MadHatter
from cat.env import get_env
from cat.agents import BaseAgent, AgentOutput
from cat.agents.memory_agent import MemoryAgent
from cat.agents.procedures_agent import ProceduresAgent
from cat.log import log


class MainAgent(BaseAgent):
    """Main Agent.
    This class manages sub agents that in turn use the LLM.
    """

    def __init__(self):
        self.mad_hatter = MadHatter()

    async def execute(self, cat) -> AgentOutput:
        """Execute the agents.

        Returns
        -------
        agent_output : AgentOutput
            Reply of the agent, instance of AgentOutput.
        """

        # prepare input to be passed to the agent.
        #   Info will be extracted from working memory
        # Note: agent_input works both as a dict and as an object
        self.mad_hatter.execute_hook(
            "before_agent_starts", cat=cat
        )

        # should we run the default agents?
        agent_fast_reply = self.mad_hatter.execute_hook(
            "agent_fast_reply", {}, cat=cat
        )
        if isinstance(agent_fast_reply, AgentOutput):
            return agent_fast_reply
        if isinstance(agent_fast_reply, dict) and "output" in agent_fast_reply:
            return AgentOutput(**agent_fast_reply)


        # run tools and forms
        procedures_agent = ProceduresAgent()
        procedures_agent_out : AgentOutput = await procedures_agent.execute(cat)
        if procedures_agent_out.return_direct:
            return procedures_agent_out

        # we run memory agent if:
        # - no procedures were recalled or selected or
        # - procedures have all return_direct=False
        memory_agent = MemoryAgent()
        memory_agent_out : AgentOutput = await memory_agent.execute(cat)

        # TODOV2: this should go in the why plugin
        memory_agent_out.intermediate_steps += procedures_agent_out.intermediate_steps

        return memory_agent_out
