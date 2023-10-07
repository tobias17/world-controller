import tkinter as tk
from tkinter import messagebox

from typing import Callable, Any

from core.globals import INNER_PADDING

def confirm_action(message: str, func: Callable):
    did_confirm = messagebox.askyesno(title="Confirmation", message=message)
    if did_confirm:
        func()

def make_control_buttons(root: Any, save_func: Callable[[], None], cancel_func: Callable[[], None]) -> tk.Frame:
    frame = tk.Frame(root)
    save_button = tk.Button(frame, text="Save", command=save_func)
    save_button.grid(row=0, column=0, padx=(0,INNER_PADDING))
    cancel_button = tk.Button(frame, text="Cancel", command=cancel_func)
    cancel_button.grid(row=0, column=1)
    return frame
