from inspect import Parameter, signature
from typing import Any

from .persistent import (
    deserialize_persistent_message,
    get_iris_object_classname,
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
    is_message_instance,
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

    module = request.__class__.__module__
    classname = request.__class__.__name__

    for msg, method in host.DISPATCH:
        if msg == module + "." + classname:
            call = method

    return getattr(host, call)(request)


def create_dispatch(host: Any) -> None:
    """Creates a dispatch table mapping class names to their handler methods.
    The dispatch table consists of tuples of (fully_qualified_class_name, method_name).
    Only methods that take a single typed parameter are considered as handlers.
    """
    dispatch = _declared_dispatch(host)

    for method_name in get_callable_methods(host):
        handler_info = get_handler_info(host, method_name)
        if handler_info and handler_info not in dispatch:
            dispatch.append(handler_info)

    host.DISPATCH = dispatch


def _declared_dispatch(host: Any) -> list[tuple[str, str]]:
    if "DISPATCH" in getattr(host, "__dict__", {}):
        return list(host.__dict__["DISPATCH"])

    class_dispatch = host.__class__.__dict__.get("DISPATCH")
    if class_dispatch is not None:
        return list(class_dispatch)

    return []


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

        param: Parameter = next(iter(params.values()))
        annotation = param.annotation

        if isinstance(annotation, str):
            # return it as is, assuming it's a fully qualified class name
            return annotation, method_name

        if is_iris_object_instance(annotation):
            return (
                f"{type(annotation).__module__}.{type(annotation).__name__}",
                method_name,
            )

        if annotation == Parameter.empty or not isinstance(annotation, type):
            return None

        return f"{annotation.__module__}.{annotation.__name__}", method_name

    except ValueError:
        return None
