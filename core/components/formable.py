from typing import List

from core.components.export_info import ExportInfo

class Formable:
    PARAM_LIST: List[ExportInfo]

    @classmethod
    def empty_object(cls, **kwargs):
        obj = cls()
        if hasattr(obj, "REQUIRED"):
            for attr in getattr(obj, "REQUIRED"):
                if attr not in kwargs:
                    raise ValueError(f"Failed to provide named parameter '{attr}' when creating empty {obj.__class__.__name__}")
                setattr(obj, attr, kwargs[attr])
        for export_info in obj.PARAM_LIST:
            setattr(obj, export_info.name, export_info.default())
        return obj
