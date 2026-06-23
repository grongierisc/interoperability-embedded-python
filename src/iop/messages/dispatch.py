import ast
import logging
from collections.abc import Callable
from dataclasses import dataclass
from inspect import Parameter, signature
from typing import Any

from .persistent import (
    deserialize_persistent_message,
    get_iris_object_classname,
    is_persistent_message_class,
    is_persistent_message_instance,
    serialize_persistent_message,
)
from .serialization import (
    deserialize_message,
    deserialize_pickle_message,
    serialize_message,
    serialize_message_generator,
    serialize_pickle_message,
    serialize_pickle_message_generator,
)
from .validation import (
    is_iris_object_instance,
    is_message_class,
    is_message_instance,
    is_pickle_message_class,
    is_pickle_message_instance,
)

_MESSAGE_CLASSES = {
    "IOP.Message",
    "IOP.Generator.Message.Start",
}
_PICKLE_MESSAGE_CLASSES = {
    "IOP.PickleMessage",
    "IOP.Generator.Message.StartPickle",
}
_HANDLER_ATTRIBUTE = "__iop_handler_message__"
_IRIS_MODULE_PREFIX = "iris."
_UNRESOLVED = object()


@dataclass(frozen=True)
class _DispatchCandidate:
    message: str
    method: str
    source: str
    priority: int
    index: int


def handler(message_type: Any) -> Callable[[Callable], Callable]:
    """Declare a method as the handler for a message type.

    Use @handler(MessageType) when a BusinessProcess or BusinessOperation should
    route a specific message type to a specific method. Typed one-argument
    methods are also auto-discovered; on_message() remains the fallback.
    See docs/cookbooks/add-business-process.md and
    docs/cookbooks/add-business-operation.md.

    Args:
        message_type: The message class, fully qualified class name string, or
            IRIS object instance this method handles.
    """
    message = _message_key_from_declared(message_type)
    if message is None:
        raise TypeError("handler() requires a message class or class name")

    def _handler(method: Callable) -> Callable:
        setattr(method, _HANDLER_ATTRIBUTE, message)
        return method

    return _handler


def dispatch_serializer(message: Any, is_generator: bool = False) -> Any:
    """Serializes the message based on its type.

    Args:
        message: The message to serialize

    Returns:
        The serialized message

    Raises:
        TypeError: If message is invalid type
    """
    if message is not None:
        if is_persistent_message_instance(message):
            return serialize_persistent_message(message, is_generator=is_generator)
        elif is_message_instance(message):
            if is_generator:
                return serialize_message_generator(message)
            return serialize_message(message)
        elif is_pickle_message_instance(message):
            if is_generator:
                return serialize_pickle_message_generator(message)
            return serialize_pickle_message(message)
        elif is_iris_object_instance(message):
            return message

    if message == "" or message is None:
        return message

    if hasattr(message, "__iter__"):
        raise TypeError(
            "You may have tried to invoke a generator function without using the 'send_generator_request' method. Please use that method to handle generator functions."
        )

    raise TypeError(
        "The message must be an instance of a class that is a subclass of Message or IRISObject %Persistent class."
    )


def dispatch_deserializer(serial: Any) -> Any:
    """Deserializes the message based on its type.

    Args:
        serial: The serialized message

    Returns:
        The deserialized message
    """
    if serial is None or not type(serial).__module__.startswith("iris"):
        return serial

    iris_classname = get_iris_object_classname(serial)

    if iris_classname in _MESSAGE_CLASSES:
        return deserialize_message(serial)

    if iris_classname in _PICKLE_MESSAGE_CLASSES:
        return deserialize_pickle_message(serial)

    deserialized = deserialize_persistent_message(serial, iris_classname=iris_classname)
    if deserialized is not serial:
        return deserialized

    if serial._IsA("IOP.Message"):
        return deserialize_message(serial)

    if serial._IsA("IOP.PickleMessage"):
        return deserialize_pickle_message(serial)

    return serial


def dispatch_message(host: Any, request: Any) -> Any:
    """Dispatches the message to the appropriate method.

    Args:
        request: The request object

    Returns:
        The response object
    """
    call = "on_message"

    message_names = _message_keys_from_request(request)

    for msg, method in host.DISPATCH:
        if msg in message_names:
            return getattr(host, method)(request)

    return getattr(host, call)(request)


