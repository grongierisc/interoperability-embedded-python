from __future__ import annotations

import importlib
import inspect
import os
import sys
from typing import Any, Optional

import iris_persistence
from iris_persistence import Field as Field
from iris_persistence import Model
from iris_persistence.models import ModelMeta
from iris_persistence.runtime import get_runtime


DEFAULT_SUPERCLASS = "Ens.MessageBody"
DEFAULT_SYNC_MODE = "extend"
MESSAGE_KIND_PARAMETER = "IOP_MESSAGE_KIND"
MESSAGE_KIND_VALUE = "PersistentMessage"
PYTHON_CLASS_PARAMETER = "IOP_PYTHON_CLASS"
PYTHON_CLASSPATH_PARAMETER = "IOP_PYTHON_CLASSPATH"

_PYTHON_TO_IRIS_CACHE: dict[str, str] = {}
_IRIS_TO_PYTHON_CACHE: dict[str, str] = {}
_IRIS_TO_PYTHON_CLASSPATH_CACHE: dict[str, str] = {}
_IRIS_TO_PYTHON_STRICT_CACHE: dict[str, bool] = {}
_IRIS_TO_MESSAGE_CLASS_CACHE: dict[str, type] = {}
_IRIS_PARAMETER_CACHE: dict[tuple[str, str], Optional[str]] = {}
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

        if not any(
            getattr(base, "_iop_persistent_message_base", False) for base in bases
        ):
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
    has_classname = meta is not None and hasattr(meta, "classname")
    has_mode = meta is not None and hasattr(meta, "mode")
    has_auto_sync = meta is not None and hasattr(meta, "auto_sync")

    if not has_superclasses:
        cls._superclasses = DEFAULT_SUPERCLASS
    if not has_classname and not getattr(cls, "_iop_registered_classname", None):
        cls._classname = python_classname_to_iris_classname(get_python_classname(cls))
    if not has_mode:
        cls._sync_mode = DEFAULT_SYNC_MODE
    if not has_auto_sync:
        cls._auto_sync = True
    _set_message_parameters(cls)


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


def python_classname_to_iris_classname(python_classname: str) -> str:
    """Encode a Python FQCN as an IRIS-safe classname."""
    if not python_classname:
        raise ValueError("Python classname cannot be empty")
    return ".".join(
        _encode_iris_identifier(part) for part in python_classname.split(".")
    )


def iris_classname_to_python_classname(iris_classname: str) -> str:
    """Decode an IRIS classname produced by python_classname_to_iris_classname."""
    if not iris_classname:
        raise ValueError("IRIS classname cannot be empty")
    return ".".join(_decode_iris_identifier(part) for part in iris_classname.split("."))


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

    _prepare_message_class(msg_cls, iris_classname, registered=True)

    if sync_schema:
        msg_cls.sync_schema()
        _AUTO_SYNCED.add((msg_cls, iris_classname))


def serialize_persistent_message(
    message: _PersistentMessage, is_generator: bool = False
) -> Any:
    if is_generator:
        raise TypeError(
            "PersistentMessage cannot be used as a generator start message."
        )

    msg_cls = type(message)
    iris_classname = resolve_iris_classname(msg_cls)
    _ensure_schema(msg_cls, iris_classname)

    iris_obj = iris_persistence.materialize(
        message,
        auto_sync=False,
        validate=False,
    )
    return iris_obj


