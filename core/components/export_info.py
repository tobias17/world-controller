from typing import Optional, Type, Tuple, Any, Dict, List, Callable

from core.logger import error

class Parameter:
    TO_DICT: bool = True
    name:  str
    type_: type
    def __init__(self, name: str, type_: type):
        self.name  = name
        self.type_ = type_
    def to_dict(self):
        return { 'name': self.name, 'type': type_to_int[self.type_] }
    @staticmethod
    def from_dict(dict: Dict) -> Optional['Parameter']:
        if 'name' not in dict:             error(f"did not find key 'name' in dictionary when loading Parameters"); return None
        if type(dict['name']) is not str:  error(f"'name' value was of type {type(dict['name'])} when trying to load Parameters, expected string"); return None
        if 'type' not in dict:             error(f"did not find key 'name' in dictionary when loading Parameters"); return None
        if type(dict['type']) is not int:  error(f"'type' value was of type {type(dict['type'])} when trying to load Parameters, expected int"); return None

        return Parameter(dict['name'], int_to_type[dict['type']])

class DirPath: pass
class FilePath: pass

type_to_int = {
    str: 0,
    int: 1,
    DirPath: 2,
    FilePath: 3,
    Parameter: 4,
}
int_to_type = { v: k for k, v in type_to_int.items() }

def dictize(obj):
    if type(obj) is list:
        return [dictize(o) for o in obj]
    if hasattr(obj, 'TO_DICT'):
        return obj.to_dict()
    return obj

default_values = {
    str: lambda: "",
    int: lambda: 0,
    DirPath: lambda: "",
    Parameter: lambda: Parameter("new_parameter", str),
    Dict: lambda: dict(),
    List: lambda: list(),
}

class ExportInfo:
    name: str
    type_: Type
    default: Callable[[], Any]
    child: Optional['ExportInfo']
    data: Optional[Dict] = None

    def __init__(self, name: str, type_: Type, default: Optional[Callable[[], Any]]=None, child: Optional['ExportInfo']=None):
        self.name = name
        self.type_ = type_
        self.default = default if default is not None else default_values[type_]
        self.child = child
