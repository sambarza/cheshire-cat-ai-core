import time
from uuid import uuid4
from inspect import signature
from typing import Callable, List, Dict

from langchain_core.tools import StructuredTool
from fastmcp.tools.tool import FunctionTool, ParsedFunction

from ag_ui.core.events import EventType # take away after they fix the bug
from cat.protocols.agui import events
from cat.types import Message, TextContent
from cat.utils import run_sync_or_async


class CatTool:
    """All @tool decorated functions in plugins and MCP tools become a CatTool."""

    def __init__(
        self,
        func: Callable,
        name: str,
        description: str,
        input_schema: Dict,
        output_schema: Dict,
        is_internal: bool = True,
        return_direct: bool = False,
        examples: List[str] = [],
    ):
        self.func = func
        self.name = name 
        self.description = description 
        self.input_schema = input_schema 
        self.output_schema = output_schema

        self.return_direct = return_direct
        self.examples = examples
        self.is_internal = is_internal
    
        # will be assigned by MadHatter
        self.plugin_id = None

    @classmethod
    def from_decorated_function(
        cls,
        func: Callable,
        return_direct: bool = False,
        examples: List[str] = []
    ) -> 'CatTool':
        
        parsed_function = ParsedFunction.from_function(
            func,
            exclude_args=["cat"], # awesome, will only be used at execution
            validate=False
        )

        return cls(
            func,
            name = parsed_function.name,
            description = parsed_function.description,
            input_schema = parsed_function.input_schema,
            output_schema = parsed_function.output_schema,
            return_direct = return_direct,
            examples = examples
        )

    @classmethod
    def from_fastmcp(
        cls,
        t: FunctionTool,
        mcp_client_func: Callable
    ) -> 'CatTool':
        
        return cls(
            func = mcp_client_func,
            name = t.name,
            description = t.description or t.name,
            input_schema = t.inputSchema,
            output_schema = t.outputSchema,
            is_internal = False
        )
    
    def __repr__(self) -> str:
        return f"CatTool(name={self.name}, input_schema={self.input_schema}, internal={self.is_internal})"

    async def execute(self, cat: 'StrayCat', tool_call) -> Message:
        """
        Execute a CatTool with the provided tool_call data structure (which is returned by the LLM).
        Will emit AGUI events for tool execution and return a Message with role="tool".

        Parameters
        ----------
        cat : StrayCat
            Session object.
        tool_call : dict
            Dictionary representing the choice of tool and its args (produced by LLM)

        Returns
        -------
        Message
            A Message with role="tool" and the tool output.
        """

        # Emit AGUI events
        await self.emit_agui_tool_start_events(cat, tool_call)

        # execute the tool
        if self.is_internal:
            # internal tool
            tool_output = await run_sync_or_async(
                self.func, **tool_call["args"], cat=cat
            )
        else:
            # MCP tool
            async with cat.mcp:
                tool_output = await self.func(self.name, tool_call["args"])
        
        # Standardize output
        tool_output = self.standardize_output(tool_call, tool_output) 
        
        # Emit AGUI events
        await self.emit_agui_tool_end_events(cat, tool_call, tool_output)

        # TODOV2: should return something analogous to:
        #   https://modelcontextprotocol.info/specification/2024-11-05/server/tools/#tool-result
        #   Only supporting text for now
        return tool_output

    def standardize_output(self, tool_call, tool_output):

        text = ""

        if isinstance(tool_output, str):
            text = tool_output
        elif hasattr(tool_output, "content"):
            text += tool_output.content[0].text # TODO: many content blocks here of different types, also embedded resources
        else:
            raise Exception("Cannot convert tool output")
        
        return Message(
            role="tool",
            content=TextContent(
                text=text,
                tool={
                    "in": tool_call,
                    "out": tool_output
                }
            )
        )
    
    def langchainfy(self):
        """Convert CatTool to a langchain compatible StructuredTool object"""
        return StructuredTool(
            name=self.name.strip().replace(" ", "_"),
            description=self.description,
            args_schema=self.input_schema,
        )

    async def emit_agui_tool_start_events(self, cat, tool_call):
        await cat.agui_event(
            events.ToolCallStartEvent(
                timestamp=int(time.time()),
                tool_call_id=str(tool_call["id"]),
                tool_call_name=tool_call["name"]
            )
        )
        await cat.agui_event(
            events.ToolCallArgsEvent(
                timestamp=int(time.time()),
                tool_call_id=str(tool_call["id"]),
                delta=str(tool_call["args"]), # here the protocol assumes tool args are streamed
                raw_event=tool_call
            )
        )
    
    async def emit_agui_tool_end_events(self, cat, tool_call, tool_output):
        await cat.agui_event(
            events.ToolCallEndEvent(
                timestamp=int(time.time()),
                tool_call_id=str(tool_call["id"]) # may be more than one?
            )
        )
        await cat.agui_event(
            events.ToolCallResultEvent(
                type=EventType.TOOL_CALL_RESULT, # bug in the lib, this should not be necessary
                timestamp=int(time.time()),
                message_id=str(uuid4()), # shold be the id of the last user message
                tool_call_id=str(tool_call["id"]),
                content=str(tool_output)
            )
        )


def tool(
    func: Callable, return_direct: bool = False, examples: List[str] = []
) -> Callable:
    return CatTool.from_decorated_function(
        func,
        return_direct=return_direct,
        examples=examples
    )

