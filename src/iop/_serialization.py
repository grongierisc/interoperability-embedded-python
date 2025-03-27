from __future__ import annotations
import codecs
import importlib
import inspect
import pickle
import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Type

from . import _iris
from pydantic import BaseModel, TypeAdapter, ValidationError

from iop._message import _PydanticPickleMessage
from iop._utils import _Utils

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
    def _convert_to_json_safe(obj: Any) -> Any:
        """Convert objects to JSON-safe format."""
        if isinstance(obj, BaseModel):
            return obj.model_dump_json()
        elif is_dataclass(obj):
            return TempPydanticModel.model_validate(dataclass_to_dict(obj)).model_dump_json()
        else:
            raise SerializationError(f"Object {obj} must be a Pydantic model or dataclass")

    @staticmethod
    def serialize(message: Any, use_pickle: bool = False) -> Any:
        """Serializes a message to IRIS format."""
        if isinstance(message, _PydanticPickleMessage) or use_pickle:
            return MessageSerializer._serialize_pickle(message)
        return MessageSerializer._serialize_json(message)

    @staticmethod
    def _serialize_json(message: Any) -> Any:
        json_string = MessageSerializer._convert_to_json_safe(message)
        
        msg = _iris.get_iris().cls('IOP.Message')._New()
        msg.classname = f"{message.__class__.__module__}.{message.__class__.__name__}"
        
        if hasattr(msg, 'buffer') and len(json_string) > msg.buffer:
            msg.json = _Utils.string_to_stream(json_string, msg.buffer)
        else:
            msg.json = json_string
        return msg

    @staticmethod
    def deserialize(serial: Any, use_pickle: bool = False) -> Any:
        if use_pickle:
            return MessageSerializer._deserialize_pickle(serial)
        return MessageSerializer._deserialize_json(serial)

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
    def _serialize_pickle(message: Any) -> Any:
        pickle_string = codecs.encode(pickle.dumps(message), "base64").decode()
        msg = _iris.get_iris().cls('IOP.PickleMessage')._New()
        msg.classname = f"{message.__class__.__module__}.{message.__class__.__name__}"
        msg.jstr = _Utils.string_to_stream(pickle_string)
        return msg

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

def dataclass_from_dict(klass: Type, dikt: Dict) -> Any:
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
    dikt = asdict(instance)
    # assign any extra fields
    for k, v in vars(instance).items():
        if k not in dikt:
            dikt[k] = v
    return dikt

# Maintain backwards compatibility
serialize_pickle_message = lambda msg: MessageSerializer.serialize(msg, use_pickle=True)
serialize_message = lambda msg: MessageSerializer.serialize(msg, use_pickle=False)
deserialize_pickle_message = lambda serial: MessageSerializer.deserialize(serial, use_pickle=True)
deserialize_message = lambda serial: MessageSerializer.deserialize(serial, use_pickle=False)