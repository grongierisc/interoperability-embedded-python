from inspect import signature, Parameter
from typing import Any, List, Tuple, Callable

from ._serialization import serialize_message, serialize_pickle_message, deserialize_message, deserialize_pickle_message, serialize_message_generator, serialize_pickle_message_generator
from ._message_validator import is_message_instance, is_pickle_message_instance, is_iris_object_instance

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
        if is_message_instance(message):
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

    if hasattr(message, '__iter__'):
        raise TypeError("You may have tried to invoke a generator function without using the 'send_generator_request' method. Please use that method to handle generator functions.")

    raise TypeError("The message must be an instance of a class that is a subclass of Message or IRISObject %Persistent class.")

def dispatch_deserializer(serial: Any) -> Any:
    """Deserializes the message based on its type.
    
    Args:
        serial: The serialized message
        
    Returns:
        The deserialized message
    """
    if (
        serial is not None
        and type(serial).__module__.startswith('iris')
        and (
            serial._IsA("IOP.Message")
            or serial._IsA("Grongier.PEX.Message")
        )
    ):
        return deserialize_message(serial)
    elif (
        serial is not None
        and type(serial).__module__.startswith('iris')
        and (
            serial._IsA("IOP.PickleMessage")
            or serial._IsA("Grongier.PEX.PickleMessage")
        )
    ):
        return deserialize_pickle_message(serial)
    else:
        return serial

def dispach_message(host: Any, request: Any) -> Any:
    """Dispatches the message to the appropriate method.
    
    Args:
        request: The request object
        
    Returns:
        The response object
    """
    call = 'on_message'

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
    if len(host.DISPATCH) > 0:
        return

    for method_name in get_callable_methods(host):
        handler_info = get_handler_info(host, method_name)
        if handler_info:
            host.DISPATCH.append(handler_info)

def get_callable_methods(host: Any) -> List[str]:
    """Returns a list of callable method names that don't start with underscore."""
    return [
        func for func in dir(host) 
        if callable(getattr(host, func)) and not func.startswith("_")
    ]

def get_handler_info(host: Any, method_name: str) -> Tuple[str, str] | None:
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
            return f"{type(annotation).__module__}.{type(annotation).__name__}", method_name
        
        if annotation == Parameter.empty or not isinstance(annotation, type):

            return None

        return f"{annotation.__module__}.{annotation.__name__}", method_name
            
    except ValueError:
        return None