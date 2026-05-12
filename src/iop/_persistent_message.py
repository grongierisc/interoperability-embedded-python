from __future__ import annotations

import importlib
from typing import Any, Optional

from iris_persistence import Field, Model
from iris_persistence.models import ModelMeta
from iris_persistence.query import _build_model_from_iris_obj, _materialize_related_value
from iris_persistence.runtime import get_runtime

from . import _iris


DEFAULT_SUPERCLASS = "Ens.MessageBody"
DEFAULT_SYNC_MODE = "extend"

_PYTHON_TO_IRIS_CACHE: dict[str, str] = {}
_IRIS_TO_PYTHON_CACHE: dict[str, str] = {}
_AUTO_SYNCED: set[tuple[type, str]] = set()


class PersistentMessageError(Exception):
    """Raised when a native persistent message cannot be materialized."""


class _PersistentMessageMeta(ModelMeta):
    def __init__(cls, name: str, bases: tuple, namespace: dict, **kwargs: Any):
        super().__init__(name, bases, namespace, **kwargs)

        if namespace.get("_iop_persistent_message_abstract", False):
            cls._iop_persistent_message_base = True
            cls._iop_persistent_message_abstract = True
            return

        if not any(getattr(base, "_iop_persistent_message_base", False) for base in bases):
            cls._iop_persistent_message_base = True
            cls._iop_persistent_message_abstract = True
            return

        _apply_persistent_message_defaults(cls, namespace, kwargs)
        cls._iop_persistent_message_base = True
        cls._iop_persistent_message_abstract = False


def _explicit_meta_classname(cls: type) -> Optional[str]:
    meta = cls.__dict__.get("Meta")
    if meta is None or not hasattr(meta, "classname"):
        return None
    value = getattr(meta, "classname")
    return str(value) if value else None


def _apply_persistent_message_defaults(
    cls: type,
    namespace: Optional[dict] = None,
    kwargs: Optional[dict] = None,
) -> None:
    namespace = namespace or {}
    kwargs = kwargs or {}
    meta = namespace.get("Meta") or cls.__dict__.get("Meta")

    has_superclasses = "superclasses" in kwargs or (
        meta is not None and hasattr(meta, "superclasses")
    )
    has_mode = meta is not None and hasattr(meta, "mode")
    has_auto_sync = meta is not None and hasattr(meta, "auto_sync")

    if not has_superclasses:
        cls._superclasses = DEFAULT_SUPERCLASS
    if not has_mode:
        cls._sync_mode = DEFAULT_SYNC_MODE
    if not has_auto_sync:
        cls._auto_sync = True


class _PersistentMessage(Model, metaclass=_PersistentMessageMeta):
    _iop_persistent_message_abstract = True

    def get_iris_id(self) -> Optional[str]:
        if self.pk:
            return self.pk

        iris_obj = self.__dict__.get("_iris_obj")
        if iris_obj is None:
            return None

        try:
            obj_id = get_runtime().get_object_id(iris_obj)
            if obj_id:
                return str(obj_id)
        except Exception:
            pass

        for method_name in ("_Id", "Id", "%Id"):
            try:
                method = getattr(iris_obj, method_name)
                obj_id = method()
                if obj_id:
                    return str(obj_id)
            except Exception:
                pass
        return None


def is_persistent_message_class(klass: Any) -> bool:
    try:
        return (
            isinstance(klass, type)
            and issubclass(klass, _PersistentMessage)
            and not getattr(klass, "_iop_persistent_message_abstract", False)
        )
    except TypeError:
        return False


def is_persistent_message_instance(obj: Any) -> bool:
    return is_persistent_message_class(type(obj))


def get_python_classname(klass: type) -> str:
    return f"{klass.__module__}.{klass.__name__}"


def register_persistent_message_class(
    msg_cls: type,
    iris_classname: str,
    *,
    sync_schema: bool = True,
) -> None:
    if not is_persistent_message_class(msg_cls):
        raise TypeError("The class must be a subclass of PersistentMessage")
    if not iris_classname:
        raise ValueError("PersistentMessage IRIS classname cannot be empty")

    explicit_classname = _explicit_meta_classname(msg_cls)
    if explicit_classname and explicit_classname != iris_classname:
        raise ValueError(
            f"{get_python_classname(msg_cls)} declares Meta.classname={explicit_classname!r}, "
            f"but CLASSES registers it as {iris_classname!r}"
        )

    _apply_persistent_message_defaults(msg_cls)
    msg_cls._classname = iris_classname
    msg_cls._parameters = {
        **(getattr(msg_cls, "_parameters", {}) or {}),
        "IOP_MESSAGE_KIND": "PersistentMessage",
        "IOP_PYTHON_CLASS": get_python_classname(msg_cls),
    }
    msg_cls._iop_registered_classname = iris_classname
    _cache_mapping(get_python_classname(msg_cls), iris_classname)

    if sync_schema:
        msg_cls.sync_schema()

    _register_mapping_in_iris(get_python_classname(msg_cls), iris_classname)


