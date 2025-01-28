from __future__ import annotations
import codecs
import importlib
import inspect
import pickle
import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Type

import iris
from pydantic import BaseModel, TypeAdapter

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
    def serialize(message: Any, use_pickle: bool = False) -> iris.cls:
        """Serializes a message to IRIS format."""
        if isinstance(message, _PydanticPickleMessage) or use_pickle:
            return MessageSerializer._serialize_pickle(message)
        return MessageSerializer._serialize_json(message)

    @staticmethod
    def _serialize_json(message: Any) -> iris.cls:
        json_string = MessageSerializer._convert_to_json_safe(message)
        
        msg = iris.cls('IOP.Message')._New()
        msg.classname = f"{message.__class__.__module__}.{message.__class__.__name__}"
        
        if hasattr(msg, 'buffer') and len(json_string) > msg.buffer:
            msg.json = _Utils.string_to_stream(json_string, msg.buffer)
        else:
            msg.json = json_string
        return msg

    @staticmethod
    def deserialize(serial: iris.cls, use_pickle: bool = False) -> Any:
        if use_pickle:
            return MessageSerializer._deserialize_pickle(serial)
        return MessageSerializer._deserialize_json(serial)

    @staticmethod
    def _deserialize_json(serial: iris.cls) -> Any:
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
    def _serialize_pickle(message: Any) -> iris.cls:
        pickle_string = codecs.encode(pickle.dumps(message), "base64").decode()
        msg = iris.cls('IOP.PickleMessage')._New()
        msg.classname = f"{message.__class__.__module__}.{message.__class__.__name__}"
        msg.jstr = _Utils.string_to_stream(pickle_string)
        return msg

    @staticmethod
    def _deserialize_pickle(serial: iris.cls) -> Any:
        string = _Utils.stream_to_string(serial.jstr)
        return pickle.loads(codecs.decode(string.encode(), "base64"))

    @staticmethod
    def _parse_classname(classname: str) -> tuple[str, str]:
        j = classname.rindex(".")
        if j <= 0:
            raise SerializationError(f"Classname must include a module: {classname}")
        return classname[:j], classname[j+1:]

def dataclass_from_dict(klass: Type, dikt: Dict) -> Any:
    field_types = {
        key: val.annotation
        for key, val in inspect.signature(klass).parameters.items()
    }
    processed_dict = {}
    for key, val in inspect.signature(klass).parameters.items():
        if key not in dikt and val.default != val.empty:
            processed_dict[key] = val.default
            continue
        
        value = dikt.get(key)
        if value is None:
            processed_dict[key] = None
            continue

        try:
            field_type = field_types[key]
            if field_type != inspect.Parameter.empty:
                adapter = TypeAdapter(field_type)
                processed_dict[key] = adapter.validate_python(value)
            else:
                processed_dict[key] = value
        except Exception:
            processed_dict[key] = value

    instance = klass(
        **processed_dict
    )
    # handle any extra fields
    for k, v in dikt.items():
        if k not in processed_dict:
            setattr(instance, k, v)
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