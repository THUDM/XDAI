"""
provide logger module.
Any other modules in "hua should use "logger" from this module
to log messages.
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path


project_path = Path(__file__).parent.parent

def get_logger(name: str, classname: str = "") -> logging.Logger:
    """
    configured Loggers
    """
    if not classname:
        classname = name
    base_dir = project_path
    log_base_dir = os.path.join(base_dir, "logs")

    if not name:
        name = "chatbot"

    log_dir = os.path.join(log_base_dir, f"{name}_logs")

    for the_dir in [log_base_dir, log_dir]:
        if not os.path.exists(the_dir):
            os.mkdir(the_dir)

    CHATBOT_LOG_LEVEL = "INFO"

    log_formatter = logging.Formatter(
        fmt="[%(asctime)s %(name)s] %(levelname)s: %(message)s"
    )

    # create logger and set level to debug
    logger = logging.getLogger(name)
    logger.handlers = []
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    time_now = datetime.now()
    time_format = "%Y-%m-%d-%H"
    filepath = os.path.join(log_dir, f"log-{time_now.strftime(time_format)}.txt")

    file_handler = logging.FileHandler(filepath, "a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(CHATBOT_LOG_LEVEL)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    return logger


# logger = get_logger("xiaodai")
logger = get_logger("XDAI")
__all__ = ["get_logger", "logger"]
