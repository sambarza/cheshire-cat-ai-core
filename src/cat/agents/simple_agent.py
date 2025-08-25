from cat.convo.messages import Message
from cat.agents.base_agent import BaseAgent, AgentOutput, LLMAction
from cat.log import log

class SimpleAgent(BaseAgent):

    name = "simple"

    async def execute(self, cat) -> AgentOutput:

        llm_out: Message = await cat.llm(
            await self.get_system_prompt(cat),
            messages=cat.chat_request.messages,
            tools=await self.get_tools(cat), # TODOV2: not sure it is always the case to have cat as an argument
            stream=cat.chat_request.stream,
            execution_name="PROMPT"
        )

        log.warning(llm_out)

        agent_out = AgentOutput()
        if llm_out.content.type == "tool_call":
            # emit event
            # run the tool:
            #   if return_direct, self.cat.send_message
            #   else:
            #       append tool output to chat_request.messages
            #       await self.execute()
            agent_out.output = "I want to run a tool"
            agent_out.actions = [
                LLMAction(
                    name=llm_out.content.tool_call["name"],
                    id=llm_out.content.tool_call["id"],
                    input=llm_out.content.tool_call["args"]["tool_input"],
                    output="non ancora chiamato"
                )
            ] # can be many, and must be converted
        elif llm_out.content.type == "text":
            agent_out.output = llm_out.content.text

        return agent_out
    
