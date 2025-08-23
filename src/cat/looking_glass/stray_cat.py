
import asyncio
from collections.abc import AsyncGenerator

from typing import Literal, get_args, List, Dict, Union, Any, Callable

from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import SystemMessagePromptTemplate
from langchain_core.output_parsers.string import StrOutputParser

from cat.auth.permissions import AuthUserInfo
from cat.looking_glass.cheshire_cat import CheshireCat
from cat.looking_glass.callbacks import NewTokenHandler
from cat.memory.working_memory import WorkingMemory
from cat.convo.messages import ChatRequest, ChatResponse, ChatMessage
from cat.mad_hatter.decorators import CatTool
from cat.agents import AgentOutput
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
     - in `@form` decorated classes you can access it via `self.cat`

    Parameters
    ----------
    user_data : AuthUserInfo
        User data object containing user information.
    """

    chat_request: ChatRequest | None = None
    chat_response: ChatResponse | None = None

    working_memory: WorkingMemory
    """State machine containing the conversation state, acting as a simple dictionary / object.
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
        user_data: AuthUserInfo
    ):

        # user data
        self.__user_id = user_data.name # TODOV2: use id
        self.__user_data = user_data

        self.chat_request = ChatRequest() # empty, will be set upon message requests
        self.chat_response = ChatResponse(user_id=self.user_id, text="") # empty, will be set upon message requests
        
        # get working memory from cache or create a new one
        self.load_working_memory_from_cache()

    def __repr__(self):
        return f"StrayCat(user_id={self.user_id}, user_name={self.user_data.name})"

    # TODOV2: method should be one and should be `send_message`.
    #         Stray should not know about websockets or anything network related
    async def __send_ws_json(self, data: Any):
        
        if self.message_callback:
            await self.message_callback(data)


    async def recall(self, query=None):
        """Recall long term memories."""
        await self.memory.recall(cat=self, query=query)


    async def store(self, item=None):
        """Store info in long term memory"""
        await self.memory.store(cat=self, item=item)


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


    async def llm(
            self,
            system_prompt: str,
            prompt_variables: dict = {},
            use_chat_history: bool = False,
            messages: list[ChatMessage] = [],
            tools: list[CatTool] = [], # TODOV2
            model: str | None = None,  # TODOV2
            stream: bool = False,
            execution_name: str = "prompt"
        ) -> str:
        """Generate a response using the Large Language Model.

        Parameters
        ----------
        system_prompt : str
            The system prompt (context, personality, or a simple instruction/request).
        prompt_variables : dict
            Structured info to hydrate the system_prompt.
        use_chat_history : bool
            When `True`, will load messages from working memory. Default is `False`
        messages : list[Message]
            Chat messages so far, as a list of `HumanMessage` and `CatMessage`. Will override `use_chat_history` when used.
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
            callbacks.append(NewTokenHandler(self))

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

        chain = (
            prompt
            | RunnableLambda(lambda x: utils.langchain_log_prompt(x, execution_name))
            | self._llm # TODOV2: make configurable via init_chat_model
            | RunnableLambda(lambda x: utils.langchain_log_output(x, execution_name))
            | StrOutputParser()
        )

        output = await chain.ainvoke(
            prompt_variables,
            config=RunnableConfig(callbacks=callbacks)
        )

        return output
    

    async def __call__(
        self,
        message_request: ChatRequest,
        message_callback: Callable | None = None
    ) -> ChatResponse:
        """Run the conversation turn.

        This method is called on the user's message received from the client.  
        It is the main pipeline of the Cat, it is called automatically.

        Parameters
        ----------
        message_request : ChatRequest
            Dictionary received from the client via http or websocket.

        Returns
        -------
        final_output : ChatResponse
            ChatResponse object, the Cat's answer to be sent back to the client.
        """

        # Store message_callback to send intermediate messages back to the client
        self.message_callback = message_callback

        # Both request and response are available during the whole flow
        self.chat_request = message_request
        self.chat_response = ChatResponse(
            user_id=self.user_id,
            text="meow"
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

        log.info(self.chat_request)

        try:
            # recall episodic and declarative memories from vector collections
            #   and store them in working_memory
            await self.recall()

            # reply with agent
            agent_output: AgentOutput = await self.main_agent.execute(self)
        except Exception as e:
            log.error(e)
            await self.send_error(str(e))

        # prepare final cat message
        # TODOV2: makes no sense, the agent itself can edit cat.working_memory.chat_response
        final_output = ChatResponse(
            user_id=self.user_id, text=str(agent_output.output)
        )

        # run message through plugins
        final_output = self.mad_hatter.execute_hook(
            "before_cat_sends_message", final_output, cat=self
        )

        # will both call the callback (if any) and return the final reply
        log.info(final_output)
        await self.send_chat_message(final_output)
        return final_output


    async def run(
        self,
        user_message: ChatRequest,
    ) -> AsyncGenerator[Any, None]:
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def callback(msg: str) -> None:
            await queue.put(msg)

        async def runner() -> None:
            try:
                # Assuming self(user_message, callback) is awaitable
                await self(user_message, callback)  # type: ignore[call-arg]
            except Exception as e:
                await queue.put(f"[Error] {e}")
            finally:
                await queue.put(None)

        runner_task: asyncio.Task[None] = asyncio.create_task(runner())

        try:
            while True:
                msg = await queue.get()
                if msg is None:
                    break
                yield msg
        except asyncio.CancelledError:
            runner_task.cancel()
            raise

    # async def run(self, message, return_message=False):
    #     try:
    #         # run main flow
    #         cat_message = await self.__call__(message)
    #         # save working memory to cache
    #         self.update_working_memory_cache()

    #         if return_message:
    #             # return the message for HTTP usage
    #             return cat_message
    #         else:
    #             # send message back to client via WS
    #             await self.send_chat_message(cat_message)
    #     except Exception as e:
    #         log.error(e)
    #         if return_message:
    #             return {"error": str(e)}
    #         else:
    #             try:
    #                 await self.send_error(e)
    #             except ConnectionClosedOK as ex:
    #                 log.warning(ex)


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

        response = await self.llm(prompt)

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
        return CheshireCat()._llm

    @property
    def embedder(self):
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
        return CheshireCat().embedder

    @property
    def memory(self):
        """Gives access to the long term memory, containing vector DB collections (episodic, declarative, procedural).

        Returns
        -------
        memory : LongTermMemory
            Long term memory of the Cat.


        Examples
        --------
        TODO examples
        """
        return CheshireCat().memory

    @property
    def rabbit_hole(self):
        """Gives access to the `RabbitHole`, to upload documents and URLs into the vector DB.

        Returns
        -------
        rabbit_hole : RabbitHole
            Module to ingest documents and URLs for RAG.


        Examples
        --------
        >>> cat.rabbit_hole.ingest_file(...)
        """
        return CheshireCat().rabbit_hole

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
        return CheshireCat().mad_hatter

    @property
    def main_agent(self):
        """Gives access to the default main agent.
        """
        return CheshireCat().main_agent

    @property
    def white_rabbit(self):
        """Gives access to `WhiteRabbit`, to schedule repeatable tasks.

        Returns
        -------
        white_rabbit : WhiteRabbit
            Module to manage cron tasks via `APScheduler`.

        Examples
        --------
        Send a websocket message after 30 seconds
        >>> def ring_alarm_api():
        ...     cat.send_chat_message("It's late!")
        ...
        ... cat.white_rabbit.schedule_job(ring_alarm_api, seconds=30)
        """
        return CheshireCat().white_rabbit
    
    @property
    def cache(self):
        """Gives access to internal cache."""
        return CheshireCat().cache
    
    @property
    def mcp(self):
        """Gives access to the MCP client."""
        return CheshireCat().mcp
