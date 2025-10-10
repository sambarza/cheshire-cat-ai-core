from cat.types import Message

class AgentDefault:

    async def execute(self, cat):

        for i in range(6): # TODOV2: not sure
            llm_mex: Message = await cat.llm(
                # delegate prompt construction to plugins
                await cat.get_system_prompt(),
                # pass conversation messages
                messages=cat.chat_request.messages + cat.chat_response.messages,
                # pass tools (both internal and MCP)
                tools=await cat.list_tools(),
                # whether to stream or not
                stream=cat.chat_request.stream,
                # give a name to LLM execution for logging purposes
                # TODOV2: log should be done via langchain handlers
                execution_name="DEFAULT AGENT"
            )

            cat.chat_response.messages.append(llm_mex)
            
            if len(llm_mex.tool_calls) == 0:
                # No tool calls, exit
                return
            else:
                # LLM has chosen to use tools, run them
                # TODOV2: tools may require explicit user permission
                # TODOV2: tools may return an artifact, resource or elicitation
                for tool_call in llm_mex.tool_calls:
                    # actually executing the tool
                    tool_message = await cat.call_tool(tool_call)
                    # append tool request and tool output messages
                    cat.chat_response.messages.append(tool_message)

                    # if t.return_direct: TODO recover return_direct