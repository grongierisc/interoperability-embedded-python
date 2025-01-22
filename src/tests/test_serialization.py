import datetime
import decimal
import uuid
from dataclasses import dataclass

import pytest
import iris

from iop._serialization import (
    SerializationError,
    serialize_message,
    deserialize_message,
    serialize_pickle_message,
    deserialize_pickle_message,
)

@dataclass
class Object:
    value: str

@dataclass
class FullMessge:
    text: str
    dikt: dict
    text_json: str
    obj: Object
    number: int
    date: datetime.date
    time: datetime.time
    dt: datetime.datetime
    dec: decimal.Decimal
    uid: uuid.UUID
    data: bytes
    items: list  # Changed from df to a simple list

def test_json_serialization():
    # Create test data
    test_items = [{'col1': 1, 'col2': 'a'}, {'col1': 2, 'col2': 'b'}]  # Simple list of dicts instead of DataFrame
    test_uuid = uuid.uuid4()
    test_bytes = b'hello world'
    
    msg = FullMessge(
        text="test",
        dikt={'key': 'value'},
        text_json="{\"key\": \"value\"}",
        obj=Object(value="test"),
        number=42,
        date=datetime.date(2023, 1, 1),
        time=datetime.time(12, 0),
        dt=datetime.datetime(2023, 1, 1, 12, 0),
        dec=decimal.Decimal("3.14"),
        uid=test_uuid,
        data=test_bytes,
        items=test_items
    )
    
    # Test serialization
    serial = serialize_message(msg)
    assert type(serial).__module__.startswith('iris') and serial._IsA("IOP.Message")
    assert serial.classname == f"{FullMessge.__module__}.{FullMessge.__name__}"
    
    # Test deserialization
    result = deserialize_message(serial)
    assert isinstance(result, FullMessge)
    assert result.text == msg.text
    assert result.dikt == msg.dikt
    assert result.text_json == msg.text_json
    assert result.obj == msg.obj
    assert result.number == msg.number
    assert result.date == msg.date
    assert result.time == msg.time
    assert result.dt == msg.dt
    assert result.dec == msg.dec
    assert result.uid == msg.uid
    assert result.data == msg.data
    assert result.items == msg.items

def test_pickle_serialization():
    msg = FullMessge(
        text="test",
        dikt={'key': 'value'},
        text_json="{\"key\": \"value\"}",
        obj=Object(value="test"),
        number=42,
        date=datetime.date(2023, 1, 1),
        time=datetime.time(12, 0),
        dt=datetime.datetime(2023, 1, 1, 12, 0),
        dec=decimal.Decimal("3.14"),
        uid=uuid.uuid4(),
        data=b'hello world',
        items=[{'col1': 1, 'col2': 'a'}, {'col1': 2, 'col2': 'b'}]
    )
    
    # Test serialization
    serial = serialize_pickle_message(msg)
    assert type(serial).__module__.startswith('iris') and serial._IsA("IOP.PickleMessage")
    assert serial.classname == f"{FullMessge.__module__}.{FullMessge.__name__}"
    
    # Test deserialization
    result = deserialize_pickle_message(serial)
    assert isinstance(result, FullMessge)
    assert result.text == msg.text
    assert result.dikt == msg.dikt
    assert result.text_json == msg.text_json
    assert result.obj == msg.obj
    assert result.number == msg.number
    assert result.date == msg.date
    assert result.time == msg.time
    assert result.dt == msg.dt
    assert result.dec == msg.dec
    assert result.uid == msg.uid
    assert result.data == msg.data
    assert result.items == msg.items

def test_invalid_message_deserialization():
    # Create an invalid message without classname
    msg = iris.cls('IOP.Message')._New()
    msg.classname = None
    msg.json = "{}"
    
    with pytest.raises(SerializationError, match="JSON message malformed, must include classname"):
        deserialize_message(msg)
    
    # Test invalid module
    msg.classname = "invalid.module.Class"
    with pytest.raises(SerializationError, match="Failed to load class invalid.module.Class: No module named 'invalid'"):
        deserialize_message(msg)
