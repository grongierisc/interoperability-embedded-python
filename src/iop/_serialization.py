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

from iop._utils import _Utils

class IrisJSONEncoder(json.JSONEncoder):
    """JSONEncoder that handles dates, decimals, UUIDs, etc."""
    
    def default(self, o: Any) -> Any:
        if o.__class__.__name__ == 'DataFrame':
            return 'dataframe:' + o.to_json(orient="table")
        elif isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith("+00:00"):
                r = r[:-6] + "Z"
            return 'datetime:' + r
        elif isinstance(o, datetime.date):
            return 'date:' + o.isoformat()
        elif isinstance(o, datetime.time):
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return 'time:' + r
        elif isinstance(o, decimal.Decimal):
            return 'decimal:' + str(o)
        elif isinstance(o, uuid.UUID):
            return 'uuid:' + str(o)
        elif isinstance(o, bytes):
            return 'bytes:' + base64.b64encode(o).decode("UTF-8")
        elif hasattr(o, '__dict__'):
            return o.__dict__
        return super().default(o)

class IrisJSONDecoder(json.JSONDecoder):
    """JSONDecoder that handles special type annotations."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        json.JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj: Dict) -> Dict:
        ret = {}
        for key, value in obj.items():
            i = 0
            if isinstance(value, str):
                i = value.find(":")
            if i > 0:
                typ = value[:i]
                val = value[i+1:]
                ret[key] = self._convert_typed_value(typ, val)
            else:
                ret[key] = value
        return ret
                
    def _convert_typed_value(self, typ: str, val: str) -> Any:
        if typ == 'datetime':
            return datetime.datetime.fromisoformat(val)
        elif typ == 'date':
            return datetime.date.fromisoformat(val)
        elif typ == 'time':
            return datetime.time.fromisoformat(val)
        elif typ == 'dataframe':
            module = importlib.import_module('pandas')
            return module.read_json(val, orient="table")
        elif typ == 'decimal':
            return decimal.Decimal(val)
        elif typ == 'uuid':
            return uuid.UUID(val)
        elif typ == 'bytes':
            return base64.b64decode(val.encode("UTF-8"))
        return val


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
    msg = dataclass_from_dict(msg, jdict)
    return msg

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