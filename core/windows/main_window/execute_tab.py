import tkinter as tk
from tkinter import ttk


from enum import IntEnum, auto
import threading

from core.components.executor import create_executor
from core.logger import info, error, critical
from core.globals import OUTER_PADDING, INNER_PADDING
from .shared import GlobalState, LockGlobalState

class ExecuteType(IntEnum):
    SINGLE_SHOT = auto()
    SET_AMOUNT  = auto()
    UNLIMITED   = auto()

def _start_executor(global_state: GlobalState, execute_type: tk.IntVar, set_amount_count: tk.Entry):
    if not global_state.world:
        error("Cannot start executor wiht no world loaded")
        return
    if global_state.execute_thread:
        if not global_state.execute_thread.is_alive():
            global_state.execute_thread = None
        else:
            error("Executor thread is already running, stop or terminate the current thread to start a new one")
            return
    if global_state.lock:
        error(f"Cannot start executor when global state is locked for '{global_state.lock}'")
        return
    if not global_state.execute_selection:
        critical("global_state.execute_selection was None when _start_executor was called")
        return
    
    generator_name = global_state.execute_selection.get()
    if not generator_name:
        error("Generator function must be selected to start executor")
        return

    # figure out how many times we should run the generator
    ex_type: int = execute_type.get()
    if ex_type == ExecuteType.SINGLE_SHOT:
        execute_count = 1
    elif ex_type == ExecuteType.SET_AMOUNT:
        count_string = set_amount_count.get()
        if not count_string.isdigit():
            error(f"Execute set amount count '{count_string}' is not a number")
            return
        execute_count = int(count_string)
        if execute_count <= 0:
            error(f"Execute set amount count must be >= 1, got '{execute_count}'")
            return
    elif ex_type == ExecuteType.UNLIMITED:
        execute_count = -1
    else:
        critical(f"Got unsupported ExecuteType {ex_type}")
        return

    try:
        def _on_update(progress: float) -> None:
            if global_state.execute_bar and progress is not None:
                if progress == -1:
                    global_state.execute_bar['mode'] = 'indeterminate'
                    global_state.execute_bar.start()
                    info(f"indeterminate: {progress}")
                else:
                    global_state.execute_bar['mode'] = 'determinate'
                    global_state.execute_bar.stop()
                    global_state.execute_bar['value'] = progress * 100
                    info(f"determinate: {progress}")

        thread, event = create_executor(execute_count, global_state.world, generator_name, global_state.module_cache, global_state.node_cache, _on_update)
        if not thread or not event:
            return
        global_state.execute_event = event
    
        def _thread_wrapper():
            if global_state.execute_label:
                global_state.execute_label.config(text=f"Executing {generator_name}...")
            with LockGlobalState(global_state, "Executing Generator"):
                thread.start()
                thread.join()
                if global_state.execute_label:
                    global_state.execute_label.config(text=f"Finished executing {generator_name}")

        global_state.execute_thread = threading.Thread(target=_thread_wrapper)
        global_state.execute_thread.start()
    except Exception as ex:
        global_state.execute_thread = None
        error(f"Exception occured starting executor -> {ex}")
        raise ex from ex
    
def _stop_executor(global_state: GlobalState):
    if not global_state.execute_thread:
        error("No executor thread running to stop")
        return
    if not global_state.world:
        critical("Thread was started with no world loaded")
        return
    if not global_state.execute_event:
        critical("global_state.execute_event was None when trying to _stop_executor")
        return
    
    global_state.execute_event.set()

def _reload_selected_module_cache(global_state: GlobalState):
    if not global_state.execute_selection:
        critical("global_state.execute_selection was None when entering _reload_selected_generator_cache")
        return
    gen_name = global_state.execute_selection.get()
    if gen_name in global_state.module_cache:
        del global_state.module_cache[gen_name]
        info(f"Reloaded {gen_name}")
    else:
        info(f"{gen_name} was not loaded, skipping reload")

def make_execute_tab(root: tk.Frame, global_state: GlobalState):
    # add widgets for selecting which generator to run
    selection_frame = tk.Frame(root)
    tk.Label(selection_frame, text="Generator").grid(row=0, column=0, padx=(0,INNER_PADDING))
    global_state.execute_selection = tk.StringVar(root, "")
    options = [""]
    global_state.execute_options = tk.OptionMenu(selection_frame, global_state.execute_selection, *options)
    global_state.execute_options.grid(row=0, column=1, padx=(0,INNER_PADDING))
    tk.Button(selection_frame, text="Reload", command=lambda: _reload_selected_module_cache(global_state)).grid(row=0, column=2)
    selection_frame.pack(pady=(OUTER_PADDING,INNER_PADDING))

    # add widgets for selecting execution type
    execute_type_frame = tk.Frame(root)
    execute_type = tk.IntVar(root, value=ExecuteType.SINGLE_SHOT.value)
    tk.Radiobutton(execute_type_frame, text="Single Shot", variable=execute_type, value=ExecuteType.SINGLE_SHOT.value).grid(row=0, column=0, sticky='w', pady=(0,INNER_PADDING))
    tk.Radiobutton(execute_type_frame, text="Set Amount", variable=execute_type, value=ExecuteType.SET_AMOUNT.value).grid(row=1, column=0, sticky='w', padx=(0,INNER_PADDING), pady=(0,INNER_PADDING))
    set_amount_count = tk.Entry(execute_type_frame)
    set_amount_count.grid(row=1, column=1)
    tk.Radiobutton(execute_type_frame, text="Unlimited", variable=execute_type, value=ExecuteType.UNLIMITED.value).grid(row=2, column=0, sticky='w', pady=(0,INNER_PADDING))
    execute_type_frame.pack()

    # add widgets for starting and stopping execution
    control_frame = tk.Frame(root)
    tk.Button(control_frame, text="Start Executor", command=lambda: _start_executor(global_state, execute_type, set_amount_count)).grid(row=0, column=0, padx=(0,INNER_PADDING))
    tk.Button(control_frame, text="Stop Executor", command=lambda: _stop_executor(global_state)).grid(row=0, column=1)
    control_frame.pack()

    # add widgets for displaying the execution state
    global_state.execute_label = tk.Label(root, text="waiting for executor")
    global_state.execute_label.pack(pady=(OUTER_PADDING,INNER_PADDING))
    global_state.execute_bar = ttk.Progressbar(root, length=500, mode="determinate")
    global_state.execute_bar.pack(padx=OUTER_PADDING)

def update_execute_options(global_state: GlobalState):
    if not global_state.world or not global_state.execute_options or not global_state.execute_selection:
        error("Can not update execute options when no world is loaded")
        return
    
    global_state.execute_options['menu'].delete(0, 'end')
    found = False
    for generator in global_state.world.generators:
        choice = generator.filename
        global_state.execute_options['menu'].add_command(label=choice, command=tk._setit(global_state.execute_selection, choice))
        if choice == global_state.execute_selection.get():
            found = True
    if not found:
        global_state.execute_selection.set("")
