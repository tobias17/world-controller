import tkinter as tk
from tkinter import ttk

import os

from core.windows.generic_form import prompt_edit_form
from core.components.generator_info import GeneratorInfo
from core.logger import error, critical
from core.globals import OUTER_PADDING

from .shared import GlobalState
from .execute_tab import update_execute_options

def _generator_checks(generator, is_new: bool, global_state: GlobalState) -> bool:
    if not global_state.world:
        critical("global_state.world was not set when entering _generator_checks")
        return False
    
    filepath = generator.get_filepath(global_state.world.dirpath)
    if is_new and os.path.exists(filepath):
        error("Generator file can not already exist")
        return False
    if not is_new and not os.path.exists(filepath):
        error(f"Could not find geenrator file at {filepath}")
        return False
    return generator.is_valid()

def _bind_generator_info_options(global_state: GlobalState):
    options = [s.name for s in global_state.world.structs] # type: ignore
    if len(options) == 0:
        error("Can not create generators with 0 structs defined")
    [p for p in GeneratorInfo.PARAM_LIST if p.name == "input_struct_names"][0].child.data = { "options": options } # type: ignore

def _new_generator(root: tk.Tk, global_state: GlobalState):
    if global_state.lock:
        error(f"Cannot create generators when global state is locked for '{global_state.lock}'")
        return
    world = global_state.world
    if not world:
        error("A world needs to be loaded to create generators.")
        return
    
    info = GeneratorInfo.empty_object()
    _bind_generator_info_options(global_state)
    updated_info = prompt_edit_form(root, info, lambda g: _generator_checks(g, True, global_state))
    if not updated_info:
        return
    info: GeneratorInfo = updated_info # type: ignore

    world.generators.append(info)
    world.save()
    info.create_file(world.dirpath)

    update_generator_table(global_state)
    update_execute_options(global_state)

def _edit_table_item(event: tk.Event, root: tk.Tk, tree: ttk.Treeview, global_state: GlobalState) -> None:
    if global_state.lock:
        error(f"Cannot edit generators when global state is locked for '{global_state.lock}'")
        return
    if not global_state.world:
        return

    item = tree.identify_row(event.y)
    if not item:
        return
    
    index = int(item[1:], base=16) - 1
    if index >= len(global_state.world.generators):
        critical(f"index ({index}) out of range for global_state.world.generators (len={len(global_state.world.generators)})")
    generator: GeneratorInfo = global_state.world.generators[index].copy()
    _bind_generator_info_options(global_state)
    updated_generator = prompt_edit_form(root, generator, lambda f: _generator_checks(f, False, global_state))
    if not updated_generator:
        return
    generator: GeneratorInfo = updated_generator # type: ignore

    global_state.world.generators.append(generator)
    global_state.world.save()

    update_generator_table(global_state)
    update_execute_options(global_state)

def make_generator_table(root, global_state: GlobalState) -> None:
    columns = ("Filename", "Inputs")
    tree = ttk.Treeview(root, columns=columns, show="headings")
    for index, text in enumerate(columns):
        tree.heading(f"#{index + 1}", text=text)
    tree.pack(fill="both", padx=OUTER_PADDING, pady=(OUTER_PADDING, 0), expand=True)
    tree.bind("<Double-1>", lambda event: _edit_table_item(event, root, tree, global_state))

    button = tk.Button(root, text="New Generator", command=lambda: _new_generator(root, global_state))
    button.pack(pady=OUTER_PADDING)

    global_state.generators_tree = tree

def update_generator_table(global_state: GlobalState) -> None:
    if not global_state.generators_tree or not global_state.world:
        return

    for item in global_state.generators_tree.get_children():
        global_state.generators_tree.delete(item)
    for generator in global_state.world.generators:
        global_state.generators_tree.insert("", "end", values=(generator.filename, len(generator.input_struct_names)))