def create_dispatch(host: Any) -> None:
    """Creates a dispatch table mapping class names to their handler methods.
    The dispatch table consists of tuples of (fully_qualified_class_name, method_name).
    Only methods that take a single typed parameter are considered as handlers.
    """
    candidates: list[_DispatchCandidate] = []
    index = 0

    for message, method in _decorated_dispatch(host):
        candidates.append(
            _DispatchCandidate(message, method, "@handler", priority=0, index=index)
        )
        index += 1

    for message, method in _declared_dispatch(host):
        candidates.append(
            _DispatchCandidate(message, method, "DISPATCH", priority=1, index=index)
        )
        index += 1

    for method_name in get_callable_methods(host):
        if _handler_message(getattr(host, method_name)) is not None:
            continue
        handler_info = get_handler_info(host, method_name)
        if handler_info:
            message, method = handler_info
            candidates.append(
                _DispatchCandidate(
                    message, method, "typed method", priority=1, index=index
                )
            )
            index += 1

    host.DISPATCH = _deduplicate_dispatch(host, candidates)


def _declared_dispatch(host: Any) -> list[tuple[str, str]]:
    if "DISPATCH" in getattr(host, "__dict__", {}):
        return _normalized_dispatch(host.__dict__["DISPATCH"])

    class_dispatch = host.__class__.__dict__.get("DISPATCH")
    if class_dispatch is not None:
        return _normalized_dispatch(class_dispatch)

    return []


def _normalized_dispatch(dispatch: Any) -> list[tuple[str, str]]:
    entries = []
    for message, method in dispatch:
        key = _message_key_from_declared(message)
        if key is not None:
            entries.append((key, method))
    return entries


def _decorated_dispatch(host: Any) -> list[tuple[str, str]]:
    dispatch = []
    for method_name in dir(host):
        method = getattr(host, method_name)
        if not callable(method):
            continue
        message = _handler_message(method)
        if message is not None:
            dispatch.append((message, method_name))
    return dispatch


def _deduplicate_dispatch(
    host: Any, candidates: list[_DispatchCandidate]
) -> list[tuple[str, str]]:
    selected: dict[str, _DispatchCandidate] = {}

    for candidate in candidates:
        current = selected.get(candidate.message)
        if current is None:
            selected[candidate.message] = candidate
            continue

        if current.method == candidate.method:
            if _is_higher_priority(candidate, current):
                selected[candidate.message] = candidate
            continue

        if _is_higher_priority(candidate, current):
            _log_duplicate_mapping(host, kept=candidate, discarded=current)
            selected[candidate.message] = candidate
        else:
            _log_duplicate_mapping(host, kept=current, discarded=candidate)

    return [
        (candidate.message, candidate.method)
        for candidate in sorted(selected.values(), key=lambda item: item.index)
    ]


def _is_higher_priority(
    candidate: _DispatchCandidate, current: _DispatchCandidate
) -> bool:
    if candidate.priority != current.priority:
        return candidate.priority < current.priority
    return candidate.index > current.index


def _log_duplicate_mapping(
    host: Any, kept: _DispatchCandidate, discarded: _DispatchCandidate
) -> None:
    message = (
        f"Duplicate dispatch mapping for {kept.message}: "
        f"keeping {kept.method} from {kept.source}; "
        f"discarding {discarded.method} from {discarded.source}."
    )
    log_warning = getattr(host, "log_warning", None)
    if callable(log_warning):
        try:
            log_warning(message)
            return
        except Exception:
            pass

    logging.getLogger(__name__).warning(message)


def _handler_message(method: Any) -> str | None:
    message = getattr(method, _HANDLER_ATTRIBUTE, None)
    if message is not None:
        return message

    func = getattr(method, "__func__", None)
    return getattr(func, _HANDLER_ATTRIBUTE, None)


def get_callable_methods(host: Any) -> list[str]:
    """Returns a list of callable method names that don't start with underscore."""
    return [
        func
        for func in dir(host)
        if callable(getattr(host, func)) and not func.startswith("_")
    ]


