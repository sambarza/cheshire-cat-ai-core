import functools
import inspect
from typing import Union, Callable, List
from inspect import signature

from pydantic import ConfigDict
from langchain_core.tools import StructuredTool


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

    def run(self, input_by_llm: str, cat) -> str:
        return self.func(input_by_llm, cat=cat)
    
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

    # TODOV2: test support for pydantic2 works in langchain
    #class Config:
    #    extra = "allow"
    model_config = ConfigDict(
        extra = "allow"
    )


# @tool decorator, a modified version of a langchain Tool that also takes a Cat instance as argument
# adapted from https://github.com/hwchase17/langchain/blob/master/langchain/agents/tools.py
def tool(
    *args: Union[str, Callable], return_direct: bool = False, examples: List[str] = []
) -> Callable:
    """
    Make tools out of functions, can be used with or without arguments.
    Requires:
        - Function must be of type (str, cat) -> str
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
