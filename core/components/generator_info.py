import re

from core.components.formable import Formable
from core.components.export_info import ExportInfo, dictize
from core.logger import error
from core.utils import file_to_class_name, check_name
from core.globals import USERCODE_DIRNAME, USERCODE_GENERATORS_DIRNAME, USERCODE_TYPES_DIRNAME

from typing import List, Dict

generator_template = """
from typing import List, Iterator, Optional

<imports>

def generate(create_args<params>) -> Iterator[Optional[float]]:
    # After major actions and at good stopping points, your generator should yield
    # Generators are only able to be stopped after yields, so not doing so might lock the program up
    # When it makes sense, yield a float between 0 and 1 to indicate the percent progress of your generator
    # If a percentage does not make sense, yield -1
    # When your generator is complete with no more work to do, yield None

    # we cannot determine a percentage completion so we yield -1
    import random
    while random.random() < 0.9:
        # *computation here*
        yield -1

    # we know our percentage completion here so we yield a number between 0 and 1
    for i in range(10):
        # *computation here*
        yield (i+1)/10
    
    # generator is complete so we yield None
    yield None
""".lstrip()
import_template = f"from {USERCODE_DIRNAME}.{USERCODE_TYPES_DIRNAME}.<file_name> import <class_name>"
params_template = "<file_name>s: List[<class_name>]"

class GeneratorInfo(Formable):
    TO_DICT: bool = True
    PARAM_LIST = [
        ExportInfo("filename", str),
        ExportInfo("input_struct_names", List, child=ExportInfo("input_struct_name", str)),
    ]

    filename: str
    input_struct_names: List[str]

    def copy(self) -> 'GeneratorInfo':
        struct = GeneratorInfo()
        for export_info in GeneratorInfo.PARAM_LIST:
            setattr(struct, export_info.name, getattr(self, export_info.name))
        return struct

    def to_dict(self) -> dict:
        return { k:dictize(v) for k,v in self.__dict__.items() }
    @classmethod
    def from_dict(cls, data: Dict) -> 'GeneratorInfo':
        obj: 'GeneratorInfo' = cls()
        for k, v in data.items():
            setattr(obj, k, v)
        return obj

    def is_valid(self) -> bool:
        if not check_name(self.filename):
            return False
        seen = []
        repeats = []
        for input in self.input_struct_names:
            if not input:
                error("input struct names can not be empty")
                return False
            if input not in repeats:
                if input not in seen:
                    seen.append(input)
                else:
                    repeats.append(input)
        if len(repeats) > 0:
            error(f"can not have multiple of the same input structs, saw the following more than once: {repeats}")
            return False
        return True

    def create_file(self, world_dirpath: str) -> None:
        text = generator_template
        text = text if len(self.input_struct_names) == 0 else text.replace("<params>", ", <params>")
        for key, delimeter, template in [("<imports>", "\n", import_template), ("<params>", ", ", params_template)]:
            text = text.replace(key, delimeter.join([template.replace("<file_name>", n).replace("<class_name>", file_to_class_name(n)) for n in self.input_struct_names]))
        with open(self.get_filepath(world_dirpath), "w") as f:
            f.write(text)

    def get_filepath(self, world_dirpath: str) -> str:
        return f"{world_dirpath}/{USERCODE_DIRNAME}/{USERCODE_GENERATORS_DIRNAME}/{self.filename}.py"
