"""The log engine."""

import logging
import sys
import json
import traceback
from pprint import pformat
from loguru import logger

from cat.env import get_env


def get_log_level():
    """Return the global LOG level."""
    return get_env("CCAT_LOG_LEVEL")


class CatLogEngine:
    """The log engine.

    Engine to filter the logs in the terminal according to the level of severity.

    Attributes
    ----------
    LOG_LEVEL : str
        Level of logging set in the `.env` file.

    Notes
    -----
    The logging level set in the `.env` file will print all the logs from that level to above.
    Available levels are:

        - `DEBUG`
        - `INFO`
        - `WARNING`
        - `ERROR`
        - `CRITICAL`

    Default to `CCAT_LOG_LEVEL` env variable (`INFO`).
    """

    def __init__(self):
        self.LOG_LEVEL = get_log_level()
        self.default_log()

        # workaround for pdfminer logging
        # https://github.com/pdfminer/pdfminer.six/issues/347
        logging.getLogger("pdfminer").setLevel(logging.WARNING)

    def show_log_level(self, record):
        """Allows to show stuff in the log based on the global setting.

        Parameters
        ----------
        record : dict

        Returns
        -------
        bool

        """
        return record["level"].no >= logger.level(self.LOG_LEVEL).no

    def default_log(self):
        """Set the same debug level to all the project dependencies.

        Returns
        -------
        """

        level = "<level>{level}:</level>"
        # time = "<green>[{time:YYYY-MM-DD HH:mm:ss.SSS}]</green>"
        # origin = "<level>{extra[original_name]}.{extra[original_class]}.{extra[original_caller]}::{extra[original_line]}</level>"
        message = "<level>{message}</level>"
        log_format = f"{level}\t{message}"

        logger.remove()
        logger.add(
            sys.stdout,
            level=self.LOG_LEVEL,
            colorize=True,
            format=log_format,
            # backtrace=True,
            # diagnose=True,
            filter=self.show_log_level,
        )

    def __call__(self, msg, level="DEBUG"):
        """Alias of self.log()"""
        self.log(msg, level)

    def debug(self, msg):
        """Logs a DEBUG message"""
        self.log(msg, level="DEBUG")

    def info(self, msg):
        """Logs an INFO message"""
        self.log(msg, level="INFO")

    def warning(self, msg):
        """Logs a WARNING message"""
        self.log(msg, level="WARNING")

    def error(self, msg):
        """Logs an ERROR message"""
        self.log(msg, level="ERROR")

        # Only print the traceback if an exception handler is being executed
        if sys.exc_info()[0] is not None:
            traceback.print_exc()

    def critical(self, msg):
        """Logs a CRITICAL message"""
        self.log(msg, level="CRITICAL")
        
        # Only print the traceback if an exception handler is being executed
        if sys.exc_info()[0] is not None:
            traceback.print_exc()

    def log(self, msg, level="DEBUG"):
        """Log a message

        Parameters
        ----------
        msg :
            Message to be logged.
        level : str
            Logging level."""

        # prettify
        if isinstance(msg, str):
            pass
        elif type(msg) in [dict, list, tuple]:  # TODO: should be recursive
            try:
                msg = json.dumps(msg, indent=4)
            except Exception:
                msg = str(msg)
        else:
            msg = pformat(msg)

        # actual log
        lines = msg.split("\n")
        for line in lines:
            logger.log(level, line)


    def welcome(self):
        """Welcome message in the terminal."""
        secure = "s" if get_env("CCAT_CORE_USE_SECURE_PROTOCOLS") in ("true", "1") else ""

        cat_host = get_env("CCAT_CORE_HOST")
        cat_port = get_env("CCAT_CORE_PORT")
        cat_address = f"http{secure}://{cat_host}:{cat_port}"

        from cat.utils import get_base_path
        print("\n\n")
        with open(get_base_path() + "/welcome.txt", "r") as f:
            print(f.read())

        left_margin = " " * 15
        print(f"\n\n{left_margin} Cat REST API:   {cat_address}/docs")
        print(f"{left_margin} Cat ADMIN:      {cat_address}/admin\n\n")
        # self.log_examples()


    def colored_text(self, text: str, color: str):
        """Get colored text.

        Args:
            text: The text to color.
            color: The color to use.

        Returns:
            The colored text. Supports blue, yellow, pink, green and red
        """

        colors = {
            "blue": "36;1",
            "yellow": "33;1",
            "pink": "38;5;200",
            "green": "32;1",
            "red": "31;1",
        }

        color_str = colors[color]
        return f"\u001b[{color_str}m\033[1;3m{text}\u001b[0m"


    def log_examples(self):
        """Log examples for the log engine."""

        for c in [self, "Hello there!", {"ready", "set", "go"}, [1, 4, "sdfsf"], {"a": 1, "b": {"c": 2}}]:
            self.debug(c)
            self.info(c)
            self.warning(c)
            self.error(c)
            self.critical(c)

        def intentional_error():
            print(42/0)

        try:
            intentional_error()
        except Exception:
            self.error("This error is just for demonstration purposes.")

    def langchain_log_prompt(self, langchain_prompt, title):
    
        if(get_env("CCAT_DEBUG") == "true"):
            print("\n")
            print(self.colored_text(f"===== {title} INPUT =====", "green"))
            for m in langchain_prompt.messages:
                print(self.colored_text(type(m).__name__, "green"))
                if isinstance(m.content, list):
                    for sub_m in m.content:
                        if sub_m.get("type") == "text":
                            print(sub_m["text"])
                        elif sub_m.get("type") == "image_url":
                            print("(image)")
                        else:
                            print(" -- Could not log content:", sub_m.keys())
                else:
                    print(m.content)
            print(self.colored_text("========================================", "green"))
        
        return langchain_prompt


    def langchain_log_output(self, langchain_output, title):
        if(get_env("CCAT_DEBUG") == "true"):
            print("\n")
            print(self.colored_text(f"===== {title} OUTPUT =====", "blue"))
            if hasattr(langchain_output, 'tool_calls') and len(langchain_output.tool_calls) > 0:
                for t in langchain_output.tool_calls:
                    print(f"Calling tool {t["name"]} with input {t["args"]}")
            else:
                print(langchain_output.content)
            print(self.colored_text("========================================", "blue"))
        return langchain_output
            

# logger instance
log = CatLogEngine()
