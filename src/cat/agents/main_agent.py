

from cat.agents import BaseAgent, AgentOutput
from cat.agents.simple_agent import SimpleAgent
from cat.utils import run_sync_or_async
from cat.log import log


class MainAgent(BaseAgent):
    """Main Agent.
    This class routes between sub agents, that in turn use the LLM.
    """

    def agent_router(self, cat) -> BaseAgent:
        """Selects which agent to run. At the moment the selected agent is taken directly from chat request.
        If no agent is specified, SimpleAgent will run.
        
        When LLMs will be faster, we may introduce an LLM selection (can also be done via plugin).
        """

        simple_agent = SimpleAgent()

        requested_agent = cat.chat_request.agent
        available_agents = [
            simple_agent,
        ] # TODOV2: get decorated @agents from plugins
        
        # route through the available agents
        for a in available_agents:
            if requested_agent == a.name:
                return a
        
        # required agent does not exist
        log.warning(f'Agent "{requested_agent}" does not exist. Using "simple" agent.')
        return simple_agent


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
        cat.mad_hatter.execute_hook(
            "before_agent_starts", cat=cat
        )

        # should we run the default agents?
        agent_fast_reply = cat.mad_hatter.execute_hook(
            "agent_fast_reply", {}, cat=cat
        )
        if isinstance(agent_fast_reply, AgentOutput):
            return agent_fast_reply
        if isinstance(agent_fast_reply, dict) and "output" in agent_fast_reply:
            return AgentOutput(**agent_fast_reply)
        
        selected_agent = self.agent_router(cat)
        #TODOV2 allow sync with inspection (iscoroutine)
        return await run_sync_or_async(
            selected_agent.execute, cat
        )
        


        # TODOV2: tools and forms are currently deactivated
        # run tools and forms
        #procedures_agent = ProceduresAgent()
        #procedures_agent_out : AgentOutput = await procedures_agent.execute(cat)
        #if procedures_agent_out.return_direct:
        #    return procedures_agent_out



        return main_agent_out
