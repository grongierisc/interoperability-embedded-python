from __future__ import annotations

import importlib.util
import os
import sys
from types import ModuleType


def module_name_from_file(filename: str) -> str:
    return os.path.splitext(os.path.basename(filename))[0]


def import_module_from_path(module_name: str, file_path: str) -> ModuleType:
    if not os.path.isabs(file_path):
        raise ValueError("The file path must be absolute")

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot find module named {module_name} at {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def load_settings(filename: str | None = None) -> tuple[ModuleType, str | None]:
    path_added = None
    if filename:
        if not os.path.isabs(filename):
            raise ValueError("The filename must be absolute")
        path_added = os.path.normpath(os.path.dirname(filename))
        sys.path.insert(0, path_added)
        settings = import_module_from_path(module_name_from_file(filename), filename)
    else:
        import settings  # type: ignore

    return settings, path_added


def folder_path(filename: str | None, path_added_to_sys: str | None) -> str:
    del path_added_to_sys
    return os.path.dirname(filename) if filename else os.getcwd()
