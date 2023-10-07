from typing import Dict, List, Callable, Any
from enum import Enum
from datetime import datetime
import inspect

class Levels(Enum):
    DEBUG    = "Debug"
    INFO     = "Info"
    WARNING  = "Warning"
    ERROR    = "Error"
    CRITICAL = "Critical"

ALL_LEVELS = [Levels.DEBUG, Levels.INFO, Levels.WARNING, Levels.ERROR, Levels.CRITICAL]

class LogInfo:
    message: str
    level: Levels
    time: str
    stack: List[inspect.FrameInfo]
    def __init__(self, message: str, level: Levels, stack_delta: int=3):
        self.message = message
        self.level = level
        self.time = datetime.now().strftime("%H:%M:%S")
        self.stack = inspect.stack()[stack_delta:]

actions: Dict[Levels, List[Callable[[LogInfo], Any]]] = { }

def add_action(action: Callable[[LogInfo], Any], levels: List[Levels]):
    for level in levels:
        if level not in actions:
            actions[level] = []
        actions[level].append(action)

def _generic_log(message: str, level: Levels):
    if level in actions:
        info = LogInfo(message, level)
        for action in actions[level]:
            action(info)


def debug(message: str)    -> str: _generic_log(message, Levels.DEBUG)   ; return message
def info(message: str)     -> str: _generic_log(message, Levels.INFO)    ; return message
def warning(message: str)  -> str: _generic_log(message, Levels.WARNING) ; return message
def error(message: str)    -> str: _generic_log(message, Levels.ERROR)   ; return message
def critical(message: str) -> str: _generic_log(message, Levels.CRITICAL); return message
