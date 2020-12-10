#!/usr/bin/env python3

"""
Standardises logger across scripts automatically

Invoke with the following

from umccr_utils.logger import get_logger

logger = get_logger()
"""

import logging
import inspect

# Logger styles
CONSOLE_LOGGER_STYLE = '%(asctime)s %(funcName)-25s: %(levelname)-8s %(message)s'
LOGGER_DATEFMT = '%y-%m-%d %H:%M:%S'


def get_caller_function():
    """
    Get the function that was used to call the previous
    Some loggers report <module>

    :return:
    """
    # Get the inspect stack trace
    inspect_stack = inspect.stack()

    # Since we're already in a function, we need the third attribute
    # i.e function of interest -> function that called this one -> this function
    frame_info = inspect_stack[2]

    # Required attribute is' function
    function_id = getattr(frame_info, "function", None)

    if function_id is None:
        # Don't really want to break on this just yet but code is ready to go for it.
        return None
    else:
        return function_id


def initialise_logger():
    """
    Return the logger in a nice logging format
    :return:
    """
    # Initialise logger
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter(CONSOLE_LOGGER_STYLE, datefmt=LOGGER_DATEFMT)
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(console)


def get_logger():
    """
    Get the name of where this function was called from - return a logging object
    Use a trackback from the inspect to do this
    :return:
    """
    function_that_called_this_one = get_caller_function()
    return logging.getLogger(function_that_called_this_one)
