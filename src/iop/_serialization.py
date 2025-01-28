from __future__ import annotations
import base64
import codecs
import datetime
import decimal
import importlib
import json
import pickle
import uuid
from typing import Any, Dict, Type

from dacite import Config, from_dict
import iris

from iop._message import _PydanticPickleMessage
from iop._utils import _Utils
from pydantic import BaseModel

# Constants
DATETIME_FORMAT_LENGTH = 23
TIME_FORMAT_LENGTH = 12
TYPE_SEPARATOR = ':'
SUPPORTED_TYPES = {
    'datetime', 'date', 'time', 'dataframe', 
    'decimal', 'uuid', 'bytes'
}

class SerializationError(Exception):
    """Base exception for serialization errors."""
    pass

class TypeConverter:
    """Handles type conversion for special data types."""
    
    @staticmethod
    def convert_to_string(typ: str, obj: Any) -> str:
        if typ == 'dataframe':
            return obj.to_json(orient="table")
        elif typ == 'datetime':
            return TypeConverter._format_datetime(obj)
        elif typ == 'date':
            return obj.isoformat()
        elif typ == 'time':
            return TypeConverter._format_time(obj)
        elif typ == 'bytes':
            return base64.b64encode(obj).decode("UTF-8")
        return str(obj)

    @staticmethod
    def convert_from_string(typ: str, val: str) -> Any:
        try:
            if typ == 'datetime':
                return datetime.datetime.fromisoformat(val)
            elif typ == 'date':
                return datetime.date.fromisoformat(val)
            elif typ == 'time':
                return datetime.time.fromisoformat(val)
            elif typ == 'dataframe':
                try:
                    import pandas as pd
                except ImportError:
                    raise SerializationError("Failed to load pandas module")
                return pd.read_json(val, orient="table")
            elif typ == 'decimal':
                return decimal.Decimal(val)
            elif typ == 'uuid':
                return uuid.UUID(val)
            elif typ == 'bytes':
                return base64.b64decode(val.encode("UTF-8"))
            return val
        except Exception as e:
            raise SerializationError(f"Failed to convert type {typ}: {str(e)}")

    @staticmethod
    def _format_datetime(dt: datetime.datetime) -> str:
        r = dt.isoformat()
        if dt.microsecond:
            r = r[:DATETIME_FORMAT_LENGTH] + r[26:]
        if r.endswith("+00:00"):
            r = r[:-6] + "Z"
        return r

    @staticmethod
    def _format_time(t: datetime.time) -> str:
        r = t.isoformat()
        if t.microsecond:
            r = r[:TIME_FORMAT_LENGTH]
        return r

class IrisJSONEncoder(json.JSONEncoder):
    """JSONEncoder that handles dates, decimals, UUIDs, etc."""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if obj.__class__.__name__ == 'DataFrame':
            return f'dataframe:{TypeConverter.convert_to_string("dataframe", obj)}'
        elif isinstance(obj, datetime.datetime):
            return f'datetime:{TypeConverter.convert_to_string("datetime", obj)}'
        elif isinstance(obj, datetime.date):
            return f'date:{TypeConverter.convert_to_string("date", obj)}'
        elif isinstance(obj, datetime.time):
            return f'time:{TypeConverter.convert_to_string("time", obj)}'
        elif isinstance(obj, decimal.Decimal):
            return f'decimal:{obj}'
        elif isinstance(obj, uuid.UUID):
            return f'uuid:{obj}'
        elif isinstance(obj, bytes):
            return f'bytes:{TypeConverter.convert_to_string("bytes", obj)}'
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

