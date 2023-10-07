import tkinter as tk
from tkinter import ttk, messagebox

from typing import Tuple
import os

from core.windows.generic_form import prompt_edit_form
from core.components.struct import Struct
from core.globals import OUTER_PADDING, INSTANCES_DIRNAME
from core.logger import error, critical
from core import globals

from .shared import GlobalState


def _create_struct_checks(struct) -> bool:
    if len(os.listdir(struct.dirpath)) > 0:
        error("dirpath needs to be empty to create a new struct.")
        return False
    return struct.is_valid()

def new_struct(root: tk.Tk, global_state: GlobalState):
    if global_state.lock:
        error(f"Cannot create structs when global state is locked for '{global_state.lock}'")
        return
    world = global_state.world
    if not world:
        error("A world needs to be loaded to create structs.")
        return
    
    struct = Struct.empty_object(world_dirpath=global_state.world.dirpath) # type: ignore
    struct.dirpath = f"{world.dirpath}/{globals.STRUCT_DIRNAME}"
    updated_struct = prompt_edit_form(root, struct, _create_struct_checks)
    if not updated_struct:
        return
    struct: Struct = updated_struct # type: ignore

    struct.save()
    world.structs.append(struct)
    world.struct_paths.append(struct.dirpath)
    world.save()

    update_struct_table(global_state)

def _edit_table_item(event: tk.Event, root: tk.Tk, tree: ttk.Treeview, global_state: GlobalState) -> None:
    if global_state.lock:
        error(f"Cannot edit structs when global state is locked for '{global_state.lock}'")
        return
    if not global_state.world:
        return

    item = tree.identify_row(event.y)
    if not item:
        return
    
    index = int(item[1:], base=16) - 1
    if index >= len(global_state.world.structs):
        critical(f"index ({index}) out of range for global_state.world.structs (len={len(global_state.world.structs)})")
    struct = global_state.world.structs[index]
    updated_struct = prompt_edit_form(root, struct.copy(), lambda s: s.is_valid()) # type: ignore
    if not updated_struct:
        return
    struct: Struct = updated_struct # type: ignore

    struct.save()
    global_state.world.structs.append(struct)
    global_state.world.struct_paths.append(struct.dirpath)
    global_state.world.save()

    update_struct_table(global_state)

def make_struct_table(root, global_state: GlobalState) -> None:
    columns = ("Name", "Parameters", "Instances", "Path")
    tree = ttk.Treeview(root, columns=columns, show="headings")
    for index, text in enumerate(columns):
        tree.heading(f"#{index + 1}", text=text)
    tree.pack(fill="both", padx=OUTER_PADDING, pady=(OUTER_PADDING, 0), expand=True)
    tree.bind("<Double-1>", lambda event: _edit_table_item(event, root, tree, global_state))

    button = tk.Button(root, text="New Struct", command=lambda: new_struct(root, global_state))
    button.pack(pady=OUTER_PADDING)

    global_state.struct_tree = tree

def update_struct_table(global_state: GlobalState) -> None:
    if global_state.struct_tree and global_state.world:
        for item in global_state.struct_tree.get_children():
            global_state.struct_tree.delete(item)
        for struct in global_state.world.structs:
            inst_dirpath = f"{struct.dirpath}/{INSTANCES_DIRNAME}"
            if not os.path.isdir(inst_dirpath):
                inst_count = 0
                response = messagebox.askyesno("No Struct Instance Root", f"Failed to find instance root folder for Struct {struct.name} at:\n{inst_dirpath}\n\nCreate a new instance root folder?")
                if response:
                    os.mkdir(inst_dirpath)
            else:
                inst_count = len([f for f in os.listdir() if f.endswith(".json")])
            global_state.struct_tree.insert("", "end", values=(struct.name, len(struct.parameters), inst_count, struct.dirpath.replace(global_state.world.dirpath, "")))
