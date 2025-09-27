
import asyncio
import time
from uuid import uuid4
from collections.abc import AsyncGenerator
from typing import Literal, get_args, List, Dict, Union, Any, Callable

from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import SystemMessagePromptTemplate

from cat.protocols.agui import events
from cat.auth.permissions import AuthUserInfo
from cat.looking_glass.cheshire_cat import CheshireCat
from cat.looking_glass.callbacks import NewTokenHandler
from cat.memory.working_memory import WorkingMemory
from cat.types.chats import ChatRequest, ChatResponse
from cat.types.messages import Message
from cat.mad_hatter.decorators import CatTool
from cat.cache.cache_item import CacheItem
from cat import utils
from cat.log import log

MSG_TYPES = Literal["notification", "chat", "error", "chat_token"]

# The Stray cat goes around tools, hooks and endpoints... making troubles
class StrayCat:
    """Session object containing user data, conversation state and many utility pointers.
    The framework creates an instance for every http request and websocket connection, making it available for plugins.

    You will be interacting with an instance of this class directly from within your plugins:

     - in `@hook`, `@tool` and `@endpoint` decorated functions will be passed as argument `cat` or `stray`

    Parameters
    ----------
    user_data : AuthUserInfo
        User data object containing user information.
    """

    chat_request: ChatRequest | None = None
    """The ChatRequest object coming from the client, containining the request for this conversation turn."""
    
    chat_response: ChatResponse | None = None
    """ChatResponse object that will go out to the client once the conversation turn is finished.
        It is available since the beginning of the Cat flow."""

    working_memory: WorkingMemory
    """State machine containing the conversation state, persisted across conversation turns, acting as a simple dictionary / object.
    Can be used in plugins to store and retrieve data to drive the conversation or do anything else.

    Examples
    --------
    Store a value in the working memory during conversation
    >>> cat.working_memory["location"] = "Rome"
    or
    >>> cat.working_memory.location = "Rome"

    Retrieve a value in later conversation turns
    >>> cat.working_memory["location"]
    "Rome"
    >>> cat.working_memory.location
    "Rome"
    """

    def __init__(
        self,
        user_data: AuthUserInfo,
        ccat: CheshireCat
    ):

        # user data
        self.__user_id = user_data.id
        self.__user_data = user_data

        # pointer to CheshireCat instance
        self._ccat = ccat

        # get working memory from cache or create a new one
        self.load_working_memory_from_cache()

    def __repr__(self):
        return f"StrayCat(user_id={self.user_id}, user_name={self.user_data.name})"

    # TODOV2: method should be one and should be `send_message`.
    #         Stray should not know about websockets or anything network related
    async def __send_ws_json(self, data: Any):
        
        if self.message_callback:
            await self.message_callback(data)


    def load_working_memory_from_cache(self):
        """Load the working memory from the cache."""
        
        self.working_memory = \
            self.cache.get_value(f"{self.user_id}_working_memory") or WorkingMemory()

    def update_working_memory_cache(self):
        """Update the working memory in the cache."""

        updated_cache_item = CacheItem(f"{self.user_id}_working_memory", self.working_memory, -1)
        self.cache.insert(updated_cache_item)


    # TODOV2: take away `ws` and simplify these methods so it is only one
    async def send_ws_message(self, content: str | dict, msg_type: MSG_TYPES = "notification"):
        """Send a message via websocket.

        This method is useful for sending a message via websocket directly without passing through the LLM.  
        In case there is no connection the message is skipped and a warning is logged.

        Parameters
        ----------
        content : str
            The content of the message.
        msg_type : str
            The type of the message. Should be either `notification` (default), `chat`, `chat_token` or `error`

        Examples
        --------
        Send a notification via websocket
        >>> await cat.send_ws_message("Hello, I'm a notification!")

        Send a chat message via websocket
        >>> await cat.send_ws_message("Meooow!", msg_type="chat")
        
        Send an error message via websocket
        >>> await cat.send_ws_message("Something went wrong", msg_type="error")

        Send custom data
        >>> await cat.send_ws_message({"What day it is?": "It's my unbirthday"})
        """

        options = get_args(MSG_TYPES)

        if msg_type not in options:
            raise ValueError(
                f"The message type `{msg_type}` is not valid. Valid types: {', '.join(options)}"
            )

        if msg_type == "error":
            await self.__send_ws_json(
                {"type": msg_type, "name": "GenericError", "description": str(content)}
            )
        else:
            await self.__send_ws_json({"type": msg_type, "content": content})


    async def send_chat_message(self, message: str | ChatResponse):
        """Sends a chat message to the user using the active WebSocket connection.  
        In case there is no connection the message is skipped and a warning is logged

        Parameters
        ----------
        message: str, CatMessage
            Message to send
        save: bool | optional
            Save the message in the conversation history. Defaults to False.

        Examples
        --------
        Send a chat message during conversation from a hook, tool or form
        >>> cat.send_chat_message("Hello, dear!")

        Using a `CatMessage` object
        >>> message = CatMessage(text="Hello, dear!", user_id=cat.user_id)
        ... cat.send_chat_message(message)
        """

        if isinstance(message, str):
            message = ChatResponse(text=message, user_id=self.user_id)

        await self.__send_ws_json(message.model_dump())


    async def send_notification(self, content: str):
        """Sends a notification message to the user using the active WebSocket connection.  
        In case there is no connection the message is skipped and a warning is logged

        Parameters
        ----------
        content: str
            Message to send

        Examples
        --------
        Send a notification to the user
        >>> cat.send_notification("It's late!")
        """
        await self.send_ws_message(content=content, msg_type="notification")


    async def send_error(self, error: Union[str, Exception]):
        """Sends an error message to the user using the active WebSocket connection.

        In case there is no connection the message is skipped and a warning is logged

        Parameters
        ----------
        error: str, Exception
            Message to send

        Examples
        --------
        Send an error message to the user
        >>> cat.send_error("Something went wrong!")
        or
        >>> cat.send_error(CustomException("Something went wrong!"))
        """

        if isinstance(error, str):
            error_message = {
                "type": "error",
                "name": "GenericError",
                "description": str(error),
            }
        else:
            error_message = {
                "type": "error",
                "name": error.__class__.__name__,
                "description": str(error),
            }

        await self.__send_ws_json(error_message)

    async def agui_event(self, event: events.BaseEvent):
        await self.__send_ws_json(dict(event))
    
    # TODOV2: keep .llm sync as it was, for retrocompatibility (returned a string, also)
    #           add an async method for the chain with tools
    async def llm(
            self,
            system_prompt: str,
            prompt_variables: dict = {},
            messages: list[Message] = [],
            tools: list[CatTool] = [],
            model: str | None = None,  # TODOV2 the default?
            stream: bool = False,
            execution_name: str = "prompt"
        ) -> Message: # TODOV2: does not return a string anymore
        """Generate a response using the Large Language Model.

        Parameters
        ----------
        system_prompt : str
            The system prompt (context, personality, or a simple instruction/request).
        prompt_variables : dict
            Structured info to hydrate the system_prompt.
        messages : list[Message]
            Chat messages so far, as a list of `HumanMessage` and `CatMessage`.
        tools : TODOV2
        model : str | None
            LLM to use, in the format `vendor:model`, e.g. `openai:gpt-5`.
            If None, uses default LLM as in the settings.
        stream : bool
            Whether to stream the tokens via websocket or not.
        execution_name : str
            Name of this LLM run, for logging purposes.

        Returns
        -------
        str
            The generated LLM response.

        Examples
        -------
        Detect profanity in a message
        >>> message = cat.working_memory.user_message_json.text
        ... cat.llm(f"Does this message contain profanity: '{message}'?  Reply with 'yes' or 'no'.")
        "no"

        Run the LLM and stream the tokens via websocket
        >>> cat.llm("Tell me which way to go?", stream=True)
        "It doesn't matter which way you go"
        """

        # should we stream the tokens?
        callbacks = []
        if stream:
            # token handler (will emit token events)
            callbacks.append(NewTokenHandler(self))
            # TODOV2: tool choice tokens are not streamed

        # Add callbacks from plugins
        self.mad_hatter.execute_hook(
            "llm_callbacks", callbacks, cat=self
        )

        # ensure prompt variables and placeholders in system_prompt match
        prompt_variables, system_prompt = utils.match_prompt_variables(prompt_variables, system_prompt)
        
        # here we deal with motherfucking langchain
        prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(
                    template=system_prompt
                )
            ] + [m.langchainfy() for m in messages]
        )
        
        llm_with_tools = self._llm
        if hasattr(self._llm, "bind_tools"):
            llm_with_tools = self._llm.bind_tools([
                t.langchainfy() for t in tools
            ])

        chain = (
            prompt
            | RunnableLambda(lambda x: log.langchain_log_prompt(x, execution_name)) # TODOV2: should be done via langchain handler
            | llm_with_tools # TODOV2: make configurable via init_chat_model
            | RunnableLambda(lambda x: log.langchain_log_output(x, execution_name))
        )

        langchain_msg = await chain.ainvoke(
            prompt_variables,
            config=RunnableConfig(callbacks=callbacks)
        )

        return Message.from_langchain(langchain_msg)
        # TODOV2: have a couple of try/except to manage LLM crashes
    

    async def execute_hook(self, hook_name, default_value):
        return self.mad_hatter.execute_hook( # TODOV2: have hook execution async
            hook_name,
            default_value,
            cat=self
        )


    async def execute_agent(self, slug):
        try:
            await self._ccat.execute_agent(slug, self)
        except Exception as e:
            log.error(f"Could not execute agent {slug}: {e}")
            raise e
        

    async def get_system_prompt(self) -> str:

        # obtain prompt parts from plugins
        # TODOV2: give better naming to these hooks
        prompt_prefix = await self.execute_hook(
            "agent_prompt_prefix",
            self.chat_request.context.instructions
        )
        prompt_suffix = await self.execute_hook("agent_prompt_suffix", "")

        return prompt_prefix + prompt_suffix


    async def list_tools(self) -> List[CatTool]:
        """
        Get both plugins' tools and MCP tools in CatTool format.
        """

        mcp_tools = await self.mcp.list_tools()
        mcp_tools = [
            CatTool.from_fastmcp(t, self.mcp.call_tool)
            for t in mcp_tools
        ]

        return mcp_tools + self.mad_hatter.tools
    

    # TODO: should support MCP notation call_tool("name", {a: 32})
    async def call_tool(self, tool_call, *args, **kwargs): # TODO: annotate CatToolResult?
        """Call a tool."""

        name = tool_call["name"]
        for t in await self.list_tools():
            if t.name == name:
                return await t.execute(self, tool_call)
            
        raise Exception(f"Tool {name} not found")
            


    async def __call__(
        self,
        chat_request: ChatRequest,
        message_callback: Callable | None = None
    ) -> ChatResponse:
        """Run the conversation turn.

        This method is called on the user's message received from the client.  
        It is the main pipeline of the Cat, it is called automatically.

        Parameters
        ----------
        chat_request : ChatRequest
            ChatRequest object received from the client via http or websocket.
        message_callback : Callable | None
            A function that will be used to emit messages via http (streaming) or websocket.
            If None, this method will not emit messages and will only return the final ChatResponse.

        Returns
        -------
        chat_response : ChatResponse | None
            ChatResponse object, the Cat's answer to be sent back to the client.
            If message_callback is passed, this method will return None and emit the final response via the message_callback
        """

        # Store message_callback to send messages back to the client
        self.message_callback = message_callback

        # Both request and response are available during the whole flow
        self.chat_request = chat_request
        self.chat_response = ChatResponse(
            messages=[]
        )

        log.info(self.chat_request)

        # Run a totally custom reply (skips all the side effects of the framework)
        fast_reply = self.mad_hatter.execute_hook(
            "fast_reply", {}, cat=self
        )
        if fast_reply != {}: # TODOV2: dunno if this breaks pydantic validation on the output
            return fast_reply

        # hook to modify/enrich user input
        # TODOV2: shuold be compatible with the old `user_message_json`
        self.chat_request = self.mad_hatter.execute_hook(
            "before_cat_reads_message", self.chat_request, cat=self
        )

        # run agent(s). They will populate the ChatResponse
        requested_agent = self.chat_request.agent
        await self.execute_agent(requested_agent)

        # run final response through plugins
        self.chat_response = self.mad_hatter.execute_hook(
            "before_cat_sends_message", self.chat_response, cat=self
        )

        # Return final reply
        log.info(self.chat_response)

        return self.chat_response


    async def run(
        self,
        request: ChatRequest,
    ) -> AsyncGenerator[Any, None]:
        """Runs the Cat keeping a queue of its messages in order to stream them or send them via websocket.
        Emits the main AGUI lifecycle events
        """

        # unique id for this run
        run_id = str(uuid4())
        thread_id = str(uuid4()) # TODO: should it be the one in the db? Was request.thread

        # AGUI event for agent run start
        yield events.RunStartedEvent(
            timestamp=int(time.time()),
            thread_id=thread_id,
            run_id=run_id
        )

        # build queue and task
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        async def callback(msg) -> None:
            await queue.put(msg) # TODO have a timeout
        async def runner() -> None:
            try:
                # Main entry point to StrayCat.__call__, contains the main AI flow
                final_reply = await self(request, callback)

                # AGUI event for agent run finish
                await callback(
                    events.RunFinishedEvent(
                        timestamp=int(time.time()),
                        thread_id=thread_id,
                        run_id=run_id,
                        result=final_reply.model_dump()
                    )
                )
            except Exception as e:
                await callback(
                    events.RunErrorEvent(
                        timestamp=int(time.time()),
                        message=str(e)
                        # result= TODOV2 this should be the final response
                    )
                )
                log.error(e)
                raise e
            finally:
                await queue.put(None)

        try:
            # run the task
            runner_task: asyncio.Task[None] = asyncio.create_task(runner())

            # wait for new messages to stream or websocket back to the client
            while True:
                msg = await queue.get() # TODO have a timeout
                if msg is None:
                    break
                yield msg
        except Exception as e:
            runner_task.cancel()
            yield events.RunErrorEvent(
                timestamp=int(time.time()),
                message=str(e)
            )
            log.error(e)
            raise e



    async def classify(
        self, sentence: str, labels: List[str] | Dict[str, List[str]], score_threshold: float = 0.5
    ) -> str | None:
        """Classify a sentence.

        Parameters
        ----------
        sentence : str
            Sentence to be classified.
        labels : List[str] or Dict[str, List[str]]
            Possible output categories and optional examples.

        Returns
        -------
        label : str
            Sentence category.

        Examples
        -------
        >>> cat.classify("I feel good", labels=["positive", "negative"])
        "positive"

        Or giving examples for each category:

        >>> example_labels = {
        ...     "positive": ["I feel nice", "happy today"],
        ...     "negative": ["I feel bad", "not my best day"],
        ... }
        ... cat.classify("it is a bad day", labels=example_labels)
        "negative"

        """

        if isinstance(labels, dict):
            labels_names = labels.keys()
            examples_list = "\n\nExamples:"
            for label, examples in labels.items():
                for ex in examples:
                    examples_list += f'\n"{ex}" -> "{label}"'
        else:
            labels_names = labels
            examples_list = ""

        labels_list = '"' + '", "'.join(labels_names) + '"'

        prompt = f"""Classify this sentence:
"{sentence}"

Allowed classes are:
{labels_list}{examples_list}

"{sentence}" -> """

        response = await self.llm(prompt).content.text # TODOV2: not tested

        # find the closest match and its score with levenshtein distance
        best_label, score = min(
            ((label, utils.levenshtein_distance(response, label)) for label in labels_names),
            key=lambda x: x[1],
        )

        return best_label if score < score_threshold else None
    

    @property
    def user_id(self) -> str:
        """The user's id.
        
        Returns
        -------
        user_id : str
            Current user's id.
        """
        return self.__user_id
    
    @property
    def user_data(self) -> AuthUserInfo:
        """`AuthUserInfo` object containing user data.

        Returns
        -------
        user_data : AuthUserInfo
            Current user's data.
        """
        return self.__user_data
    
    @property
    def _llm(self):
        """Instance of langchain `LLM`.
        Only use it if you directly want to deal with langchain, prefer method `cat.llm(prompt)` otherwise.
        """
        ccat = self._ccat
        requested_llm = self.chat_request.model
        if requested_llm and requested_llm in ccat.llms:
            return ccat.llms[requested_llm]
        return ccat.factory.get_default("llm")

    @property
    def _embedder(self):
        """Langchain `Embeddings` object.

        Returns
        -------
        embedder : langchain `Embeddings`
            Langchain embedder to turn text into a vector.


        Examples
        --------
        >>> cat.embedder.embed_query("Oh dear!")
        [0.2, 0.02, 0.4, ...]
        >>> await cat.embedder.aembed_query("Oh dear!")
        [0.2, 0.02, 0.4, ...]
        """
        ccat = self._ccat
        requested_embedder = self.chat_request.model # TODOV2: should come from DB options
        if requested_embedder and requested_embedder in ccat.embedders:
            return ccat.llms[requested_embedder]
        return ccat.factory.get_default("embedder")

    @property
    def mad_hatter(self):
        """Gives access to the `MadHatter` plugin manager.

        Returns
        -------
        mad_hatter : MadHatter
            Module to manage plugins.


        Examples
        --------

        Obtain the path in which your plugin is located
        >>> cat.mad_hatter.get_plugin().path
        /app/cat/plugins/my_plugin

        Obtain plugin settings
        >>> cat.mad_hatter.get_plugin().load_settings()
        {"num_cats": 44, "rows": 6, "remainder": 0}
        """
        return self._ccat.mad_hatter
    
    @property
    def cache(self):
        """Gives access to internal cache."""
        return self._ccat.cache
    
    @property
    def mcp(self):
        """Gives access to the MCP client."""
        return self._ccat.mcp_clients[self.user_id]
