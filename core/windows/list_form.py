import tkinter as tk
from tkinter import BaseWidget, messagebox

from typing import Tuple, Optional, Type, List, Any, Dict, Callable
from functools import partial

from core.components.export_info import ExportInfo, Parameter
from core.windows.clusters import make_control_buttons, confirm_action
from core.logger import debug, info, error, critical
from core.globals import INNER_PADDING, OUTER_PADDING

# stuff for Parameter handling
type_to_name: Dict[Type, str] = {
    str: "string",
    int: "int",
}
name_to_type: Dict[str, Type] = { n: t for t, n in type_to_name.items() }
name_list: List[str] = [ n for n in name_to_type ]

class ListFormHolder:
    type_: Type
    index: int
    widgets: List[Dict]

    def __init__(self, root, type_: Type, type_data: Optional[Dict]):
        self.root = root
        self.type_ = type_
        self.type_data = type_data if type_data is not None else {}
        self.datas = []
        self.index = -1

        self.frame = tk.Frame(root)
        self.frame.pack(fill='x', padx=OUTER_PADDING, pady=(OUTER_PADDING, 0))
    
    def add_row(self, value): # type: ignore
        self.index += 1
        self.datas.append({})
        if self.index != len(self.datas) - 1:
            critical(f"ListFormHolder.index mismatch with len(ListFormHolder.widgets) - 1, {self.index} != {len(self.datas) - 1}")
        
        w = self.datas[self.index]
        width = 1
        stretch_col = 0
        padx = (0,INNER_PADDING)
        if self.type_ is Parameter:
            value: Parameter
            w['name_entry'] = tk.Entry(self.frame)
            w['name_entry'].insert(0, value.name)
            w['name_entry'].grid(row=self.index, column=0, sticky='ew', padx=padx)
            w['variable'] = tk.StringVar(self.frame)
            w['variable'].set(type_to_name[value.type_])
            w['type_drop'] = tk.OptionMenu(self.frame, w['variable'], *name_list)
            w['type_drop'].grid(row=self.index, column=1, sticky='ew', padx=padx)
            width = 2
        elif self.type_ is str:
            w['variable'] = tk.StringVar(self.frame, value)
            if 'options' in self.type_data:
                w['str_drop'] = tk.OptionMenu(self.frame, w['variable'], *self.type_data['options'])
                w['str_drop'].grid(row=self.index, column=0, sticky='ew', padx=padx)
            else:
                critical(f"type {self.type_} does not have add_row procedure without 'options' in type_data")
                return
        else:
            critical(f"type {self.type_} does not have add_row procedure")
            return
        
        if self.index == 0:
            self.frame.columnconfigure(stretch_col, weight=1)
        confirm_text = "Are you sure you want to delete this parameter? This action can not be undone."
        index = self.index
        remove_func = lambda: confirm_action(confirm_text, lambda: self.remove_row(index))
        w['remove_button'] = tk.Button(self.frame, text=" - ", command=remove_func)
        w['remove_button'].grid(row=self.index, column=width, sticky='ew', pady=(0,INNER_PADDING))
    
    def remove_row(self, index: int):
        for i in range(index, len(self.datas) - 1):
            if self.type_ is Parameter:
                self.datas[i]['variable'].set(self.datas[i+1]['variable'].get())
                e: tk.Entry = self.datas[i]['name_entry']
                e.delete(0, len(e.get()))
                e.insert(0, self.datas[i+1]['name_entry'].get())
            elif self.type_ is str:
                self.datas[i]['variable'].set(self.datas[i+1]['variable'].get())
            else:
                critical(f"type {self.type_} does not have remove_row procedure")
                return
        
        for key in self.datas[-1]:
            if key in ['variable']:
                continue
            self.datas[-1][key].destroy()
        
        self.index -= 1
        del self.datas[-1]
    
    def extract_list(self):
        l = []
        for w in self.datas:
            if self.type_ is Parameter:
                l.append(Parameter(w['name_entry'].get(),
                                   name_to_type[w['variable'].get()]))
            elif self.type_ is str:
                l.append(w['variable'].get())
            else:
                critical(f"type {self.type_} does not have extract_list procedure")
        return l

def _try_save(root: tk.Toplevel, holder: ListFormHolder):
    l = holder.extract_list()

    if l:
        root.saved = l # type: ignore
        root.destroy()

def prompt_list_form(parent, list_: List, export_info: ExportInfo) -> Optional[List]:
    root = tk.Toplevel(parent)
    root.saved = False # type: ignore
    root.title(f"Edit List")
    
    holder = ListFormHolder(root, export_info.type_, export_info.data)
    for value in list_:
        holder.add_row(value)

    add_button = tk.Button(root, text="New Entry", command=lambda: holder.add_row(export_info.default()))
    add_button.pack()

    make_control_buttons(root, save_func=lambda: _try_save(root, holder), cancel_func=root.destroy).pack(side="bottom", pady=OUTER_PADDING)

    root.geometry(f"400x400")
    root.transient(parent)
    root.grab_set()
    parent.wait_window(root)

    if root.saved: # type: ignore
        return root.saved # type: ignore
    return None
