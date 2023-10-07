from typing import Iterator, Optional, Dict, Callable, Type, Tuple
from types import ModuleType
import importlib.util
import threading
import sys
import os

from core.components.world import World
from core.components.node import Node, NodeCache
from core.utils import file_to_class_name
from core.logger import critical
from core.globals import (
    STRUCT_DIRNAME, INSTANCES_DIRNAME,
    USERCODE_DIRNAME, USERCODE_GENERATORS_DIRNAME, USERCODE_TYPES_DIRNAME, USERCODE_COMMON_DIRNAME,
)

def _executor_thread(generator_call: Iterator[Optional[float]], max_count: int, exit_event: threading.Event, on_update: Optional[Callable[[float], None]], on_end: Optional[Callable[[], None]]):
    for index, value in enumerate(generator_call):
        if exit_event.is_set() or not value:
            break

        if on_update:
            on_update(value)

        if max_count > 0 and index + 1 >= max_count:
            break
    
    if on_end:
        on_end()

def _load_module(module_name, module_path) -> Optional[ModuleType]:
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        critical(f"Failed to load module, name={module_name}, path={module_path}, spec={spec}, loader={None if not spec else spec.loader}")
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

def _load_usercode(world_dirpath: str) -> bool:
    for dirname in [USERCODE_TYPES_DIRNAME, USERCODE_COMMON_DIRNAME]:
        dirpath = f"{world_dirpath}/{USERCODE_DIRNAME}/{dirname}"
        for py_file in os.listdir(dirpath):
            if not py_file.endswith(".py"):
                continue
            module_name = os.path.splitext(py_file)[0]
            module = _load_module(module_name, f"{dirpath}/{py_file}")
            if not module:
                return False
            sys.modules[f"{USERCODE_DIRNAME}.{dirname}.{module_name}"] = module
    return True

def create_executor(
    execute_count: int, world: World, generator_name: str, module_cache: Dict[str, Iterator[Optional[float]]],
    node_cache: NodeCache, on_update: Optional[Callable[[float], None]]=None, on_end: Optional[Callable[[], None]]=None
) -> Tuple[Optional[threading.Thread], Optional[threading.Event]]:
    # load the usercode (types and common subdirs)
    ok = _load_usercode(world.dirpath)
    if not ok:
        return None, None
    if generator_name not in module_cache:
        # module is not in cache so we need to load it
        gen_filepath = f"{world.dirpath}/{USERCODE_DIRNAME}/{USERCODE_GENERATORS_DIRNAME}/{generator_name}.py"
        gen_module = _load_module(generator_name, gen_filepath)
        if not gen_module:
            return None, None

        # get the GeneratorInfo for the currently selected generator function
        generator_infos = [i for i in world.generators if i.filename == generator_name]
        if len(generator_infos) != 1:
            critical(f"Found {len(generator_infos)} GeneratorInfo objects with name {generator_name}, expected 1")
            return None, None
        generator_info = generator_infos[0]

        # create the node arguments for the generator function
        node_args = { }
        for name in generator_info.input_struct_names:
            # grab the module
            module_name = f"{USERCODE_DIRNAME}.{USERCODE_TYPES_DIRNAME}.{name}"
            if module_name not in sys.modules:
                critical(f"Failed to find module in sys.modules, searched for {module_name}")
                return None, None
            
            # grab the class
            module = sys.modules[module_name]
            class_name = file_to_class_name(name)
            if not hasattr(module, class_name):
                critical(f"Failed to find class '{class_name}' in module '{module_name}'")
                return None, None
            cls: Type[Node] = getattr(module, class_name)

            # add to the node args a Node instance for each file in the instances folder
            instance_dirpath = f"{world.dirpath}/{STRUCT_DIRNAME}/{name}/{INSTANCES_DIRNAME}"
            node_args[f"{name}s"] = [cls(f"{instance_dirpath}/{f}", node_cache) for f in os.listdir(instance_dirpath)] if os.path.isdir(instance_dirpath) else []

        # create the generator function and store it in the cache
        create_args = { 'world_dirpath': world.dirpath, 'global_cache': node_cache }
        module_cache[generator_name] = gen_module.generate(create_args, **node_args) # type: ignore

    # create a thread to run the executor and start it
    generator_call = module_cache[generator_name]
    exit_event = threading.Event()
    execute_thread = threading.Thread(target=_executor_thread, args=(generator_call, execute_count, exit_event, on_update, on_end))

    return execute_thread, exit_event
