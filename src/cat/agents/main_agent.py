
from cat.mad_hatter.mad_hatter import MadHatter
from cat.env import get_env
from cat.agents import BaseAgent, AgentOutput
from cat.agents.memory_agent import MemoryAgent
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
        
        # TODOV2: here is how you list MCP tools, prompts and resources
        tools = await cat.mcp.list_tools()
        prompts = await cat.mcp.list_prompts()
        resources = await cat.mcp.list_resources()
        log.warning(tools)
        log.warning(prompts)
        log.warning(resources)


        # TODOV2: tools and forms are curtrently deactivated
        # run tools and forms
        #procedures_agent = ProceduresAgent()
        #procedures_agent_out : AgentOutput = await procedures_agent.execute(cat)
        #if procedures_agent_out.return_direct:
        #    return procedures_agent_out

        # we run memory agent if:
        # - no procedures were recalled or selected or
        # - procedures have all return_direct=False
        memory_agent = MemoryAgent()
        memory_agent_out : AgentOutput = await memory_agent.execute(cat)

        return memory_agent_out
