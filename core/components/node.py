from typing import Dict, List, TypeVar, Type
import json
import uuid
import time
import os

from core.components.export_info import Parameter
from core.utils import file_to_class_name
from core.logger import error
from core.globals import STRUCT_DIRNAME, INSTANCES_DIRNAME

T = TypeVar('T')

class CacheLine:
    data: Dict
    time: float

class NodeCache:
    __max_size: int
    __cache: Dict[str, CacheLine]

    def __init__(self, max_size: int):
        if max_size < 1:
            raise ValueError(f"Tried creating cache with max_size {max_size}, must be >= 1")
        self.__max_size = max_size
        self.__cache = {}

    def contains(self, path_on_disk: str) -> bool:
        return path_on_disk in self.__cache

    def retrieve(self, path_on_disk: str) -> Dict:
        cache_line = self.__cache[path_on_disk]
        cache_line.time = time.time()
        return cache_line.data
    
    def store(self, path_on_disk: str, data: Dict) -> None:
        if path_on_disk in self.__cache:
            cache_line = self.__cache[path_on_disk]
        else:
            cache_line = CacheLine()
            self.__cache[path_on_disk] = cache_line
        cache_line.time = time.time()
        cache_line.data = data

        if len(self.__cache) > self.__max_size:
            earliest_key  = None
            earliest_time = 0
            for key in self.__cache:
                key_time = self.__cache[key].time
                if earliest_key is None or key_time < earliest_time:
                    earliest_key = key
                    earliest_time = key_time
            del self.__cache[earliest_key] # type: ignore

class Node:
    NAME: str
    ATTRS: List[str]
    __path_on_disk: str
    __global_cache: NodeCache
    
    def __init__(self, path_on_disk, global_cache):
        self.__path_on_disk = path_on_disk
        self.__global_cache = global_cache

    def __load_data(self) -> Dict:
        if self.__global_cache.contains(self.__path_on_disk):
            return self.__global_cache.retrieve(self.__path_on_disk)
        else:
            if not os.path.isfile(self.__path_on_disk):
                raise FileExistsError(error(f"Could not find node information on disk, searched {self.__path_on_disk}"))
            with open(self.__path_on_disk) as f:
                data = json.load(f)
            return data

    def _load(self, attr):
        if not hasattr(self, attr):
            data = self.__load_data()
            if attr not in data:
                data[attr] = None
                self.__global_cache.store(self.__path_on_disk, data)
            setattr(self, attr, data[attr])
        return getattr(self, attr)
    
    def _save(self, attr, value):
        setattr(self, attr, value)
        data = self.__load_data()
        data[attr] = value
        with open(self.__path_on_disk, "w") as f:
            json.dump(data, f)
        self.__global_cache.store(self.__path_on_disk, data)

    def load_all(self):
        data = None
        for attr in self.ATTRS:
            if not hasattr(self, attr):
                if data is None:
                    data = self.__load_data()
                if attr not in data:
                    data[attr] = None
                    self.__global_cache.store(self.__path_on_disk, data)
                setattr(self, attr, data[attr])
    
    def unload_all(self):
        for attr in self.ATTRS:
            if hasattr(self, attr):
                delattr(self, attr)

    @classmethod
    def create(cls: Type[T], create_args) -> T:
        if cls is Node:
            raise ValueError("Can not instanciate base Node, must be usertype generated from user-defined struct")
        path_on_disk = f"{create_args['world_dirpath']}/{STRUCT_DIRNAME}/{cls.NAME}/{INSTANCES_DIRNAME}/{uuid.uuid4().hex}.json" # type: ignore
        if os.path.exists(path_on_disk):
            raise RuntimeError(f"Found duplicate node path when trying to create new Node {path_on_disk}")
        with open(path_on_disk, "w") as f:
            f.write("{}")
        obj = cls(path_on_disk, create_args['global_cache']) # type: ignore
        return obj


total_file = """
from typing import Optional

from core.components.node import Node

#########################################################
# NOTE: This file is auto-generated.                    #
# Any changes made to this file will automatically get  #
# deleted the next time the associated struct is saved. #
#########################################################

class <class_name>(Node):
    NAME = "<struct_name>"
    ATTRS = [<attr_list>]

    def __init__(self, *args):
        super().__init__(*args)
<getters_and_setters>""".lstrip()

getters_and_setters = """
    def get_<name>(self) -> Optional[<type>]:  return self._load("<name>")
    def set_<name>(self, value: <type>) -> None:  self._save("<name>", value)
"""

def generate_node_text(name: str, parameters: List[Parameter]) -> str:
    return total_file \
        .replace("<struct_name>", name) \
        .replace("<attr_list>", ", ".join([f'"{p.name}"' for p in parameters])) \
        .replace("<class_name>", file_to_class_name(name)) \
        .replace("<getters_and_setters>", "".join([getters_and_setters.replace("<name>", p.name).replace("<type>", p.type_.__name__) for p in parameters]))
