
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import SystemMessagePromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.output_parsers.string import StrOutputParser

from cat.looking_glass import prompts
from cat.looking_glass.callbacks import NewTokenHandler
from cat.agents import BaseAgent, AgentOutput
from cat import utils


class MemoryAgent(BaseAgent):

    def execute(self, cat) -> AgentOutput:

        # obtain prompt parts from plugins
        prompt_prefix = cat.mad_hatter.execute_hook(
            "agent_prompt_prefix", prompts.MAIN_PROMPT_PREFIX, cat=cat
        )
        prompt_suffix = cat.mad_hatter.execute_hook(
            "agent_prompt_suffix", prompts.MAIN_PROMPT_SUFFIX, cat=cat
        )

        prompt_variables = cat.mad_hatter.execute_hook(
            "agent_context", {}, cat=cat
        )
        sys_prompt = prompt_prefix + prompt_suffix

        # ensure prompt variables and placeholders match
        prompt_variables, sys_prompt = utils.match_prompt_variables(prompt_variables, sys_prompt)

        prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(
                    template=sys_prompt
                ),
                *(cat.working_memory.langchainfy_chat_history()),
            ]
        )

        chain = (
            prompt
            | RunnableLambda(lambda x: utils.langchain_log_prompt(x, "MAIN PROMPT"))
            | cat._llm
            | RunnableLambda(lambda x: utils.langchain_log_output(x, "MAIN PROMPT OUTPUT"))
            | StrOutputParser()
        )

        callbacks = [
            NewTokenHandler(cat)
        ]
        cat.mad_hatter.execute_hook(
            "llm_callbacks", callbacks, cat=cat
        )

        output = chain.invoke(
            # convert to dict before passing to langchain
            prompt_variables,
            config=RunnableConfig(callbacks=callbacks)
        )

        return AgentOutput(output=output)
    
