from inspect import signature
from typing import Any

from iop._serialization import serialize_message, serialize_pickle_message, deserialize_message, deserialize_pickle_message
from iop._message_validator import is_message_instance, is_pickle_message_instance, is_iris_object_instance

def dispatch_serializer(message: Any) -> Any:
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
            return serialize_message(message)
        elif is_pickle_message_instance(message):
            return serialize_pickle_message(message)
        elif is_iris_object_instance(message):
            return message

    if message == "" or message is None:
        return message

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

def dispach_message(host, request: Any) -> Any:
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

def create_dispatch(host) -> None:
    """Creates a list of tuples, where each tuple contains the name of a class and the name of a method
    that takes an instance of that class as its only argument.
    """
    if len(host.DISPATCH) == 0:
        method_list = [func for func in dir(host) if callable(getattr(host, func)) and not func.startswith("_")]
        for method in method_list:
            try:
                param = signature(getattr(host, method)).parameters
            except ValueError as e:
                param = ''
            if (len(param) == 1):
                annotation = str(param[list(param)[0]].annotation)
                i = annotation.find("'")
                j = annotation.rfind("'")
                if j == -1:
                    j = None
                classname = annotation[i+1:j]
                host.DISPATCH.append((classname, method))
    return
