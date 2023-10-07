import tkinter as tk
from tkinter import BaseWidget, filedialog

from typing import Optional, Dict, Callable, List, Type, Any
import os

from core.components.export_info import ExportInfo, DirPath
from core.components.formable import Formable
from core.windows.list_form import prompt_list_form
from core.windows.clusters import make_control_buttons
from core.logger import error
from core.globals import INNER_PADDING, OUTER_PADDING

LINE_SIZE    = 20
LABEL_OFFSET = 10

def _choose_path(entry: tk.Entry, is_file: bool):
    if is_file:
        raise NotImplementedError()
    else:
        value = entry.get()
        kwargs: Dict[str, str] = { "title": "Choose a path" }
        if os.path.isdir(value):
            kwargs["initialdir"] = value
        path = filedialog.askdirectory(**kwargs) # type: ignore
        if path:
            entry.delete(0, len(entry.get()))
            entry.insert(0, path)

def _edit_list(parent: BaseWidget, data: Dict, export_info: ExportInfo):
    new_list = prompt_list_form(parent, [v for v in data['list']], export_info)
    if not new_list:
        return
    data['list'] = new_list


ExtraChecks = Callable[[Formable], bool]

def _try_save(root: tk.Toplevel, obj: Formable, entry_data: Dict, extra_checks: ExtraChecks):
    for export_info in obj.PARAM_LIST:
        if export_info.type_ in [str, DirPath]:
            value = entry_data[export_info.name]['entry'].get()
            if export_info.type_ == DirPath and not os.path.exists(value):
                error(f"'{export_info.name}' is not valid directory path")
                return
            setattr(obj, export_info.name, value)
        elif export_info.type_ == List:
            setattr(obj, export_info.name, entry_data[export_info.name]['list'])
        else:
            raise NotImplementedError(f"Do not know how to process {export_info.type_}")
    
    is_good = extra_checks(obj)
    if not is_good:
        return

    root.saved = True # type: ignore
    root.destroy()

def prompt_edit_form(parent: tk.Tk, obj: Formable, extra_checks: ExtraChecks=lambda _: True) -> Optional[Formable]:
    root = tk.Toplevel(parent)
    root.saved = False # type: ignore
    root.title(f"Edit {obj.__class__.__name__}")

    entry_data = { }
    frame_holder = tk.Frame(root)
    label_holder = tk.Frame(frame_holder)
    entry_holder = tk.Frame(frame_holder)
    for index, export_info in enumerate(obj.PARAM_LIST):
        entry_row = tk.Frame(entry_holder)

        row_data = {}
        if export_info.type_ == str:
            entry = tk.Entry(entry_row)
            entry.insert(0, getattr(obj, export_info.name))
            entry.grid(row=0, column=0, sticky="ew", padx=(INNER_PADDING, 0))
            row_data['entry'] = entry
        elif export_info.type_ == List:
            if export_info.child is None:
                error(f"Parameter '{export_info.name}' in PARAM_LIST was type List without a child type assigned")
                return None
            row_data['list'] = getattr(obj, export_info.name)
            default = export_info.default
            button = tk.Button(entry_row, text=f"Edit {export_info.name}", command=lambda d=row_data, e=export_info.child: _edit_list(root, d, e))
            button.grid(row=0, column=0)
        elif export_info.type_ == DirPath:
            entry = tk.Entry(entry_row)
            entry.insert(0, getattr(obj, export_info.name))
            button = tk.Button(entry_row, text="Choose", command=lambda entry=entry: _choose_path(entry, False))
            button.grid(row=0, column=1, sticky="e", padx=(INNER_PADDING, 0))
            entry.grid(row=0, column=0, sticky="ew", padx=(INNER_PADDING, 0))
            row_data['entry'] = entry
        else:
            raise NotImplementedError(f"Do not know how to process {export_info.type_}")
        entry_data[export_info.name] = row_data

        label = tk.Label(label_holder, text=export_info.name)
        label.grid(row=index, column=0, sticky="w", pady=(0, LABEL_OFFSET))
        entry_row.columnconfigure(0, weight=1)
        entry_row.grid(row=index, column=0, stick="nsew", pady=(0 if index==0 else (INNER_PADDING, 0)))
        entry_holder.rowconfigure(index, weight=1)
    
    label_holder.grid(row=0, column=0, sticky="w")
    entry_holder.columnconfigure(0, weight=1)
    entry_holder.grid(row=0, column=1, sticky="nsew")
    frame_holder.columnconfigure(1, weight=1)
    frame_holder.pack(fill="x", padx=OUTER_PADDING, pady=OUTER_PADDING)

    make_control_buttons(root, save_func=lambda: _try_save(root, obj, entry_data, extra_checks), cancel_func=root.destroy).pack()

    root.geometry(f"800x{(LINE_SIZE+INNER_PADDING+LABEL_OFFSET)*(len(obj.PARAM_LIST))+LINE_SIZE+OUTER_PADDING*3}")
    root.transient(parent)
    root.grab_set()
    parent.wait_window(root)

    return obj if root.saved==True else None # type: ignore