def deserialize_persistent_message(
    serial: Any,
    iris_classname: Optional[str] = None,
) -> Any:
    iris_classname = iris_classname or get_iris_object_classname(serial)
    if not iris_classname:
        return serial

    msg_cls = _IRIS_TO_MESSAGE_CLASS_CACHE.get(iris_classname)
    if msg_cls is None:
        python_classname, python_classpath, strict = _resolve_python_message_metadata(
            iris_classname
        )
        if not python_classname:
            return serial

        try:
            msg_cls = load_python_class(python_classname, python_classpath)
        except (AttributeError, ModuleNotFoundError, PersistentMessageError) as exc:
            if strict:
                raise PersistentMessageError(
                    f"IRIS class {iris_classname!r} is marked as a PersistentMessage for "
                    f"Python class {python_classname!r}, but that Python class could not "
                    "be imported. Ensure the message class is importable, or register it "
                    "through CLASSES so migration writes IOP_PYTHON_CLASSPATH."
                ) from exc
            return serial

        if not is_persistent_message_class(msg_cls):
            if strict:
                raise PersistentMessageError(
                    f"IRIS class {iris_classname!r} maps to {python_classname!r}, "
                    "but that class is not a PersistentMessage subclass."
                )
            return serial

        _prepare_message_class(msg_cls, iris_classname, registered=False)
        _IRIS_TO_MESSAGE_CLASS_CACHE[iris_classname] = msg_cls

    known_pk = _safe_get_object_id(serial)
    return msg_cls.from_iris(serial, known_pk=known_pk or "")


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
        _prepare_message_class(msg_cls, explicit_classname, registered=False)
        return explicit_classname

    iris_classname = python_classname_to_iris_classname(python_classname)
    _prepare_message_class(msg_cls, iris_classname, registered=False)
    return iris_classname


def resolve_python_classname(iris_classname: str) -> Optional[str]:
    python_classname, _python_classpath, _strict = _resolve_python_message_metadata(
        iris_classname
    )
    return python_classname


def load_python_class(
    python_classname: str, python_classpath: Optional[str] = None
) -> type:
    module_name, _, class_name = python_classname.rpartition(".")
    if not module_name:
        raise PersistentMessageError(
            f"PersistentMessage Python classname {python_classname!r} is not fully qualified"
        )
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if not python_classpath or not _is_missing_target_module(exc, module_name):
            raise
        module = _import_module_from_classpath(module_name, python_classpath)
    else:
        if python_classpath and not hasattr(module, class_name):
            module = _import_module_from_classpath(module_name, python_classpath)
    return getattr(module, class_name)


def get_python_classpath(klass: type) -> str:
    try:
        class_file = inspect.getfile(klass)
    except TypeError:
        return ""

    if not class_file:
        return ""

    classpath = os.path.abspath(os.path.dirname(class_file))
    module_parts = klass.__module__.split(".")
    for _ in module_parts[:-1]:
        classpath = os.path.dirname(classpath)
    return classpath


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
    key = (msg_cls, iris_classname)
    if key in _AUTO_SYNCED:
        return
    if not getattr(msg_cls, "_auto_sync", False):
        return
    if getattr(msg_cls, "_sync_mode", DEFAULT_SYNC_MODE) != DEFAULT_SYNC_MODE:
        raise PersistentMessageError(
            f"{get_python_classname(msg_cls)} has auto_sync=True but mode="
            f"{getattr(msg_cls, '_sync_mode', None)!r}. Runtime auto-sync is only allowed "
            "with mode='extend'."
        )

    _prepare_message_class(msg_cls, iris_classname, registered=False)
    msg_cls.sync_schema()
    _AUTO_SYNCED.add(key)


def _prepare_message_class(
    msg_cls: type,
    iris_classname: str,
    *,
    registered: bool,
) -> None:
    _apply_persistent_message_defaults(msg_cls)
    msg_cls._classname = iris_classname
    if registered:
        msg_cls._iop_registered_classname = iris_classname
    _set_message_parameters(msg_cls)
    _cache_mapping(get_python_classname(msg_cls), iris_classname)
    _IRIS_TO_MESSAGE_CLASS_CACHE[iris_classname] = msg_cls


def _set_message_parameters(msg_cls: type) -> None:
    parameters = dict(getattr(msg_cls, "_parameters", {}) or {})
    parameters.update(
        {
            MESSAGE_KIND_PARAMETER: MESSAGE_KIND_VALUE,
            PYTHON_CLASS_PARAMETER: get_python_classname(msg_cls),
            PYTHON_CLASSPATH_PARAMETER: get_python_classpath(msg_cls),
        }
    )
    msg_cls._parameters = parameters


