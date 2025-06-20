from __future__ import annotations
import codecs
import importlib
import inspect
import pickle
import json
from dataclasses import is_dataclass
from typing import Any, Dict, Type

from pydantic import BaseModel, TypeAdapter, ValidationError

from . import _iris
from ._message import _PydanticPickleMessage, _Message
from ._utils import _Utils

class SerializationError(Exception):
    """Exception raised for serialization errors."""
    pass

class TempPydanticModel(BaseModel):
    model_config = {
        'arbitrary_types_allowed' : True,
        'extra' : 'allow'
    }

class MessageSerializer:
    """Handles message serialization and deserialization."""

    @staticmethod
    def serialize(message: Any, use_pickle: bool = False, is_generator:bool = False) -> Any:
        """Serializes a message to IRIS format."""
        message = remove_iris_id(message)
        if use_pickle:
            return MessageSerializer._serialize_pickle(message, is_generator)
        return MessageSerializer._serialize_json(message, is_generator)

    @staticmethod
    def _serialize_json(message: Any, is_generator: bool = False) -> Any:
        json_string = MessageSerializer._convert_to_json_safe(message)
        
        if is_generator:
            msg = _iris.get_iris().cls('IOP.Generator.Message.Start')._New()
        else:
            msg = _iris.get_iris().cls('IOP.Message')._New()
        msg.classname = f"{message.__class__.__module__}.{message.__class__.__name__}"
        
        if hasattr(msg, 'buffer') and len(json_string) > msg.buffer:
            msg.json = _Utils.string_to_stream(json_string, msg.buffer)
        else:
            msg.json = json_string
        return msg
    
    @staticmethod
    def _serialize_pickle(message: Any, is_generator: bool = False) -> Any:
        """Serializes a message to IRIS format using pickle."""
        message = remove_iris_id(message)
        pickle_string = codecs.encode(pickle.dumps(message), "base64").decode()
        if is_generator:
            msg = _iris.get_iris().cls('IOP.Generator.Message.StartPickle')._New()
        else:
            msg = _iris.get_iris().cls('IOP.PickleMessage')._New()
        msg.classname = f"{message.__class__.__module__}.{message.__class__.__name__}"
        msg.jstr = _Utils.string_to_stream(pickle_string)
        return msg

    @staticmethod
    def deserialize(serial: Any, use_pickle: bool = False) -> Any:
        if use_pickle:
            msg=MessageSerializer._deserialize_pickle(serial)
        else:
            msg=MessageSerializer._deserialize_json(serial)
    
        try:
            iris_id = serial._Id()
            msg._iris_id = iris_id if iris_id else None
        except Exception as e:
            pass

        return msg

    @staticmethod
    def _deserialize_json(serial: Any) -> Any:
        if not serial.classname:
            raise SerializationError("JSON message malformed, must include classname")
        
        try:
            module_name, class_name = MessageSerializer._parse_classname(serial.classname)
            module = importlib.import_module(module_name)
            msg_class = getattr(module, class_name)
        except Exception as e:
            raise SerializationError(f"Failed to load class {serial.classname}: {str(e)}")

        json_string = (_Utils.stream_to_string(serial.json) 
                      if serial.type == 'Stream' else serial.json)
        
        try:
            if issubclass(msg_class, BaseModel):
                return msg_class.model_validate_json(json_string)
            elif is_dataclass(msg_class):
                return dataclass_from_dict(msg_class, json.loads(json_string))
            else:
                raise SerializationError(f"Class {msg_class} must be a Pydantic model or dataclass")
        except Exception as e:
            raise SerializationError(f"Failed to deserialize JSON: {str(e)}")

    @staticmethod
    def _deserialize_pickle(serial: Any) -> Any:
        string = _Utils.stream_to_string(serial.jstr)
        return pickle.loads(codecs.decode(string.encode(), "base64"))

    @staticmethod
    def _parse_classname(classname: str) -> tuple[str, str]:
        j = classname.rindex(".")
        if j <= 0:
            raise SerializationError(f"Classname must include a module: {classname}")
        return classname[:j], classname[j+1:]
    
    @staticmethod
    def _convert_to_json_safe(obj: Any) -> Any:
        """Convert objects to JSON-safe format."""
        if isinstance(obj, BaseModel):
            return obj.model_dump_json()
        elif is_dataclass(obj) and isinstance(obj, _Message):
            return TempPydanticModel.model_validate(dataclass_to_dict(obj)).model_dump_json()
        else:
            raise SerializationError(f"Object {obj} must be a Pydantic model or dataclass Message")

    
def remove_iris_id(message: Any) -> Any:
    try:
        del message._iris_id
    except AttributeError:
        pass
    return message

def dataclass_from_dict(klass: Type | Any, dikt: Dict) -> Any:
    """Converts a dictionary to a dataclass instance.
    Handles non attended fields and nested dataclasses."""
    
    def process_field(value: Any, field_type: Type) -> Any:
        if value is None:
            return None
        if is_dataclass(field_type):
            return dataclass_from_dict(field_type, value)
        if field_type != inspect.Parameter.empty:
            try:
                return TypeAdapter(field_type).validate_python(value)
            except ValidationError:
                return value
        return value

    # Get field definitions from class signature
    fields = inspect.signature(klass).parameters
    field_dict = {}

    # Process each field
    for field_name, field_info in fields.items():
        if field_name not in dikt:
            if field_info.default != field_info.empty:
                field_dict[field_name] = field_info.default
            continue
        
        field_dict[field_name] = process_field(dikt[field_name], field_info.annotation)

    # Create instance
    instance = klass(**field_dict)
    
    # Add any extra fields not in the dataclass definition
    for key, value in dikt.items():
        if key not in field_dict:
            setattr(instance, key, value)
    
    return instance

def dataclass_to_dict(instance: Any) -> Dict:
    """Converts a class instance to a dictionary.
    Handles non attended fields."""
    result = {}
    for field in instance.__dict__:
        value = getattr(instance, field)
        if is_dataclass(value):
            result[field] = dataclass_to_dict(value)
        elif isinstance(value, list):
            result[field] = [dataclass_to_dict(i) if is_dataclass(i) else i for i in value]
        elif isinstance(value, dict):
            result[field] = {k: dataclass_to_dict(v) if is_dataclass(v) else v for k, v in value.items()}
        elif hasattr(value, '__dict__'):
            result[field] = dataclass_to_dict(value)
        else:
            result[field] = value
    return result

# Maintain backwards compatibility
serialize_pickle_message = lambda msg: MessageSerializer.serialize(msg, use_pickle=True, is_generator=False)
serialize_pickle_message_generator = lambda msg: MessageSerializer.serialize(msg, use_pickle=True, is_generator=True)
serialize_message = lambda msg: MessageSerializer.serialize(msg, use_pickle=False, is_generator=False)
serialize_message_generator = lambda msg: MessageSerializer.serialize(msg, use_pickle=False, is_generator=True)
deserialize_pickle_message = lambda serial: MessageSerializer.deserialize(serial, use_pickle=True)
deserialize_message = lambda serial: MessageSerializer.deserialize(serial, use_pickle=False)