def get_handler_info(host: Any, method_name: str) -> tuple[str, str] | None:
    """Analyzes a method to determine if it's a valid message handler.
    Returns a tuple of (fully_qualified_class_name, method_name) if valid,
    None otherwise.
    """
    try:
        params = signature(getattr(host, method_name)).parameters
        if len(params) != 1:
            return None

        method = getattr(host, method_name)
        param: Parameter = next(iter(params.values()))
        message = _message_key_from_annotation(host, method, param.annotation)
        if message is None:
            return None

        return message, method_name

    except ValueError:
        return None


def _message_key_from_annotation(
    host: Any, method: Callable, annotation: Any
) -> str | None:
    if annotation == Parameter.empty:
        return None

    if not isinstance(annotation, str):
        return _message_key_from_declared(annotation, allow_bare_string=False)

    value: Any = annotation
    for _ in range(3):
        if not isinstance(value, str):
            return _message_key_from_declared(value, allow_bare_string=False)

        key = _message_key_from_string(value, allow_bare=False)
        if key is not None:
            return key

        unquoted = _unquote_string(value)
        if unquoted is not None and unquoted != value:
            value = unquoted
            continue

        value = _lookup_annotation_name(host, method, value)
        if value is _UNRESOLVED:
            return None

    return None


def _message_keys_from_request(request: Any) -> tuple[str, ...]:
    module = request.__class__.__module__
    classname = request.__class__.__name__
    names = [f"{module}.{classname}"]

    if module.startswith("iris"):
        native_name = _native_iris_message_key(request)
        if native_name:
            names.append(native_name)
            names.append(f"{_IRIS_MODULE_PREFIX}{native_name}")

    return tuple(dict.fromkeys(names))


def _message_key_from_declared(
    message_type: Any, *, allow_bare_string: bool = True
) -> str | None:
    if isinstance(message_type, str):
        return _message_key_from_string(
            message_type,
            allow_bare=allow_bare_string,
        )

    if is_iris_object_instance(message_type):
        return _native_iris_message_key(message_type) or _python_class_key(
            type(message_type)
        )

    if message_type is Any or message_type is object:
        return None

    if not isinstance(message_type, type):
        return None

    if not _is_dispatch_message_class(message_type):
        return None

    return _python_class_key(message_type)


def _message_key_from_string(value: str, *, allow_bare: bool) -> str | None:
    if not value or _unquote_string(value) is not None:
        return None

    normalized = _strip_iris_prefix(value)
    if "." in normalized:
        return normalized if _looks_like_message_key(normalized) else None

    return normalized if allow_bare else None


def _native_iris_message_key(message: Any) -> str | None:
    iris_classname = get_iris_object_classname(message)
    if not iris_classname:
        return None
    return _strip_iris_prefix(iris_classname)


def _python_class_key(klass: type) -> str:
    return f"{klass.__module__}.{klass.__name__}"


def _strip_iris_prefix(value: str) -> str:
    if value.startswith(_IRIS_MODULE_PREFIX):
        return value[len(_IRIS_MODULE_PREFIX) :]
    return value


def _looks_like_message_key(value: str) -> bool:
    return not any(character in value for character in "'\"[](){} ,:")


def _unquote_string(value: str) -> str | None:
    try:
        literal = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return None
    return literal if isinstance(literal, str) else None


def _lookup_annotation_name(host: Any, method: Callable, name: str) -> Any:
    if not name.isidentifier():
        return _UNRESOLVED

    localns = _annotation_localns(host)
    if name in localns:
        return localns[name]

    return _annotation_globalns(method).get(name, _UNRESOLVED)


def _annotation_globalns(method: Callable) -> dict[str, Any]:
    function = getattr(method, "__func__", method)
    return getattr(function, "__globals__", {})


def _annotation_localns(host: Any) -> dict[str, Any]:
    namespace: dict[str, Any] = {}
    for klass in reversed(type(host).__mro__):
        namespace.update(vars(klass))
    return namespace


def _is_dispatch_message_class(klass: type) -> bool:
    if is_message_class(klass):
        return True
    if is_pickle_message_class(klass):
        return True
    if is_persistent_message_class(klass):
        return True
    return klass.__module__.startswith("iris")
