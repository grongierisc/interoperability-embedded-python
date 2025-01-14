import codecs
import importlib
from inspect import signature
import json
import pickle
from typing import Any, Dict, List, Type

import iris
from dacite import Config, from_dict

from iop._utils import _Utils
from iop._serialization import IrisJSONEncoder, IrisJSONDecoder
from iop._message_validator import is_message_instance, is_pickle_message_instance, is_iris_object_instance

def serialize_pickle_message(message: Any) -> iris.cls:
    """Converts a python dataclass message into an iris iop.message.

    Args:
        message: The message to serialize, an instance of a class that is a subclass of Message.

    Returns:
        The message in json format.
    """
    pickle_string = codecs.encode(pickle.dumps(message), "base64").decode()
    module = message.__class__.__module__
    classname = message.__class__.__name__

    msg = iris.cls('IOP.PickleMessage')._New()
    msg.classname = module + "." + classname

    stream = _Utils.string_to_stream(pickle_string)
    msg.jstr = stream

    return msg

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

def serialize_message(message: Any) -> iris.cls:
    """Converts a python dataclass message into an iris iop.message.

    Args:
        message: The message to serialize, an instance of a class that is a subclass of Message.

    Returns:
        The message in json format.
    """
    json_string = json.dumps(message, cls=IrisJSONEncoder, ensure_ascii=False)
    module = message.__class__.__module__
    classname = message.__class__.__name__

    msg = iris.cls('IOP.Message')._New()
    msg.classname = module + "." + classname

    if hasattr(msg, 'buffer') and len(json_string) > msg.buffer:
        msg.json = _Utils.string_to_stream(json_string, msg.buffer)
    else:
        msg.json = json_string

    return msg

def deserialize_pickle_message(serial: iris.cls) -> Any:
    """Converts an iris iop.message into a python dataclass message.
    
    Args:
        serial: The serialized message
        
    Returns:
        The deserialized message
    """
    string = _Utils.stream_to_string(serial.jstr)
    msg = pickle.loads(codecs.decode(string.encode(), "base64"))
    return msg

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

def deserialize_message(serial: iris.cls) -> Any:
    """Converts an iris iop.message into a python dataclass message.
    
    Args:
        serial: The serialized message
        
    Returns:
        The deserialized message
    """
    if (serial.classname is None):
        raise ValueError("JSON message malformed, must include classname")
    classname = serial.classname

    j = classname.rindex(".")
    if (j <= 0):
        raise ValueError("Classname must include a module: " + classname)
    try:
        module = importlib.import_module(classname[:j])
        msg = getattr(module, classname[j+1:])
    except Exception:
        raise ImportError("Class not found: " + classname)

    string = ""
    if (serial.type == 'Stream'):
        string = _Utils.stream_to_string(serial.json)
    else:
        string = serial.json

    jdict = json.loads(string, cls=IrisJSONDecoder)
    return dataclass_from_dict(msg, jdict)

def dataclass_from_dict(klass: Type, dikt: Dict) -> Any:
    """Converts a dictionary to a dataclass instance.
    
    Args:
        klass: The dataclass to convert to
        dikt: The dictionary to convert to a dataclass
        
    Returns:
        A dataclass object with the fields of the dataclass and the fields of the dictionary.
    """
    ret = from_dict(klass, dikt, Config(check_types=False))
    
    try:
        fieldtypes = klass.__annotations__
    except Exception as e:
        fieldtypes = []
    
    for key, val in dikt.items():
        if key not in fieldtypes:
            setattr(ret, key, val)
    return ret

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
