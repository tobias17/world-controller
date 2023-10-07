from tkinter import messagebox

import datetime
import os

from core.windows.main_window import create_root
from core.globals import LOG_DIRNAME
from core import logger


# TODO
# [X] Make generator that uses LLM
# [X] Progress bar and executor status label update code needs to be implemented
# [X] Add .gitignore file and push changes
# [ ] When closing the window, executor's still go on
# [ ] Standalone executor script needs to be made and tested
# [ ] Struct dirpath and name variables need to be combined
# [ ] Struct name changes break things
# [ ] Node pointer types need to be defined and implemented
# [ ] Investigate and "Open File" button for generators


#########################
#   Set up the logger   #
#########################

if not os.path.exists(LOG_DIRNAME):
    os.mkdir(LOG_DIRNAME)
log_filepath = os.path.join(LOG_DIRNAME, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))

def save_log(info: logger.LogInfo) -> None:
    with open(log_filepath, "a") as f:
        f.write(f"[{info.time}] {info.level.value.upper()}: {info.message}\n")
logger.add_action(save_log, levels=logger.ALL_LEVELS)

def print_log(info: logger.LogInfo) -> None:
    text = f"{info.level.value.upper()}: {info.message}"
    if info.level in [logger.Levels.CRITICAL]:
        trace = f"{info.level.value} occured"
        for layer in info.stack[::-1]:
            trace += f'\n   Filename "{layer.filename}", line {layer.lineno}\n      >>> {layer.code_context[0].strip() if layer.code_context else ""}'
        text = f"{trace}\n{text}\n"
    print(text)
logger.add_action(print_log, levels=logger.ALL_LEVELS)

logger.add_action(lambda info: messagebox.showwarning(info.level.value, info.message), [logger.Levels.WARNING])
logger.add_action(lambda info: messagebox.showerror(info.level.value, info.message), [logger.Levels.ERROR])
logger.add_action(lambda info: messagebox.showerror(info.level.value, f"CRITICAL: {info.message}"), [logger.Levels.CRITICAL])


##########################
#     Launch the app     #
##########################

root = create_root()
root.mainloop()
