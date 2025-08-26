import time
import functools
import inspect
from uuid import uuid4
from inspect import signature
from typing import Union, Callable, List, Dict, Any, Literal

from pydantic import ConfigDict
from langchain_core.tools import StructuredTool

from ag_ui.core.events import EventType # take away after they fix the bug
from cat.protocols.agui import events


# All @tool decorated functions in plugins become a CatTool.
# The difference between base langchain Tool and CatTool is that CatTool has an instance of the cat as attribute (set by the MadHatter)
class CatTool:
    def __init__(
        self,
        name: str,
        func: Callable,
        return_direct: bool = False,
        examples: List[str] = [],
    ):  
        if func.__doc__:
            description = func.__doc__.strip()
        else:
            description = "" # or the function name?
        
        self.func = func
        self.procedure_type = "tool"
        self.name = name
        self.description = description
        self.return_direct = return_direct

        self.triggers_map = {
            "description": [f"{name}: {description}"],
            "start_example": examples,
        }
        # remove cat argument from signature so it does not end up in prompts
        self.signature = f"{signature(self.func)}".replace(", cat)", ")")

    @property
    def start_examples(self):
        return self.triggers_map["start_example"]

    def __repr__(self) -> str:
        return f"CatTool(name={self.name}, return_direct={self.return_direct}, description={self.description})"

    ##################################################
    ### TODOV2: are these two functions still needed?
    def run(self, input_by_llm: dict, cat) -> str:
        """Low level tool function execution, sync."""
        return self.func(input_by_llm, cat=cat) # TODOV2: should be able to allow multiple arguments tools? Ask Manu
    
    async def arun(self, input_by_llm: dict, cat) -> str:
        """Low level tool function execution, async."""
        return self.func(input_by_llm, cat=cat) # TODOV2: multiple arguments tool ^
    ##################################################

    async def execute(self, cat: 'StrayCat', action: 'LLMAction') -> 'LLMAction':
        """
        Execute a CatTool with the provided LLMAction.
        Will store tool output in action.output and emit AGUI events for tool execution.

        Parameters
        ----------
        action : LLMAction
            Object representing the choice of tool made by the LLM
        cat : StrayCat
            Session object.

        Returns
        -------
        LLMAction
            Updated LLM action, with valued output.
        """
        if action.input is None:
            action.input = {}
        tool_output = self.func(
            **action.input, cat=cat
        )

        # Emit AGUI events
        await self.emit_agui_tool_start_events(cat, action)

        # Ensure the output is a string or None, 
        if (tool_output is not None) and (not isinstance(tool_output, str)):
            tool_output = str(tool_output)

        # store tool output
        action.output = tool_output

        # Emit AGUI events
        await self.emit_agui_tool_end_events(cat, action)

        # TODOV2: should return something analogous to:
        #   https://modelcontextprotocol.info/specification/2024-11-05/server/tools/#tool-result
        #   Only supporting text for now
        return action
    
    def remove_cat_from_args(self, function: Callable) -> Callable:
        """
        Remove 'cat' and '_' parameters from function signature for LangChain compatibility.
        
        Parameters
        ----------
        function : Callable
            The function to modify.

        Returns
        -------
        Callable
            The modified function without 'cat' and '_' parameters.
        """
        signature = inspect.signature(function)
        parameters = list(signature.parameters.values())
        
        filtered_parameters = [p for p in parameters if p.name != 'cat' and p.name != '_']
        new_signature = signature.replace(parameters=filtered_parameters)
        
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            if 'cat' in kwargs:
                del kwargs['cat']
            return function(*args, **kwargs)
        
        wrapper.__signature__ = new_signature
        return wrapper
    
    def langchainfy(self):
        """Convert CatTool to a langchain compatible StructuredTool object"""

        if getattr(self, "arg_schema", None) is not None:
            new_tool = StructuredTool(
                name=self.name.strip().replace(" ", "_"),
                description=self.description,
                func=self.remove_cat_from_args(self.func),
                args_schema=self.arg_schema,
            )
        else:
            new_tool = StructuredTool.from_function(
                name=self.name.strip().replace(" ", "_"),
                description=self.description,
                func=self.remove_cat_from_args(self.func),
            )

        return new_tool

        # In case we may want to avoid importing langchain
        # return {
        #     "name": "multiply",
        #     "description": "Multiply two numbers",
        #     "parameters": {
        #         "type": "object",
        #         "properties": {
        #             "a": {"type": "number", "description": "First number"},
        #             "b": {"type": "number", "description": "Second number"}
        #         },
        #         "required": ["a", "b"]
        #     }
        # }

    model_config = ConfigDict(
        extra = "allow"
    )

    async def emit_agui_tool_start_events(self, cat, action):
        await cat.agui_event(
            events.ToolCallStartEvent(
                timestamp=int(time.time()),
                tool_call_id=str(action.id),
                tool_call_name=action.name
            )
        )
        await cat.agui_event(
            events.ToolCallArgsEvent(
                timestamp=int(time.time()),
                tool_call_id=str(action.id),
                delta=str(action.input), # here the protocol assumes tool args are streamed
                raw_event=action.input
            )
        )
    
    async def emit_agui_tool_end_events(self, cat, action):
        await cat.agui_event(
            events.ToolCallEndEvent(
                timestamp=int(time.time()),
                tool_call_id=str(action.id) # may be more than one?
            )
        )
        await cat.agui_event(
            events.ToolCallResultEvent(
                type=EventType.TOOL_CALL_RESULT, # bug in the lib, this should not be necessary
                timestamp=int(time.time()),
                message_id=str(uuid4()), # shold be the id of the last user message
                tool_call_id=str(action.id),
                content=str(action.output)
            )
        )


# @tool decorator, a modified version of a langchain Tool that also takes a Cat instance as argument
# adapted from https://github.com/hwchase17/langchain/blob/master/langchain/agents/tools.py
def tool(
    *args: Union[str, Callable], return_direct: bool = False, examples: List[str] = []
) -> Callable:
    """
    Make tools out of functions, can be used with or without arguments.
    Requires:
        - Function must contain the cat argument -> str
        - Function must have a docstring
    Examples:
        .. code-block:: python
            @tool
            def search_api(query: str, cat) -> str:
                # Searches the API for the query.
                return "https://api.com/search?q=" + query
            @tool("search", return_direct=True)
            def search_api(query: str, cat) -> str:
                # Searches the API for the query.
                return "https://api.com/search?q=" + query
    """

    def _make_with_name(tool_name: str) -> Callable:
        def _make_tool(func: Callable[[str], str]) -> CatTool:
            assert func.__doc__, "Function must have a docstring"
            tool_ = CatTool(
                name=tool_name,
                func=func,
                return_direct=return_direct,
                examples=examples,
            )
            return tool_

        return _make_tool

    if len(args) == 1 and isinstance(args[0], str):
        # if the argument is a string, then we use the string as the tool name
        # Example usage: @tool("search", return_direct=True)
        return _make_with_name(args[0])
    elif len(args) == 1 and callable(args[0]):
        # if the argument is a function, then we use the function name as the tool name
        # Example usage: @tool
        return _make_with_name(args[0].__name__)(args[0])
    elif len(args) == 0:
        # if there are no arguments, then we use the function name as the tool name
        # Example usage: @tool(return_direct=True)
        def _partial(func: Callable[[str], str]) -> CatTool:
            return _make_with_name(func.__name__)(func)

        return _partial
    else:
        raise ValueError("Too many arguments for tool decorator")
