import tkinter as tk
from tkinter import ttk

from typing import Optional, Dict, Iterator
import threading

from core.components.world import World
from core.components.node import NodeCache
from core.logger import error

class GlobalState:
    status_label: tk.Label

    world: Optional[World] = None
    lock: Optional[str] = None

    struct_tree: Optional[ttk.Treeview] = None

    generators_tree: Optional[ttk.Treeview] = None

    execute_options: Optional[tk.OptionMenu] = None
    execute_selection: Optional[tk.StringVar] = None
    execute_thread: Optional[threading.Thread] = None
    execute_event: Optional[threading.Event] = None
    execute_label: Optional[tk.Label]
    execute_bar: Optional[ttk.Progressbar]
    module_cache: Dict[str, Iterator[Optional[float]]] = {}
    node_cache: NodeCache = NodeCache(16)

class LockGlobalState:
    def __init__(self, global_state: GlobalState, reason: str):
        if global_state.lock:
            error(f"Global state is currently locked for '{global_state.lock}'")
            raise RuntimeError()
        if not reason:
            error(f"LockGlobalState must have reason passed in, got None or whitespace")
        self.global_state = global_state
        self.reason = reason
    
    def __enter__(self) -> None:
        self.global_state.lock = self.reason

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.global_state.lock = None
