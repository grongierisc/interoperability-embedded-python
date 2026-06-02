from __future__ import annotations

import importlib
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def temporary_env(name: str, value: str | None) -> Iterator[None]:
    """Temporarily set an environment variable, restoring the previous value."""
    missing = object()
    previous = os.environ.get(name, missing)
    if value is not None:
        os.environ[name] = value
    try:
        yield
    finally:
        if previous is missing:
            os.environ.pop(name, None)
        else:
            os.environ[name] = str(previous)


def normalize_path(path: str) -> str:
    return os.path.abspath(os.path.normpath(path))


def prepend_sys_path(path: str) -> str:
    """Move *path* to the front of sys.path and invalidate import caches."""
    normalized = normalize_path(path)
    while normalized in sys.path:
        sys.path.remove(normalized)
    sys.path.insert(0, normalized)
    importlib.invalidate_caches()
    return normalized


def remove_sys_path(path: str | None) -> None:
    if not path:
        return
    normalized = normalize_path(path)
    while normalized in sys.path:
        sys.path.remove(normalized)
    importlib.invalidate_caches()


@contextmanager
def temporary_sys_path(path: str | None) -> Iterator[str | None]:
    """Temporarily prepend *path* to sys.path, then remove it."""
    if not path:
        yield None
        return
    normalized = prepend_sys_path(path)
    try:
        yield normalized
    finally:
        remove_sys_path(normalized)
