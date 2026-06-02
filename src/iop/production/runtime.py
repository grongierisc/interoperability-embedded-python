from __future__ import annotations

import os
from contextlib import contextmanager
from functools import wraps
from typing import TYPE_CHECKING, Any

from ..runtime.protocol import DirectorProtocol as _DirectorProtocol
from .types import Port

if TYPE_CHECKING:
    from .model import Production


def _has_remote_director(production: Production) -> bool:
    try:
        from ..runtime.remote import _RemoteDirector
    except Exception:
        return False

    return isinstance(production._director, _RemoteDirector)


def resolve_target(target_value: Any) -> Any:
    """Resolve Port values to the current IRIS dispatch string."""
    if isinstance(target_value, Port):
        return target_value.resolve()
    return target_value


@contextmanager
def _temporary_env(name: str, value: str | None):
    if not value:
        yield
        return

    missing = object()
    previous = os.environ.get(name, missing)
    os.environ[name] = value
    try:
        yield
    finally:
        if previous is missing:
            os.environ.pop(name, None)
        else:
            os.environ[name] = str(previous)


class _NamespaceDirectorProxy:
    def __init__(self, director: Any, namespace: str):
        self._director = director
        self._namespace = namespace

    @property
    def namespace(self) -> str:
        return self._namespace

    def __getattr__(self, name: str) -> Any:
        attribute = getattr(self._director, name)
        if not callable(attribute):
            return attribute

        @wraps(attribute)
        def call_with_namespace(*args: Any, **kwargs: Any) -> Any:
            with _temporary_env("IRISNAMESPACE", self._namespace):
                return attribute(*args, **kwargs)

        return call_with_namespace


class _ProductionRuntime:
    def __init__(self, production: Production):
        self.production = production

    @property
    def director(self) -> _DirectorProtocol:
        if self.production._director is not None:
            return self.production._director

        from ..runtime.local import _LocalDirector
        from ..runtime.remote import _RemoteDirector, get_remote_settings

        remote_settings = get_remote_settings()
        if remote_settings:
            if self.production.namespace:
                remote_settings = dict(remote_settings)
                remote_settings["namespace"] = self.production.namespace
            return _RemoteDirector(remote_settings)

        if self.production.namespace:
            return _NamespaceDirectorProxy(
                _LocalDirector(),
                self.production.namespace,
            )
        return _LocalDirector()