def _cache_mapping(python_classname: str, iris_classname: str) -> None:
    _PYTHON_TO_IRIS_CACHE[python_classname] = iris_classname
    _IRIS_TO_PYTHON_CACHE[iris_classname] = python_classname
    _IRIS_TO_PYTHON_STRICT_CACHE[iris_classname] = True


def _resolve_python_message_metadata(
    iris_classname: str,
) -> tuple[Optional[str], Optional[str], bool]:
    cached = _IRIS_TO_PYTHON_CACHE.get(iris_classname)
    if cached:
        return (
            cached,
            _IRIS_TO_PYTHON_CLASSPATH_CACHE.get(iris_classname),
            _IRIS_TO_PYTHON_STRICT_CACHE.get(iris_classname, True),
        )

    kind = get_iris_class_parameter(iris_classname, MESSAGE_KIND_PARAMETER)
    python_classname = get_iris_class_parameter(iris_classname, PYTHON_CLASS_PARAMETER)
    python_classpath = get_iris_class_parameter(
        iris_classname, PYTHON_CLASSPATH_PARAMETER
    )
    strict = kind == MESSAGE_KIND_VALUE or bool(python_classname)

    if not python_classname:
        python_classname = iris_classname_to_python_classname(iris_classname)

    if python_classname and strict:
        _cache_mapping(python_classname, iris_classname)
        if python_classpath:
            _IRIS_TO_PYTHON_CLASSPATH_CACHE[iris_classname] = python_classpath

    return python_classname, python_classpath, strict


def get_iris_class_parameter(
    iris_classname: str,
    parameter_name: str,
) -> Optional[str]:
    key = (iris_classname, parameter_name)
    if key in _IRIS_PARAMETER_CACHE:
        return _IRIS_PARAMETER_CACHE[key]

    value = None
    runtime = get_runtime()
    for method_name in ("_GetParameter", "%GetParameter"):
        try:
            raw_value = runtime.call_classmethod(
                iris_classname,
                method_name,
                parameter_name,
            )
        except Exception:
            continue
        if raw_value:
            value = str(raw_value)
            break

    if value is not None:
        _IRIS_PARAMETER_CACHE[key] = value
    return value


def _is_missing_target_module(exc: ModuleNotFoundError, module_name: str) -> bool:
    missing_name = getattr(exc, "name", None)
    return bool(
        missing_name
        and (module_name == missing_name or module_name.startswith(f"{missing_name}."))
    )


def _encode_iris_identifier(value: str) -> str:
    if not value:
        raise ValueError("IRIS classname parts cannot be empty")

    encoded: list[str] = []
    for char in value:
        if char == "z":
            encoded.append("zz")
        elif char == "_":
            encoded.append("zU")
        elif char.isascii() and char.isalnum():
            encoded.append(char)
        else:
            encoded.append(f"zX{ord(char):X}z")

    return "".join(encoded)


def _decode_iris_identifier(value: str) -> str:
    decoded: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char != "z":
            decoded.append(char)
            index += 1
            continue

        if index + 1 >= len(value):
            decoded.append(char)
            index += 1
            continue

        marker = value[index + 1]
        if marker == "z":
            decoded.append("z")
            index += 2
        elif marker == "U":
            decoded.append("_")
            index += 2
        elif marker == "X":
            end = value.find("z", index + 2)
            if end == -1:
                decoded.append(char)
                index += 1
                continue
            try:
                decoded.append(chr(int(value[index + 2 : end], 16)))
            except ValueError:
                decoded.append(char)
                index += 1
                continue
            index = end + 1
        else:
            decoded.append(char)
            index += 1

    return "".join(decoded)


def _prepend_sys_path(path: str) -> None:
    normalized_path = os.path.abspath(os.path.normpath(path))
    while normalized_path in sys.path:
        sys.path.remove(normalized_path)
    sys.path.insert(0, normalized_path)
    importlib.invalidate_caches()


def _import_module_from_classpath(module_name: str, python_classpath: str):
    _prepend_sys_path(python_classpath)
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)