class IrisJSONDecoder(json.JSONDecoder):
    """JSONDecoder that handles special type annotations."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj: Dict) -> Dict:
        return {
            key: self._process_value(value)
            for key, value in obj.items()
        }
                
    def _process_value(self, value: Any) -> Any:
        if isinstance(value, str) and TYPE_SEPARATOR in value:
            typ, val = value.split(TYPE_SEPARATOR, 1)
            if typ in SUPPORTED_TYPES:
                return TypeConverter.convert_from_string(typ, val)
        return value

class MessageSerializer:
    """Handles message serialization and deserialization."""

    @staticmethod
    def serialize(message: Any, use_pickle: bool = False) -> iris.cls:
        """Serializes a message to IRIS format."""
        # Check for PydanticPickleMessage first
        if isinstance(message, _PydanticPickleMessage):
            return MessageSerializer._serialize_pickle(message)
        if isinstance(message, BaseModel):
            return (MessageSerializer._serialize_pickle(message) 
                   if use_pickle else MessageSerializer._serialize_json(message))
        if use_pickle:
            return MessageSerializer._serialize_pickle(message)
        return MessageSerializer._serialize_json(message)

    @staticmethod
    def deserialize(serial: iris.cls, use_pickle: bool = False) -> Any:
        """Deserializes a message from IRIS format."""
        if use_pickle:
            return MessageSerializer._deserialize_pickle(serial)
        return MessageSerializer._deserialize_json(serial)

    @staticmethod
    def _serialize_pickle(message: Any) -> iris.cls:
        pickle_string = codecs.encode(pickle.dumps(message), "base64").decode()
        msg = iris.cls('IOP.PickleMessage')._New()
        msg.classname = f"{message.__class__.__module__}.{message.__class__.__name__}"
        msg.jstr = _Utils.string_to_stream(pickle_string)
        return msg

    @staticmethod
    def _serialize_json(message: Any) -> iris.cls:
        if isinstance(message, BaseModel):
            json_string = json.dumps(message.model_dump(), cls=IrisJSONEncoder, ensure_ascii=False)
        else:
            json_string = json.dumps(message, cls=IrisJSONEncoder, ensure_ascii=False)
            
        msg = iris.cls('IOP.Message')._New()
        msg.classname = f"{message.__class__.__module__}.{message.__class__.__name__}"
        
        if hasattr(msg, 'buffer') and len(json_string) > msg.buffer:
            msg.json = _Utils.string_to_stream(json_string, msg.buffer)
        else:
            msg.json = json_string
        return msg

    @staticmethod
    def _deserialize_pickle(serial: iris.cls) -> Any:
        string = _Utils.stream_to_string(serial.jstr)
        return pickle.loads(codecs.decode(string.encode(), "base64"))

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
            json_dict = json.loads(json_string, cls=IrisJSONDecoder)
            if issubclass(msg_class, BaseModel):
                return msg_class.model_validate(json_dict)
            else:
                return dataclass_from_dict(msg_class, json_dict)
        except Exception as e:
            raise SerializationError(f"Failed to deserialize JSON: {str(e)}")

    @staticmethod
    def _parse_classname(classname: str) -> tuple[str, str]:
        j = classname.rindex(".")
        if j <= 0:
            raise SerializationError(f"Classname must include a module: {classname}")
        return classname[:j], classname[j+1:]

def dataclass_from_dict(klass: Type, dikt: Dict) -> Any:
    """Converts a dictionary to a dataclass instance."""
    ret = from_dict(klass, dikt, Config(check_types=False))
    
    try:
        fieldtypes = klass.__annotations__
    except Exception:
        fieldtypes = {}
    
    for key, val in dikt.items():
        if key not in fieldtypes:
            setattr(ret, key, val)
    return ret

# Maintain backwards compatibility
serialize_pickle_message = lambda msg: MessageSerializer.serialize(msg, use_pickle=True)
serialize_message = lambda msg: MessageSerializer.serialize(msg, use_pickle=False)
deserialize_pickle_message = lambda serial: MessageSerializer.deserialize(serial, use_pickle=True)
deserialize_message = lambda serial: MessageSerializer.deserialize(serial, use_pickle=False)