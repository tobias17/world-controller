import tkinter as tk
from tkinter import filedialog, ttk

import os

from core.components.world import World, load_world
from core.logger import error
from core import globals

from .struct_tab import make_struct_table, update_struct_table
from .generator_tab import make_generator_table, update_generator_table
from .execute_tab import make_execute_tab, update_execute_options
from .shared import GlobalState

def _try_load_world_state(global_state: GlobalState, root_path: str):
    world = load_world(root_path)
    if not world:
        return

    global_state.world = world
    global_state.status_label.config(text="Successfully loaded World")
    update_struct_table(global_state)
    update_generator_table(global_state)
    update_execute_options(global_state)

def _create_project(global_state: GlobalState):
    if global_state.lock:
        error(f"Cannot create projects when global state is locked for '{global_state.lock}'")
        return
    try:
        folder_path = filedialog.askdirectory(
            initialdir=globals.WORLD_DIRNAME,
            title="Select Empty Directory to be World Root",
        )
        if not folder_path:
            return
        
        if len(os.listdir(folder_path)) > 0:
            error("Directory needs to be empty to create a new world.")
            return
        
        World.empty_world(folder_path).save()
        structs_dirpath = f"{folder_path}/{globals.STRUCT_DIRNAME}"
        os.mkdir(structs_dirpath)
        with open(f"{structs_dirpath}/Put struct roots here.txt", 'w'):
            pass
        for dirname in globals.USERCODE_SUBDIRS:
            os.makedirs(f"{folder_path}/{globals.USERCODE_DIRNAME}/{dirname}")
        with open(f"{folder_path}/{globals.USERCODE_DIRNAME}/{globals.USERCODE_GENERATORS_DIRNAME}/Put user defined generators here.txt", 'w'):
            pass
        # TODO: do we need __init__.py files?
        # with open(f"{folder_path}/{globals.USERCODE_DIRNAME}/__init__.py", 'w') as f:
        #     f.write(f"import .{globals.USERCODE_TYPES_DIRNAME} as {globals.USERCODE_TYPES_DIRNAME}\nimport .{globals.USERCODE_GENERATORS_DIRNAME} as {globals.USERCODE_GENERATORS_DIRNAME}\n")
        
        _try_load_world_state(global_state, folder_path)
    except Exception as ex:
        error(f"Exception occured creating World:\n{ex}")

def _load_project(global_state: GlobalState):
    if global_state.lock:
        error(f"Cannot load projects when global state is locked for '{global_state.lock}'")
        return
    folder_path = filedialog.askdirectory(
        initialdir=globals.WORLD_DIRNAME,
        title="Select the World Root Directory",
    )
    if not folder_path:
        return
    
    _try_load_world_state(global_state, folder_path)

def make_menu_bar(root: tk.Tk, global_state: GlobalState) -> None:
    menu_bar = tk.Menu(root)

    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="New world",  command=lambda: _create_project(global_state))
    file_menu.add_command(label="Load world", command=lambda: _load_project(global_state))

    root.config(menu=menu_bar)

def create_root() -> tk.Tk:
    root = tk.Tk()

    root.geometry("800x500")
    root.title("World Controller")
    global_state = GlobalState()

    make_menu_bar(root, global_state)

    notebook = ttk.Notebook(root)

    struct_frame = tk.Frame(notebook)
    global_state.status_label = tk.Label(notebook, text="No World loaded, to load one head to 'File > Load world'")
    # global_state.status_label.pack()
    make_struct_table(struct_frame, global_state)
    notebook.add(struct_frame, text="Edit Structs")

    generator_frame = tk.Frame(notebook)
    make_generator_table(generator_frame, global_state)
    notebook.add(generator_frame, text="Generators")

    execute_frame = tk.Frame(notebook)
    make_execute_tab(execute_frame, global_state)
    notebook.add(execute_frame, text="Execute")

    notebook.pack(fill="both", expand=True)
    return root
