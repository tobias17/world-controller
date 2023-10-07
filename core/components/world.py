from typing import Tuple, Optional, List
import json
import os

from core.components.struct import Struct, load_struct
from core.components.generator_info import GeneratorInfo
from core.components.export_info import dictize
from core.logger import error

class World:
    SETTINGS_FILENAME = "world.json"
    dirpath: str
    structs: List[Struct]
    
    # exported values
    struct_paths: List[str]
    generators: List[GeneratorInfo]

    def save(self) -> None:
        export_list = ["struct_paths", "generators"]
        export_data = { k:dictize(v) for k,v in self.__dict__.items() if k in export_list }
        with open(f"{self.dirpath}/{World.SETTINGS_FILENAME}", 'w') as f:
            json.dump(export_data, f)
    
    @staticmethod
    def empty_world(dirpath: str) -> 'World':
        world = World()
        world.dirpath = dirpath
        world.struct_paths = []
        world.generators = []
        return world

def load_world(path: str) -> Optional[World]:
    world = World()

    world.dirpath = path
    settings_filepath = f"{path}/{World.SETTINGS_FILENAME}"
    if not os.path.exists(settings_filepath):
        error(f"Could not find world {World.SETTINGS_FILENAME} file, searched {settings_filepath}")
        return None
    with open(settings_filepath) as f:
        json_data = json.load(f)
        for k, v in json_data.items():
            if k == "generators":
                v = [GeneratorInfo.from_dict(i) for i in v]
            setattr(world, k, v)
    
    world.structs = []
    for struct_path in world.struct_paths:
        struct = load_struct(struct_path, path)
        if not struct:
            return None
        struct.save()
        world.structs.append(struct)

    return world
