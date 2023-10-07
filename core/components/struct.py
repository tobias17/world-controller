from typing import Tuple, Optional, List
import json
import os
import re

from core.components.export_info import ExportInfo, DirPath, Parameter, dictize
from core.components.formable import Formable
from core.components.node import generate_node_text
from core.globals import USERCODE_DIRNAME, USERCODE_TYPES_DIRNAME
from core.logger import error
from core.utils import check_name

class Struct(Formable):
    SETTINGS_FILENAME = "struct.json"
    PARAM_LIST = [
        ExportInfo("dirpath",    DirPath),
        ExportInfo("name",       str),
        ExportInfo("parameters", List, child=ExportInfo("parameters", Parameter)),
    ]
    REQUIRED = ["world_dirpath"]

    # load_struct() sets these
    world_dirpath: str
    dirpath: str

    # from_json() sets these
    name: str
    parameters: List[Parameter]

    def save(self) -> None:
        exlclude_list = ["dirpath"]
        export_data = { k:dictize(v) for k,v in self.__dict__.items() if k not in exlclude_list }
        with open(f"{self.dirpath}/{Struct.SETTINGS_FILENAME}", 'w') as f:
            json.dump(export_data, f)
        with open(f"{self.world_dirpath}/{USERCODE_DIRNAME}/{USERCODE_TYPES_DIRNAME}/{self.name}.py", "w") as f:
            f.write(generate_node_text(self.name, self.parameters))

    def is_valid(self) -> bool:
        if not os.path.isdir(self.dirpath):
            error(f"'{self.dirpath}' is not valid directory path")
            return False
        if not check_name(self.name):
            return False
        return True

    def copy(self) -> 'Struct':
        struct = Struct()
        for export_info in Struct.PARAM_LIST:
            setattr(struct, export_info.name, getattr(self, export_info.name))
        return struct

def load_struct(path: str, world_dirpath: str) -> Optional[Struct]:
    struct = Struct()
    struct.dirpath = path
    struct.world_dirpath = world_dirpath

    settings_filepath = f"{path}/{Struct.SETTINGS_FILENAME}"
    if not os.path.exists(settings_filepath):
        error(f"Could not find {Struct.SETTINGS_FILENAME} file, searched {settings_filepath}")
        return None
    with open(settings_filepath) as f:
        json_data = json.load(f)
        for k, v in json_data.items():
            if k == "parameters":
                v = [Parameter.from_dict(d) for d in v]
            setattr(struct, k, v)

    return struct