def serialize_persistent_message(message: _PersistentMessage, is_generator: bool = False) -> Any:
    if is_generator:
        raise TypeError("PersistentMessage cannot be used as a generator start message.")

    msg_cls = type(message)
    iris_classname = resolve_iris_classname(msg_cls)
    _ensure_schema(msg_cls, iris_classname)

    runtime = get_runtime()
    iris_obj = message.__dict__.get("_iris_obj")
    if iris_obj is None:
        iris_obj = runtime.create_object(iris_classname)

    for field_name, model_field in msg_cls.__model_fields__.items():
        if field_name not in message.__dict__:
            continue
        value = getattr(message, field_name)
        materialized = _materialize_related_value(runtime, model_field.declared_type, value)
        runtime.inject_iris_value(
            iris_obj,
            field_name,
            materialized,
            field_meta=model_field.field_info,
        )

    message._iris_obj = iris_obj
    try:
        obj_id = runtime.get_object_id(iris_obj)
        if obj_id:
            message._pk = str(obj_id)
    except Exception:
        pass
    return iris_obj


def deserialize_persistent_message(serial: Any) -> Any:
    iris_classname = get_iris_object_classname(serial)
    if not iris_classname:
        return serial

    python_classname = resolve_python_classname(iris_classname)
    if not python_classname:
        return serial

    msg_cls = load_python_class(python_classname)
    if not is_persistent_message_class(msg_cls):
        return serial

    _apply_persistent_message_defaults(msg_cls)
    msg_cls._classname = iris_classname
    msg_cls._iop_registered_classname = iris_classname
    _cache_mapping(python_classname, iris_classname)

    known_pk = _safe_get_object_id(serial)
    return _build_model_from_iris_obj(msg_cls, serial, known_pk=known_pk or "")


def resolve_iris_classname(msg_cls: type) -> str:
    python_classname = get_python_classname(msg_cls)

    cached = _PYTHON_TO_IRIS_CACHE.get(python_classname)
    if cached:
        return cached

    registered = getattr(msg_cls, "_iop_registered_classname", None)
    if registered:
        _cache_mapping(python_classname, registered)
        return registered

    explicit_classname = _explicit_meta_classname(msg_cls)
    if explicit_classname:
        _cache_mapping(python_classname, explicit_classname)
        return explicit_classname

    registry_classname = _lookup_iris_classname_in_registry(python_classname)
    if registry_classname:
        msg_cls._classname = registry_classname
        msg_cls._iop_registered_classname = registry_classname
        _cache_mapping(python_classname, registry_classname)
        return registry_classname

    raise PersistentMessageError(
        f"{python_classname} is a PersistentMessage but has no registered IRIS classname. "
        "Register it in settings.CLASSES, for example: "
        f'CLASSES = {{"Package.MessageClass": {msg_cls.__module__}.{msg_cls.__name__}}}'
    )


def resolve_python_classname(iris_classname: str) -> Optional[str]:
    cached = _IRIS_TO_PYTHON_CACHE.get(iris_classname)
    if cached:
        return cached

    python_classname = _lookup_python_classname_in_registry(iris_classname)
    if python_classname:
        _cache_mapping(python_classname, iris_classname)
    return python_classname


def load_python_class(python_classname: str) -> type:
    module_name, _, class_name = python_classname.rpartition(".")
    if not module_name:
        raise PersistentMessageError(
            f"PersistentMessage registry entry {python_classname!r} is not fully qualified"
        )
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def get_iris_object_classname(obj: Any) -> Optional[str]:
    for method_name in ("%ClassName", "_ClassName"):
        try:
            method = getattr(obj, method_name)
            value = method(1)
            if value:
                return str(value)
        except Exception:
            pass
    try:
        value = obj.__class__.__name__
        return str(value) if value else None
    except Exception:
        return None


def _safe_get_object_id(obj: Any) -> Optional[str]:
    for method_name in ("_Id", "Id", "%Id"):
        try:
            method = getattr(obj, method_name)
            obj_id = method()
            if obj_id:
                return str(obj_id)
        except Exception:
            pass
    return None


def _ensure_schema(msg_cls: type, iris_classname: str) -> None:
    if not getattr(msg_cls, "_auto_sync", False):
        return
    if getattr(msg_cls, "_sync_mode", DEFAULT_SYNC_MODE) != DEFAULT_SYNC_MODE:
        raise PersistentMessageError(
            f"{get_python_classname(msg_cls)} has auto_sync=True but mode="
            f"{getattr(msg_cls, '_sync_mode', None)!r}. Runtime auto-sync is only allowed "
            "with mode='extend'."
        )

    key = (msg_cls, iris_classname)
    if key in _AUTO_SYNCED:
        return

    msg_cls._classname = iris_classname
    msg_cls.sync_schema()
    _AUTO_SYNCED.add(key)


def _cache_mapping(python_classname: str, iris_classname: str) -> None:
    _PYTHON_TO_IRIS_CACHE[python_classname] = iris_classname
    _IRIS_TO_PYTHON_CACHE[iris_classname] = python_classname


def _registry() -> Any:
    return _iris.get_iris().cls("IOP.PersistentMessage.Registry")


def _register_mapping_in_iris(python_classname: str, iris_classname: str) -> None:
    sc = _registry().Register(python_classname, iris_classname)
    if _iris.get_iris().system.Status.IsError(sc):
        raise RuntimeError(_iris.get_iris().system.Status.GetOneStatusText(sc))


def _lookup_iris_classname_in_registry(python_classname: str) -> Optional[str]:
    try:
        value = _registry().GetIRISClassName(python_classname)
        return str(value) if value else None
    except Exception:
        return None


def _lookup_python_classname_in_registry(iris_classname: str) -> Optional[str]:
    try:
        value = _registry().GetPythonClassName(iris_classname)
        return str(value) if value else None
    except Exception:
        return None
